"""更新检查器测试"""

from chestnut_studio.utils.update_checker import API_URL, parse_release_data, parse_version


class TestApiUrl:
    def test_url_format(self):
        assert API_URL.startswith("https://api.github.com/")
        assert "Mepuru/Chestnut-Studio" in API_URL
        assert API_URL.endswith("/releases/latest")


class TestParseVersion:
    def test_with_v_prefix(self):
        assert parse_version("v2.3.0") == (2, 3, 0)

    def test_without_v_prefix(self):
        assert parse_version("2.3.0") == (2, 3, 0)

    def test_major_only(self):
        assert parse_version("v3") == (3,)

    def test_many_segments(self):
        assert parse_version("v1.2.3.4") == (1, 2, 3, 4)

    def test_zero_padded(self):
        assert parse_version("v01.02.03") == (1, 2, 3)


class TestParseReleaseData:
    def test_new_version_found(self):
        data = {
            "tag_name": "v2.5.0",
            "assets": [{"browser_download_url": "https://example.com/app.exe"}],
            "body": "新功能发布",
            "html_url": "https://github.com/Mepuru/Chestnut-Studio/releases/v2.5.0",
        }
        info = parse_release_data(data, "2.4.0")
        assert info is not None
        assert info.latest_version == "2.5.0"
        assert info.download_url == "https://example.com/app.exe"
        assert info.release_notes == "新功能发布"
        assert info.release_url == "https://github.com/Mepuru/Chestnut-Studio/releases/v2.5.0"

    def test_same_version(self):
        data = {"tag_name": "v2.4.0", "assets": []}
        assert parse_release_data(data, "2.4.0") is None

    def test_older_version(self):
        data = {"tag_name": "v2.3.1", "assets": []}
        assert parse_release_data(data, "2.4.0") is None

    def test_no_tag(self):
        assert parse_release_data({}, "2.4.0") is None

    def test_empty_tag(self):
        assert parse_release_data({"tag_name": ""}, "2.4.0") is None

    def test_no_assets(self):
        data = {
            "tag_name": "v2.5.0",
            "assets": [],
            "body": "说明文字",
            "html_url": "https://github.com/release",
        }
        info = parse_release_data(data, "2.4.0")
        assert info is not None
        assert info.download_url == ""
        assert info.release_notes == "说明文字"

    def test_no_assets_key(self):
        data = {"tag_name": "v2.5.0", "body": "说明", "html_url": "https://github.com/release"}
        info = parse_release_data(data, "2.4.0")
        assert info is not None
        assert info.download_url == ""
