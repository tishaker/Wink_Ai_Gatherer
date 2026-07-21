import requests
import re
import os
import yaml
import google_play_scraper as gp
import datetime as dt

# yaml setup
with open("AppIds_list.yaml", "r", encoding="utf-8") as file:
    data = yaml.safe_load(file)

def yaml_write(
    path: str, # Path to the file in system
    section: str, # e.g. Google Play, AppStore..
    AppId: str, # AppStore uses int format, but Google Play and RuStore use str app IDs so we need str
    version: str, # e.g. v1.4.53
    desc: str, # e.g. Поработали «под капотом»: улучшили стабильность приложения, ...
    ddt: str, # e.g. 2026-07-20 09:20:50
    folder_name: str = "yaml_files", # e.g. "Work IDs" || Output dir
) -> None:

    os.makedirs(f"{folder_name}", exist_ok=True)
    full_path = os.path.join(folder_name, path)
    
    data = {}
    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}

    data[section] = {
        "AppId": AppId,
        "version": version,
        "desc": desc,
        "date_modified": ddt
    }
    with open(full_path, 'w', encoding='utf-8') as file:
        yaml.safe_dump(data, file, allow_unicode=True, sort_keys=False)
# ==========

# Google play
CompetitorsList_toAppIdsGP = data.get("GooglePlay", {})
monitored_AppIds = {}
for competitors in CompetitorsList_toAppIdsGP:
    try:
        app_AppId = CompetitorsList_toAppIdsGP[competitors]
        result = gp.app(app_AppId, lang="ru", country="RU")    
        print(f'{competitors}: "updated": {dt.datetime.fromtimestamp(result["updated"])}, "version": {result["version"]}. Adding to service monitoring list')
        monitored_AppIds[app_AppId] = (competitors, dt.datetime.fromtimestamp(result["updated"]), result["version"])
    except Exception as e:
        print(f"Error fetching data for {competitors}: {e}")

print("\nConnection established with services, fetching patchnotes\n")
for e in monitored_AppIds:
    try:
        url = f"https://play.google.com/store/apps/details?id={e}&hl=ru&gl=RU"
        dataStore = requests.get(url).text
        
        pattern = r'<section[^>]*>.*?Новое в приложении.*?<div[^>]*>([^<]+)</div>.*?</section>'
        match = re.search(pattern, dataStore, re.DOTALL)
        
        if match:
            text_candAppIdate = match.group(1).strip()
            if "+" in text_candAppIdate or len(text_candAppIdate) < 5:
                patchnotes = "Разрабы не дали комментария к обновлению"
            else:
                patchnotes = text_candAppIdate
        else:
            patchnotes = "No data"
            
        print(f"Патчноут для {monitored_AppIds[e][0]}: {patchnotes}\n")
        yaml_write("GooglePlay.yaml", monitored_AppIds[e][0], e, monitored_AppIds[e][2], patchnotes, monitored_AppIds[e][1])
        
        
    except Exception as x:
        print(f"Error fetching patchnotes for {e}: {x}")

# AppStore
def fetch_appstore_data() -> None:
    CompetitorsList_toAppIdsAPS = data.get("AppStore", {})

    for competitors in CompetitorsList_toAppIdsAPS:
        try:
            AppId = CompetitorsList_toAppIdsAPS[competitors]
            if AppId != "nonexistent":
                url = f"https://itunes.apple.com/lookup?id={AppId}&country=ru"
                dataStore = requests.get(url).json()
                print(f"\n{competitors}")
                print(dataStore["results"][0]["releaseNotes"])
                print(dataStore["results"][0]["version"])
                print(dataStore["results"][0]["currentVersionReleaseDate"])
                yaml_write("AppStore.yaml", competitors, AppId, dataStore["results"][0]["version"], dataStore["results"][0]["releaseNotes"], dataStore["results"][0]["currentVersionReleaseDate"])
            else:
                print(f"{competitors} doesn't exist in that app store\n")
        except Exception as x:
            print(f"Error for {competitors}: {x}")

# RuStore
def fetch_rustore_data() -> None:
    CompetitorsList_toAppIdsRuStore = data.get("RuStore", {})
    
    for competitors in CompetitorsList_toAppIdsRuStore:
        try:
            AppId = CompetitorsList_toAppIdsRuStore[competitors]
            url = f"https://backapi.rustore.ru/applicationData/overallInfo/{AppId}"
            response = requests.get(url)
            stc = response.status_code
            
            print(f"Status code {stc}")
            body = response.json().get("body", {})
            
            version = body.get("versionName", "unknown")
            patchnotes = body.get("whatsNew", "Разработчик не оставил описание изменений")
            date_modified = body.get("appVerUpdatedAt", "unknown")
            print(f"\n{competitors}")
            print(version)
            print(patchnotes)
            print(date_modified)
            yaml_write("RuStore.yaml", competitors, AppId, version, patchnotes, date_modified)
        except Exception as x:
            print(f"Error for {competitors}: {x}")