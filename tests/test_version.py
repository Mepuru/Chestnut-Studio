"""版本号工具测试"""

import re
from importlib.metadata import PackageNotFoundError
from unittest.mock import patch

from chestnut_studio.utils.version import _read_pyproject_toml, get_version


class TestGetVersion:
    def test_returns_string(self):
        v = get_version()
        assert isinstance(v, str)
        assert len(v) > 0

    def test_semver_format(self):
        v = get_version()
        assert re.match(r"^\d+\.\d+\.\d+", v) is not None, f"版本号格式异常: {v}"

    def test_fallback_when_package_not_found(self):
        """当 importlib.metadata 找不到包时，回退到 pyproject.toml 读取"""
        with patch("chestnut_studio.utils.version.version") as mock_version:
            mock_version.side_effect = PackageNotFoundError
            v = get_version()
            assert re.match(r"^\d+\.\d+\.\d+", v) is not None, f"回退版本号格式异常: {v}"


class TestReadPyprojectToml:
    def test_returns_semver_string(self):
        v = _read_pyproject_toml()
        assert v == "unknown" or re.match(r"^\d+\.\d+\.\d+", v) is not None
