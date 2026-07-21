import requests, re, os, configparser, yaml
import google_play_scraper as gp
import datetime as dt
from Reports import report

# yaml setup
with open("AppIds_list.yaml", "r", encoding="utf-8") as file:
    data = yaml.safe_load(file)
# ==========


def config_write(path, section, AppId, version, desc, ddt, folder_name="ini_files"):
    config = configparser.ConfigParser()
    os.makedirs(f"{folder_name}/", exist_ok=True)
    config.read(f"{folder_name}/{path}", encoding='utf-8')
    config[section] = {
        "AppId": AppId,
        "version": version,
        "desc": desc,
        "date_modified": ddt
    }
    with open(f"{folder_name}/{path}", 'w', encoding='utf-8') as configfile:
        config.write(configfile)


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
        url = f"https://play.google.com/store/apps/details?AppId={e}&hl=ru&gl=RU"
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
        config_write("GooglePlay.ini", monitored_AppIds[e][0], e, monitored_AppIds[e][2], patchnotes, monitored_AppIds[e][1])
        
        
    except Exception as x:
        print(f"Error fetching patchnotes for {e}: {x}")



# AppStore
print("\nFetching AppStore data")

CompetitorsList_toAppIdsAPS = data.get("AppStore", {})

for competitors in CompetitorsList_toAppIdsAPS:
    try:
        AppId = CompetitorsList_toAppIdsAPS[competitors]
        if AppId != "nonexistent":
            url = f"https://itunes.apple.com/lookup?AppId={AppId}&country=ru"
            dataStore = requests.get(url).json()
            print(f"\n{competitors}")
            print(dataStore["results"][0]["releaseNotes"])
            print(dataStore["results"][0]["version"])
            print(dataStore["results"][0]["currentVersionReleaseDate"])
            config_write("AppStore.ini", competitors, AppId, dataStore["results"][0]["version"], dataStore["results"][0]["releaseNotes"], dataStore["results"][0]["currentVersionReleaseDate"])
        else:
            print("This app doesn't exist in that packet store")
    except Exception as x:
        print(f"Error for{competitors}: {x}")



# RuStore
print("\nFetching RuStore data")

CompetitorsList_toAppIdsRuStore = data.get("RuStore", {})

for competitors in CompetitorsList_toAppIdsRuStore:
    try:
        AppId = CompetitorsList_toAppIdsRuStore[competitors]
        url = f"https://backapi.rustore.ru/applicationData/overallInfo/{AppId}"
        response = requests.get(url)
        
        if response.status_code == 200:
            body = response.json().get("body", {})
            
            version = body.get("versionName", "unknown")
            patchnotes = body.get("whatsNew", "Разработчик не оставил описание изменений")
            date_modified = body.get("appVerUpdatedAt", "unknown")
        
        print(f"\n{competitors}")
        print(version)
        print(patchnotes)
        print(date_modified)
        config_write("RuStore.ini", competitors, AppId, version, patchnotes, date_modified)
    except Exception as x:
        print(f"Error for{competitors}: {x}")
        


report("competitor_report.txt")