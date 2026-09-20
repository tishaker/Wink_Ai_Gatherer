from yield_ import parse_app_store, parse_ru_store, parse_google_play, yaml_write
from reports import report
import yaml
from pathlib import Path
    
stores = [
    {"name": "GooglePlay", "file": "GooglePlay.yml", "parser": parse_google_play},
    {"name": "AppStore", "file": "AppStore.yml", "parser": parse_app_store},
    {"name": "RuStore", "file": "RuStore.yml", "parser": parse_ru_store}
]

if __name__ == "__main__":
    print("Начало работы скрипта")
    
    app_ids_path = Path(__file__).with_name("AppIds_list.yaml")
    with app_ids_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    
    for store in stores:
        competitors_list = data.get(store["name"], {})
        
        if not competitors_list:
            print(f"[WARNING] Список приложений для {store['name']} пуст или отсутствует!")
            continue

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