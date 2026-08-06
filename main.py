from yield_ import parse_app_store, parse_ru_store, parse_google_play, yaml_write
from reports import report
import yaml

with open("AppIds_list.yaml", "r", encoding="utf-8") as file:
    data = yaml.safe_load(file)

print("Начало работы скрипта")
    
    
stores = [
    {"name": "GooglePlay", "file": "GooglePlay.yaml", "parser": parse_google_play},
    {"name": "AppStore", "file": "AppStore.yaml", "parser": parse_app_store},
    {"name": "RuStore", "file": "RuStore.yaml", "parser": parse_ru_store}
]

for store in stores:
    competitors_list = data.get(store["name"], {})
    
    print(f"\nСоединение установленно, проверяю {store['name']}\n")
    
    for competitor, app_id in competitors_list.items():
        if app_id == "nonexistent":
            continue
        
        try:
            version, patchnotes, date_modif = store["parser"](app_id)
            print(f"\n{competitor}:")
            print(f"Версия: {version}\nИзменения: {patchnotes}\nДата: {date_modif}")
            
            yaml_write(
                path=store["file"],
                section=competitor,
                AppId=app_id,
                version=version,
                desc=patchnotes,
                ddt=date_modif
            )
                
        except Exception as e:
            print(f"Error for {competitor}: {e}")
    

report("competitor_report.txt")