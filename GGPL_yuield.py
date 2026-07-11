import requests, re
import google_play_scraper as gp
import datetime as dt
from ini_parser import config_write


CompetitorsList_toIDsGP = {
    "Кинопоиск": "ru.kinopoisk.tv",
    "Иви": "ru.ivi.client",
    "Okko": "ru.more.play",
    "KION": "ru.mts.mtstv",
    "PREMIER": "gpm.tnt_premier",
    "START": "ru.start.androidmobile",
    "Амедиатека": "ru.amediateka",
    "Триколор Кино и ТВ": "com.gsgroup.tricoloronline",
    "Смотрёшка": "tv.lfstrm.smotreshka",
    "НТВ-ПЛЮС ТВ": "tv.ntvplus.app1",
    "Viju": "ru.viasat.apps.viju",
    "Rutube": "rtb.mobile.android"
    }
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


print("\nFetching AppStore data")


import requests

CompetitorsList_toIDsAPS = {
    "Кинопоиск": "477718890",
    "Иви": "455705533",
    "KION": "1451612172",
    "START": "1273218458",
    "Амедиатека": "695094274",
    "Триколор Кино и ТВ": "1412797916",
    "Смотрёшка": "911254937",
    "НТВ-ПЛЮС ТВ": "6448913831",
    "Viju": "1573234236",
}


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


print("\nFetching RuStore data")


import requests
from ini_parser import config_write

CompetitorsList_toIDsRuStore = {
    "Кинопоиск": "ru.kinopoisk",
    "Иви": "ru.ivi.client",
    "Okko": "ru.more.play",
    "KION": "ru.mts.mtstv",
    "PREMIER": "gpm.tnt_premier",
    "START": "ru.start.androidmobile",
    "Амедиатека": "com.amdteka",
    "Триколор Кино и ТВ": "com.gsgroup.tricoloronline.mobile",
    "Смотрёшка": "tv.lfstrm.smotreshka",
    "НТВ-ПЛЮС ТВ": "tv.ntvplus.app",
    "Viju": "ru.viasat.apps.viju",
    "Rutube": "ru.rutube.app"
}

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
        


