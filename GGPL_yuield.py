import requests, re
import google_play_scraper as gp
import datetime as dt
from ini_parser import config_write


CompetitorsList_toIDs = {
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

for competitors in CompetitorsList_toIDs:
    try:
        app_id = CompetitorsList_toIDs[competitors]
        result = gp.app(app_id, lang="ru", country="RU")    
        print(f'{competitors}: "updated": {dt.datetime.fromtimestamp(result["updated"])}, "version": {result["version"]}. Adding to service monitoring list')
        monitored_ids[app_id] = (competitors, dt.datetime.fromtimestamp(result["updated"]))
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
        config_write("GooglePlay.ini", monitored_ids[e][0], e, patchnotes, monitored_ids[e][1])
        
        
    except Exception as x:
        print(f"Error fetching patchnotes for {e}: {x}")

