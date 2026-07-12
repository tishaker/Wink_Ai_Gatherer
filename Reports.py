import os, configparser, time
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


def report(path):
    with open(path, 'w', encoding='utf-8') as file:
        file.write("\tCompetitors_LastestUpd_Report\n\n")
        
        files = ["GooglePlay.ini", "AppStore.ini", "RuStore.ini"]
        for f_name in files:
            fpath = f"ini_files/{f_name}"
            
            if not os.path.exists(fpath):
                continue
                
            # This triggers the left-side function to run the AI on this specific file
            config_reports(fpath, file, f_name)
    

def summarize_patchnotes(raw_text):
    # Skip processing if there are no real patch notes to save API tokens
    if raw_text in ["No data", "Разрабы не дали комментария к обновлению"] or len(raw_text) < 10:
        return "Изменения не указаны"

    prompt = f"""
    Тебе дан патчноут мобильного приложения. Очисти его от маркетингового мусора, 
    рекламы сериалов и пустой воды. Напиши ОЧЕНЬ КОРОТКО (буквально 1-2 предложения), 
    какие реальные технические или продуктовые изменения произошли.
    Если там только вода ("исправили баги"), так и напиши: "Технические исправления".

    Патчноут:
    {raw_text}
    """

    try:
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=prompt,
        )
        return response.text.strip()
    except Exception as ai_error:
        print(f"AI summarizing failed: {ai_error}")
        return raw_text


def config_reports(fpath, file, f_name):
    config = configparser.ConfigParser()
    config.read(fpath, encoding='utf-8')
    
    file.write(f_name + "\n" + "-"*10 + "\n\n")
    
    for app in config.sections():
        version = config[app].get("version", "N/A")
        raw_desc = config[app].get("desc", "N/A")
        
        # Запускаем ИИ-агента для обработки текста
        summary = summarize_patchnotes(raw_desc)
        
        file.write(f"* {app} (v_{version}): {summary}\n")
        
        
    file.write("\n")