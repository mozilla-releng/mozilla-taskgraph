import pytest

from mozilla_taskgraph.util.signed_artifacts import get_signed_artifacts


@pytest.mark.parametrize(
    "input_file, formats, behavior, expected",
    [
        ("example.dmg", [], None, {"example.tar.gz": True, "example.pkg": False}),
        ("example.dmg", [], "mac_sign", {"example.tar.gz": True, "example.pkg": False}),
        ("example.dmg", [], "other", {"example.tar.gz": True, "example.pkg": True}),
        ("example.zip", [], None, {"example.zip": True}),
        ("example.zip", ["gcp_prod_autograph_gpg"], None, {"example.zip.asc": True}),
    ],
)
def test_get_signed_artifacts(input_file, formats, behavior, expected):
    result = get_signed_artifacts(input_file, formats, behavior=behavior)
    for artifact, exists in expected.items():
        if exists:
            assert artifact in result
        else:
            assert artifact not in result
