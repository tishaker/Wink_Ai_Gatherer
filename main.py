import yield_
from reports import report



if __name__ == "__main__":
    print("Начало работы скрипта")
    
    
    print("\nFetching AppStore data")
    yield_.fetch_appstore_data()
    
    print("Fetching RuStore data")
    yield_.fetch_rustore_data()
    
    report("competitor_report.txt")