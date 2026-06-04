"""版本号工具测试"""

import re

from chestnut_studio.utils.version import _read_pyproject_toml, get_version


class TestGetVersion:
    def test_returns_string(self):
        v = get_version()
        assert isinstance(v, str)
        assert len(v) > 0

    def test_semver_format(self):
        v = get_version()
        assert re.match(r"^\d+\.\d+\.\d+", v) is not None, f"版本号格式异常: {v}"


class TestReadPyprojectToml:
    def test_returns_semver_string(self):
        v = _read_pyproject_toml()
        assert v == "unknown" or re.match(r"^\d+\.\d+\.\d+", v) is not None
