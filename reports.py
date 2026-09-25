import os
import requests
import datetime
import yaml
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def _get_env_value(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name, "")
        cleaned = value.strip(' "\'')
        if cleaned:
            return cleaned
    return default


def _normalize_base_url(base_url: str) -> str:
    value = (base_url or "https://router.ai").strip(' "\'')
    value = value.rstrip("/")
    if not value.endswith("/api/v1"):
        value = f"{value}/api/v1"
    return value


def get_client(base_url: Optional[str] = None, api_key: Optional[str] = None) -> OpenAI:
    final_base_url = _normalize_base_url(base_url or _get_env_value("AI_BASE_URL", "ROUTER_AI_BASE_URL", "OPENAI_BASE_URL", default="https://router.ai"))
    final_api_key = (api_key or _get_env_value("ROUTER_AI_API_KEY", "OPENROUTER_API_KEY", "AI_API_KEY", default="DUMMY_KEY_FOR_TESTS")).strip(' "\'')

    return OpenAI(
        base_url=final_base_url,
        api_key=final_api_key,
    )


def gemini_resp(full_text: str, filename: str = "competitor_report.md") -> str:
    prompt = f"""
    тебе дан список обновлений мобильных приложений из следующего файла {filename}.
    для каждого приложения из списка сделай следующее:
    1. оставь название приложения и версию.
    2. очисти описание от маркетингового мусора по типу риторических вопросов и пустой воды. Рекламу сериалов, а именно премьеры и тд и тп оставь и выдели отдельно.
    3. напиши нормально (4-5 предложений если можно) только суть изменений.

    * если там только вода ("исправили баги"), напиши: "технические исправления," и вкратце их опиши.
    * если изменений нет или написано "No data", напиши: "изменения не указаны".
    * обязательно выдели появление новых тайлов фильмов и тд и выдели их отдельно снизу указывая платформу, Это - самое важное.
    * обязательно выведи отчёт в markdown
    * сделай разделение по платформам, чтобы было понятно, что это за платформа (GooglePlay, AppStore, RuStore)

    Верни ответ строго в формате маркированного списка, для читабельности, например:
    {filename}
    ----------
    * Название_Приложения (v_Версия): Короткое описание сути.
    * Название_Второго (v_Версия): Технические исправления.

    исходные данные:
    {full_text}
    """

    router_api_key = _get_env_value("ROUTER_AI_API_KEY", "AI_API_KEY")
    if not router_api_key:
        print("ОШИБКА: ROUTER_AI_API_KEY пустой!")
        return f"{filename}\n----------\nОшибка: Не задан API ключ."

    router_model = _get_env_value("ROUTER_AI_MODEL", "AI_MODEL", default="openai/gpt-oss-20b")
    try:
        client = get_client(
            base_url=_normalize_base_url(_get_env_value("AI_BASE_URL", "ROUTER_AI_BASE_URL", "OPENAI_BASE_URL", default="https://routerai.ru")),
            api_key=router_api_key,
        )
        response = client.chat.completions.create(
            model=router_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        content = response.choices[0].message.content
        return (content or "").strip()
    except Exception as exc:
        print(f"Ошибка выполнения запроса через Router AI: {exc}")
        return f"{filename}\n----------\nОшибка сети: {exc}"


def get_content(fpath: str) -> str:
    with open(fpath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data:
        return ""

    content = ""
    for app, info in data.items():
        app_id = info.get("AppId", "N/A")
        version = info.get("version", "N/A")
        desc = info.get("desc", "N/A")
        date_modified = info.get("date_modified", "N/A")

        content += (
            f"приложение: {app}\n"
            f"\tAppId: {app_id}\n"
            f"\tверсия: {version}\n"
            f"\tдата изменения: {date_modified}\n"
            f"\tописание: {desc}\n"
            f"{'-' * 30}\n"
        )

    return content


def SetDateStamp(filename: str = "competitor_report.txt") -> None:
    now =  datetime.datetime.now()
    months = [
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря"
    ]
    with open(filename, "a", encoding="utf-8") as file:
        file.write(
            f"\nОтчёт был сформирован {now.year} года {now.day} {months[now.month - 1]} "
            f"в {now.hour} часов {now.minute} минут {now.second}.{(now.microsecond // 1000):03d} секунд"
        )

    print("\ntimestamp set")
    
    

def report(path: str = "competitor_report.txt") -> None:
    # Удаляем старый отчёт с мусорным CSS перед формированием нового
    if os.path.exists(path):
        os.remove(path)

    with open(path, "w", encoding="utf-8") as file:
        file.write("\tCompetitors_LastestUpd_Report\n\n")

        files = ["GooglePlay.yml", "AppStore.yml", "RuStore.yml"]
        for fname in files:
            fpath = f"yaml_files/{fname}"

            if not os.path.exists(fpath):
                continue

            print(f"собираю данные из {fname}")
            txt = get_content(fpath)

            print(f"отправил весь {fname} в модель через RouterAI, жду ответ")
            ans = gemini_resp(txt, fname)

            file.write(f"{ans}\n\n")

    print("done writing a report")
    SetDateStamp(path)