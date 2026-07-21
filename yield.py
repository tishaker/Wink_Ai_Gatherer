import requests, re, os, configparser, yaml
import google_play_scraper as gp
import datetime as dt
from Reports import report

# yaml setup
with open("IDs_list.yaml", "r", encoding="utf-8") as file:
    data = yaml.safe_load(file)
# ==========


def config_write(path, section, id, version, desc, ddt, folder_name="ini_files"):
    config = configparser.ConfigParser()
    os.makedirs(f"{folder_name}/", exist_ok=True)
    config.read(f"{folder_name}/{path}", encoding='utf-8')
    config[section] = {
        "id": id,
        "version": version,
        "desc": desc,
        "date_modified": ddt
    }
    with open(f"{folder_name}/{path}", 'w', encoding='utf-8') as configfile:
        config.write(configfile)


CompetitorsList_toIDsGP = data.get("GooglePlay", {})
monitored_ids = {}

for competitors in CompetitorsList_toIDsGP:
    try:
        app_id = CompetitorsList_toIDsGP[competitors]
        result = gp.app(app_id, lang="ru", country="RU")    
        print(f'{competitors}: "updated": {dt.datetime.fromtimestamp(result["updated"])}, "version": {result["version"]}. Adding to service monitoring list')
        monitored_ids[app_id] = (competitors, dt.datetime.fromtimestamp(result["updated"]), result["version"])
    except Exception as e:
        print(f"Error fetching data for {competitors}: {e}")

print("\nConnection established with services, fetching patchnotes\n")


for e in monitored_ids:
    try:
        url = f"https://play.google.com/store/apps/details?id={e}&hl=ru&gl=RU"
        data = requests.get(url).text
        
        pattern = r'<section[^>]*>.*?Новое в приложении.*?<div[^>]*>([^<]+)</div>.*?</section>'
        match = re.search(pattern, data, re.DOTALL)
        
        if match:
            text_candidate = match.group(1).strip()
            if "+" in text_candidate or len(text_candidate) < 5:
                patchnotes = "Разрабы не дали комментария к обновлению"
            else:
                patchnotes = text_candidate
        else:
            patchnotes = "No data"
            
        print(f"Патчноут для {monitored_ids[e][0]}: {patchnotes}\n")
        config_write("GooglePlay.ini", monitored_ids[e][0], e, monitored_ids[e][2], patchnotes, monitored_ids[e][1])
        
        
    except Exception as x:
        print(f"Error fetching patchnotes for {e}: {x}")



# AppStore
print("\nFetching AppStore data")

CompetitorsList_toIDsAPS = data.get("AppStore", {})

for competitors in CompetitorsList_toIDsAPS:
    try:
        id = CompetitorsList_toIDsAPS[competitors]
        url = f"https://itunes.apple.com/lookup?id={id}&country=ru"
        data = requests.get(url).json()
        print(f"\n{competitors}")
        print(data["results"][0]["releaseNotes"])
        print(data["results"][0]["version"])
        print(data["results"][0]["currentVersionReleaseDate"])
        config_write("AppStore.ini", competitors, id, data["results"][0]["version"], data["results"][0]["releaseNotes"], data["results"][0]["currentVersionReleaseDate"])
    except Exception as x:
        print(f"Error for{competitors}: {x}")



# RuStore
print("\nFetching RuStore data")

CompetitorsList_toIDsRuStore = data.get("RuStore", {})

for competitors in CompetitorsList_toIDsRuStore:
    try:
        id = CompetitorsList_toIDsRuStore[competitors]
        url = f"https://backapi.rustore.ru/applicationData/overallInfo/{id}"
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
        config_write("RuStore.ini", competitors, id, version, patchnotes, date_modified)
    except Exception as x:
        print(f"Error for{competitors}: {x}")
        


report("competitor_report.txt")