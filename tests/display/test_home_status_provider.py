from src.smartscreen_display.home_status import (
    FileHomeStatusProvider,
)


def test_file_provider_returns_empty_when_missing(tmp_path):
    provider = FileHomeStatusProvider(
        tmp_path / "missing.json"
    )

    assert provider.get_items() == []


def test_file_provider_reads_items(tmp_path):
    path = tmp_path / "home.json"

    path.write_text(
        '''
{
  "items": [
    {
      "name": "门窗",
      "state": "已关闭"
    },
    {
      "name": "客厅灯",
      "state": "关闭"
    }
  ]
}
''',
        encoding="utf-8",
    )

    provider = FileHomeStatusProvider(path)

    assert provider.get_items() == [
        {
            "name": "门窗",
            "state": "已关闭",
        },
        {
            "name": "客厅灯",
            "state": "关闭",
        },
    ]


def test_file_provider_ignores_invalid_json(tmp_path):
    path = tmp_path / "home.json"
    path.write_text(
        "{invalid",
        encoding="utf-8",
    )

    provider = FileHomeStatusProvider(path)

    assert provider.get_items() == []


def test_file_provider_ignores_invalid_items(tmp_path):
    path = tmp_path / "home.json"

    path.write_text(
        '{"items":"invalid"}',
        encoding="utf-8",
    )

    provider = FileHomeStatusProvider(path)

    assert provider.get_items() == []
