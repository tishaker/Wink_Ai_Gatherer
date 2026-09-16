import os
import requests
import datetime
import yaml
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()


def get_client() -> OpenAI:
    base_url = (os.getenv("AI_BASE_URL") or "https://openrouter.ai/api/v1").strip(' "\'')
    api_key = (os.getenv("OPENROUTER_API_KEY") or "DUMMY_KEY_FOR_TESTS").strip(' "\'')
    
    return OpenAI(
        base_url=base_url,
        api_key=api_key,
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

    raw_api_key = os.getenv("OPENROUTER_API_KEY", "")
    api_key = raw_api_key.strip(' "\'')

    if not api_key:
        print("ОШИБКА: OPENROUTER_API_KEY пустой!")
        return f"{filename}\n----------\nОшибка: Не задан API ключ."

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://github.com/Project_Artyom",
        "X-Title": "Project Artyom",
        "Content-Type": "application/json",
        "User-Agent": "ProjectArtyom/1.0"
    }

    model = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-20b").strip(' "\'')
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if response.status_code != 200:
            try:
                error = response.json().get("error", {})
                message = error.get("message", response.text)
            except ValueError:
                message = response.text

            print(f"\nОШИБКА СЕРВЕРА [{response.status_code}]:\n{message}\n")
            return f"{filename}\n----------\nОшибка API (код {response.status_code}): {message}"

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return content.strip()

    except Exception as e:
        print(f"Ошибка выполнения запроса: {e}")
        return f"{filename}\n----------\nОшибка сети: {e}"


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

            print(f"отправил весь {fname} в Gemini через OpenRouter, жду ответ")
            ans = gemini_resp(txt, fname)

            file.write(f"{ans}\n\n")

    print("done writing a report")
    SetDateStamp(path)