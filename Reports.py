import os, configparser
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


def report(path="competitor_report.txt"):
    with open(path, 'w', encoding='utf-8') as file:
        file.write("\tCompetitors_LastestUpd_Report\n\n")
        
        files = ["GooglePlay.ini", "AppStore.ini", "RuStore.ini"]
        for fname in files:
            fpath = f"ini_files/{fname}"
            
            if not os.path.exists(fpath):
                continue
                
            print(f"cобираю данные из {fname}")
            txt = get_content(fpath)
            
            print(f"отправил весь {fname} в Gemini, жду ответ")
            ans = gemini_resp(fname, txt)
            
            file.write(f"{ans}\n\n")
            
    print("done")


def gemini_resp(filename, full_text):
    prompt = f"""
    тебе дан список обновлений мобильных приложений из следующего файла {filename}.
    для каждого приложения из списка сделай следующее:
    1. оставь название приложения и версию.
    2. очисти описание от маркетингового мусора по типу риторических вопросов, и пустой воды. Рекламу сериалов, а именно премьеры и тд и тп оставь и выдели отдельно.
    3. напиши нормально (4-5 предложений если можно) только суть изменений. 
    
    * если там только вода ("исправили баги"), напиши: "технические исправления," и вкратце их опиши.
    * если изменений нет или написано "No data", напиши: "изменения не указаны".
    * обязательно выдели появление новых тайлов фильмов и тд и выдели их отдельно снизу указывая платформу, Это - самое важное
    
    Верни ответ строго в формате маркированного списка, для читабельности, например:
    {filename}
    ----------
    * Название_Приложения (v_Версия): Короткое описание сути.
    * Название_Второго (v_Версия): Технические исправления.

    исходные данные:
    {full_text}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        print(f"Ошибка при обработке файла {filename}: {e}")
        return f"{filename}\n----------\nОшибка обработки данных ИИ."


def get_content(fpath):
    config = configparser.ConfigParser()
    config.read(fpath, encoding='utf-8')
    
    content = ""
    for app in config.sections():
        version = config[app].get("version", "N/A")
        desc = config[app].get("desc", "N/A")
        content += f"приложение: {app}\n\tверсия: {version}\n\tОписание: {desc}\n{'-'*20}\n"
        
    return content