import yaml
from reports import get_content
from yield_ import yaml_write
import responses
from yield_ import safe_requesting
from reports import gemini_resp
from unittest.mock import patch

# get_content tests


def test_get_content(tmp_path) -> None:
    
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
    
def test_yaml_write(tmp_path) -> None:
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
    
    
@responses.activate
@patch("yield_.gp.app")
def test_safe_requesting_test_googleplay_success(mock_gp_app) -> None:
    # Arrange
    url = 'https://google_winktest.com'
    
    fake_html = """
    <html>
        <body>
            ["["12.34.56"]"]
            <div>Обновлено</div>
            <div>24 июля 2026 г.</div>
            <div>Что нового</div>
            <div>Исправили баги, улучшили стабильность.</div>
        </body>
    </html>
    """
    responses.add(responses.GET, url, body=fake_html, status=200)
    
    mock_gp_app.return_value = {
        "version": "12.34.56",
        "updated": 1784803200
    }
    # Act
    version, patchnotes, date_modif = safe_requesting(url, keys='', attr=[], is_gp=True, gp_id="wink.example.app")
    
    # Assert
    assert version == "12.34.56"
    assert patchnotes == "Исправили баги, улучшили стабильность."
    assert date_modif != "unknown"
    
    
@responses.activate
def test_safe_requesting_status_403() -> None:
    url = "https://the_site_that_moved.com"
    responses.add(responses.GET, url, status=403)
        
    # Act
    v, p, g = safe_requesting(url, '', [], False)
    
    # Assert
    assert v == "unknown"
    assert p == "unknown"
    assert g == "unknown"

@responses.activate
def test_safe_requesting_status_429() -> None:
    # Arrange
    url = "https://apple_winktest.com"
    responses.add(responses.GET, url, status=429, headers={"Retry-After": '0'})
    
    fake_json = {
        'results': [
            {
                "version": "1.0.0",
                "notes": "Fake_release_notes",
                "date": "2026-08-10"
            }
        ]
    }
    responses.add(responses.GET, url, json=fake_json, status=200)    
    
    # Act
    v, p, g = safe_requesting(url, 'results', ["version", "notes", "date"], False)
    
    # Assert
    assert v == "1.0.0"
    assert p == "Fake_release_notes"
    assert g == "2026-08-10"
    
@responses.activate
def test_safe_requesting_status_404() -> None:
    # Arrange
    url = "https://the_unexisting_website.com"
    responses.add(responses.GET, url, status=404)
    
    # Act
    v, p, g = safe_requesting(url, '', [], False, "known")
    
    # Assert
    assert v == "known"
    assert p == "known"
    assert g == "known"
