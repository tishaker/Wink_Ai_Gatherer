import pytest
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
    assert result == {
        "App": {
            "AppId": "123",
            "version": 1.0,
            "desc": "Test",
            "date_modified": "2026-07-20",
        }
    }