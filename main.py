from yield_ import parse_app_store, parse_ru_store, parse_google_play, yaml_write
from reports import report
import yaml
import os
import time
from pathlib import Path

stores = [
    {"name": "GooglePlay", "file": "GooglePlay.yml", "parser": parse_google_play},
    {"name": "AppStore", "file": "AppStore.yml", "parser": parse_app_store},
    {"name": "RuStore", "file": "RuStore.yml", "parser": parse_ru_store}
]


def run_cycle() -> None:
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


if __name__ == "__main__":
    interval_days = int(os.getenv("RUN_INTERVAL_DAYS", "7"))
    interval_seconds = max(1, interval_days) * 24 * 60 * 60
    run_once = os.getenv("RUN_ONCE", "0").lower() in {"1", "true", "yes"}

    while True:
        run_cycle()
        if run_once:
            print("RUN_ONCE=1, завершаю запуск после одного цикла")
            break
        print(f"Следующий запуск через {interval_days} дней ({interval_seconds} секунд)")
        time.sleep(interval_seconds)