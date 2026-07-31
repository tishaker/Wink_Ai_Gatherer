import pytest
import os
import yaml
from reports import get_content
from yield_ import yaml_write


# get_content tests


def test_get_content(tmp_path):
    
    # Arrange
    fake_yaml = tmp_path / "test.yaml"
    fake_yaml.write_text(
        "App:\n"
        "  AppId: '123'\n"
        "  version: 1.0\n"
        "  desc: 'Test'\n"
        "  date_modified: '2026-07-20'\n"
    )

    # Act
    result = get_content(str(fake_yaml))

    # Assert
    expected_output = (
        "приложение: App\n"
        "\tAppId: 123\n"
        "\tверсия: 1.0\n"
        "\tдата изменения: 2026-07-20\n"
        "\tописание: Test\n"
        "------------------------------\n"
    )
    assert result == expected_output
    
def test_yaml_write(tmp_path):
    # Arrange
    test_folder = tmp_path / "yaml_files"
    test_file = test_folder / "output_yaml"
    
    
    # Act
    yaml_write(
        path=str(test_file), # Path to the file in system
        section="Google Play", # e.g. Google Play, AppStore..
        AppId="1234", # AppStore uses int format, but Google Play and RuStore use str app IDs so we need str
        version="v1.0", # e.g. v1.4.53
        desc="bla bla", # e.g. Поработали «под капотом»: улучшили стабильность приложения, ...
        ddt="2026-07-20 09:20:50", # e.g. 2026-07-20 09:20:50
        folder_name=str(test_folder) # e.g. "Work IDs" || Output dir
    )

    # Assert
    
    assert test_file.exists()
    with open(test_file, "r", encoding="utf-8") as test_file:
        data = yaml.safe_load(test_file)
        
    assert "Google Play" in data
    assert data["Google Play"]["AppId"] == "1234"
    assert data["Google Play"]["desc"] == "bla bla"