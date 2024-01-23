from unittest.mock import mock_open, patch

from mozilla_taskgraph.version import default_parser


def test_default_parser(repo_root):
    version = "1.0.0"

    with patch("mozilla_taskgraph.version.open", mock_open(read_data=version)) as m:
        assert default_parser({}) == version
        m.assert_called_with(str(repo_root / "version.txt"))
