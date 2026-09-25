import requests
import re
import os
import yaml
import time
import google_play_scraper as gp
import datetime as dt

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
    max_retries = 3
    retry_count = 0

    while True:
        try:
            res = requests.get(url, timeout=20)
        except requests.RequestException as exc:
            print(f"Request failed for {url}: {exc}")
            return (default_resp, default_resp, default_resp)

        if res.status_code == 200:
            if is_gp:
                try:
                    result_gp = gp.app(gp_id, lang='ru', country='ru')
                except Exception as exc:
                    print(f"Google Play scraper failed for {gp_id}: {exc}")
                    return (default_resp, default_resp, default_resp)

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

            try:
                payload = res.json()
            except ValueError:
                return (default_resp, default_resp, default_resp)

            result = payload.get(keys, [])
            if result:
                if isinstance(result, list):
                    data = result[0]
                else:
                    data = result
                return tuple(data.get(a, default_resp) for a in attr)
            return (default_resp, default_resp, default_resp)

        if res.status_code == 403:
            print("Entry Forbidden, status code 403. Try auth")
            return (default_resp, default_resp, default_resp)

        if res.status_code == 429:
            if retry_count >= max_retries:
                print("Rate limit exceeded too many times. Stopping retry loop.")
                return (default_resp, default_resp, default_resp)

            retry_count += 1
            retry_after = res.headers.get("Retry-After", "30")
            try:
                wait_time = int(retry_after)
            except (TypeError, ValueError):
                wait_time = 30

            print(f"Rate limit exceeded, retrying in {wait_time} seconds... (Attempt {retry_count}/{max_retries})")
            time.sleep(wait_time)
            continue

        if res.status_code == 404:
            print("Seems like the server has moved and there's nothing you can do. Error 404")
            return (default_resp, default_resp, default_resp)

        print("Неизвестная ошибка, попробуйте позже")
        print(f"Status code: {res.status_code}")
        return (default_resp, default_resp, default_resp)


def parse_google_play(appid : str) -> tuple:
    url = f"https://play.google.com/store/apps/details?id={appid}&hl=ru&gl=ru"
    return safe_requesting(url, "", [], True, gp_id=appid)


def parse_app_store(appid : str) -> tuple:
    url = f"https://itunes.apple.com/lookup?id={appid}&country=ru"
    return(safe_requesting(url, "results", ["version", "releaseNotes", "currentVersionReleaseDate"], False))


def parse_ru_store(appid: str) -> tuple:
    """
    RuStore сменил API: старый backapi.rustore.ru/applicationData/overallInfo мёртв (400),
    а /api/v1/application отдаёт 404. Сайт переехал на Next.js SSR.
    Данные встроены в RSC-payload HTML страницы каталога — парсим их оттуда.
    """
    url = f"https://www.rustore.ru/catalog/app/{appid}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "ru-RU,ru;q=0.9",
    }
    res = requests.get(url, headers=headers, timeout=15)

    if res.status_code == 404:
        return ("unknown", "Приложение не найдено в RuStore", "unknown")
    if res.status_code != 200:
        return ("unknown", f"Ошибка RuStore: {res.status_code}", "unknown")

    html = res.text
    default = "unknown"

    m = re.search(r'versionName\\":\\"([^\\]+)', html)
    version = m.group(1) if m else default

    m = re.search(r'whatsNew\\":\\"(.+?)(?=\\"[^\\])', html)
    if m:
        patchnotes = m.group(1).replace("\\n", "\n").replace("\\\\", "\\").replace('\\"', '"')
    else:
        patchnotes = "изменения не указаны"

    m = re.search(r'appVerUpdatedAt\\":\\"([^\\]+)', html)
    date_updated = m.group(1) if m else default

    return (version, patchnotes, date_updated)