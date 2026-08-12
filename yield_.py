import requests
import re
import os
import yaml
import time
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

def safe_requesting(url: str, keys: str, attr: list, is_gp: bool, default_resp: str = 'unknown', gp_id: str = "") -> tuple:
    res = requests.get(url)
    while True:
            if res.status_code == 200:
                if is_gp:
                    result_gp = gp.app(gp_id, lang='ru', country='ru')
                    html = res.text
                    patch_match = re.search(r"(?:Что нового|Новое в приложении).*?<div[^>]*>(.*?)</div>", html, re.DOTALL | re.IGNORECASE)
                    
                    version_gp = result_gp["version"] if result_gp["version"] != "Varies with device" else "Версия данного приложения варьируется в зависимости от устройства"
                    
                    if patch_match:
                        patchnotes = re.sub(r'<[^>]+>', '', patch_match.group(1)).strip()
                        if '+' in patchnotes or len(patchnotes) < 5:
                            patchnotes = 'No developer comments for this update'
                    else:
                        patchnotes = 'No data'
                        
                    date_gp = dt.datetime.fromtimestamp(float(result_gp["updated"])) if result_gp["updated"] != "Varies with device" else "Varies with device"

                    return (version_gp, patchnotes, date_gp)

                else:    
                    result = res.json().get(keys, [])
                    if result:
                        if isinstance(result, list):
                            data = result[0]
                        else:
                            data = result

                        return tuple(data.get(a, default_resp) for a in attr) # генератор, чтобы было не фикс. знач элементов
                    else:
                        return(default_resp, default_resp, default_resp)
            else:
    
                if res.status_code == 403:
                    print("Entry Forbidden, status code 403. Try auth")
                    return (default_resp, default_resp, default_resp)
    
                elif res.status_code == 429:
    
                    retry_after = res.headers.get("Retry-After", "60")
    
                    try:
                        wait_time = int(retry_after)
    
                    except Exception as e:
                        print(f"{e}, so the wait time is defaulted to 60 seconds")
                        wait_time = 60
    
                    time.sleep(wait_time + 2)
    
                    res = requests.get(url)
    
                elif res.status_code == 404:
                    print("Seems like the server has moved and there's nothing you can do. Error 404")
                    return (default_resp, default_resp, default_resp)
                else:
                    print("Неизвестная ошибка, попробуйте позже")
                    print(f"Status code: {res.status_code}")
                    return (default_resp, default_resp, default_resp)
    

# Google play
# don't forget to finish it, it is the shortage of the succeeding 3 functions
def parse_google_play(appid : str) -> tuple:
    url = f"https://play.google.com/store/apps/details?id={appid}&hl=ru&gl=ru"
    return safe_requesting(url, "", [], True, gp_id=appid)


def parse_app_store(appid : str) -> tuple:
    url = f"https://itunes.apple.com/lookup?id={appid}&country=ru"
    return(safe_requesting(url, "results", ["version", "releaseNotes", "currentVersionReleaseDate"], False))
    
def parse_ru_store(appid: str) -> tuple:
    url = f"https://backapi.rustore.ru/applicationData/overallInfo/{appid}"
    return(safe_requesting(url, "body", ["versionName", "whatsNew", "appVerUpdatedAt"], False))

    
# it's marked with comments and you prob won't


# ЗАБИТЬ НА ЭТОТ БЛОК, СТАРОЕ ДО ПРОВЕРКИ
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