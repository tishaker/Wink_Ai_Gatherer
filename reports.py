import os
import yaml
import datetime as time
from google import genai
from dotenv import load_dotenv


load_dotenv()

def get_client(api_key: str | None = None) -> genai.Client:
    if api_key:
        return genai.Client(api_key=api_key)
    
    # that's when we return the other key if the main one is absent, for example in tests
    return genai.Client(api_key=os.getenv("GEMINI_API_KEY") or "DUMMY_KEY_FOR_TESTS")


def report(path: str = "competitor_report.txt") -> None:
    with open(path, 'w', encoding='utf-8') as file:
        file.write("\tCompetitors_LastestUpd_Report\n\n")
        
        files = ["GooglePlay.yaml", "AppStore.yaml", "RuStore.yaml"]
        for fname in files:
            fpath = f"yaml_files/{fname}"
            
            if not os.path.exists(fpath):
                continue
                
            print(f"cобираю данные из {fname}")
            txt = get_content(fpath)
            
            print(f"отправил весь {fname} в Gemini, жду ответ")
            ans = gemini_resp(txt, fname)
            
            file.write(f"{ans}\n\n")
            
    print("done writing a report")
    
    SetDateStamp()


def gemini_resp(full_text: str, filename: str = "competitor_report.txt") -> str:
    prompt = f"""
    тебе дан список обновлений мобильных приложений из следующего файла {filename}.
    для каждого приложения из списка сделай следующее:
    1. оставь название приложения и версию.
    2. очисти описание от маркетингового мусора по типу риторических вопросов и пустой воды. Рекламу сериалов, а именно премьеры и тд и тп оставь и выдели отдельно.
    3. напиши нормально (4-5 предложений если можно) только суть изменений. 
    
    * если там только вода ("исправили баги"), напиши: "технические исправления," и вкратце их опиши.
    * если изменений нет или написано "No data", напиши: "изменения не указаны".
    * обязательно выдели появление новых тайлов фильмов и тд и выдели их отдельно снизу указывая платформу, Это - самое важное.
    
    Верни ответ строго в формате маркированного списка, для читабельности, например:
    {filename}
    ----------
    * Название_Приложения (v_Версия): Короткое описание сути.
    * Название_Второго (v_Версия): Технические исправления.

    исходные данные:
    {full_text}
    """
    
    try:
        response = get_client().models.generate_content(
            model='gemini-3.5-flash',
            contents=prompt,
        )
        return response.text.strip() if response.text else "AI failed to produce a response"
    except Exception as e:
        print(f"Ошибка при обработке файла {filename}: {e}")
        return f"{filename}\n----------\nОшибка обработки данных ИИ."


def get_content(fpath: str) -> str:
    with open(fpath, 'r', encoding='utf-8') as f:
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
    now = time.datetime.now()
    months = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]
    with open(filename, 'a', encoding="utf-8") as file:
        file.write(f"\nОтчёт был сформирован {now.year} года {now.day} {months[now.month - 1]} в {now.hour} часов {now.minute} минут {now.second}.{(now.microsecond // 1000):03d} секунд")
        
    print("\ntimestamp set")