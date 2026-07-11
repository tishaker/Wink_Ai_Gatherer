import os, sys, configparser

def config_write(path, section, id, version, desc, ddt, folder_name="ini_files"):
    os.makedirs(f"{folder_name}/", exist_ok=True)
    config = configparser.ConfigParser()
    config.read(f"{folder_name}/{path}", encoding='utf-8')
    config[section] = {
        "id": id,
        "version": version,
        "desc": desc,
        "date_modified": ddt
    }
    with open(f"{folder_name}/{path}", 'w', encoding='utf-8') as configfile:
        config.write(configfile)