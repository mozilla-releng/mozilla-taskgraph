from types import SimpleNamespace

import pytest

from mozilla_taskgraph.util.signed_artifacts import (
    generate_specifications_of_artifacts_to_sign,
    get_signed_artifacts,
)


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


def _job(build_platform, **attributes):
    return {
        "attributes": {"build_platform": build_platform, **attributes},
        "dependencies": {"build": "build-dep"},
    }


def _linux_config(make_transform_config, artifact_build=False):
    dep = SimpleNamespace(attributes={"artifact-build": artifact_build})
    return make_transform_config(kind_dependencies_tasks={"build-dep": dep})


def test_generate_specifications_source(make_transform_config):
    specs = generate_specifications_of_artifacts_to_sign(
        make_transform_config(),
        _job("linux64-shippable"),
        kind="release-source-signing",
    )
    assert specs == [
        {
            "artifacts": ["public/build/source.tar.xz"],
            "formats": ["gcp_prod_autograph_gpg"],
        }
    ]


def test_generate_specifications_macosx_signing(make_transform_config):
    specs = generate_specifications_of_artifacts_to_sign(
        make_transform_config(), _job("macosx64-shippable"), kind="mac-signing"
    )
    assert specs == [
        {
            "artifacts": ["public/build/{locale}/target.dmg"],
            "formats": ["macapp", "gcp_prod_autograph_widevine"],
        }
    ]


def test_generate_specifications_macosx_langpack(make_transform_config):
    specs = generate_specifications_of_artifacts_to_sign(
        make_transform_config(),
        _job("macosx64-shippable", chunk_locales=["ja-JP-mac"]),
        kind="mac-signing",
    )
    assert specs[-1] == {
        "artifacts": ["public/build/ja-JP-mac/target.langpack.xpi"],
        "formats": ["gcp_prod_autograph_langpack"],
    }


def test_generate_specifications_win_stub(make_transform_config):
    specs = generate_specifications_of_artifacts_to_sign(
        make_transform_config(), _job("win64-shippable", **{"stub-installer": True})
    )
    assert specs[0]["artifacts"] == [
        "public/build/{locale}/setup.exe",
        "public/build/{locale}/setup-stub.exe",
    ]


def test_generate_specifications_linux(make_transform_config):
    specs = generate_specifications_of_artifacts_to_sign(
        _linux_config(make_transform_config), _job("linux64-opt"), dep_kind="build"
    )
    assert specs == [
        {
            "artifacts": ["public/build/{locale}/target.tar.xz"],
            "formats": ["gcp_prod_autograph_gpg", "gcp_prod_autograph_widevine"],
        }
    ]


def test_generate_specifications_unknown_platform_raises(make_transform_config):
    with pytest.raises(Exception, match="Platform not implemented for signing"):
        generate_specifications_of_artifacts_to_sign(
            make_transform_config(), _job("bsd64-opt")
        )


def test_generate_specifications_strip_locale_template(make_transform_config):
    specs = generate_specifications_of_artifacts_to_sign(
        _linux_config(make_transform_config),
        _job("linux64-opt"),
        keep_locale_template=False,
        dep_kind="build",
    )
    assert specs[0]["artifacts"] == ["public/build/target.tar.xz"]


def test_generate_specifications_partner_strips_widevine(make_transform_config):
    specs = generate_specifications_of_artifacts_to_sign(
        _linux_config(make_transform_config),
        _job("linux64-opt"),
        kind="release-partner-repack-signing",
        dep_kind="build",
    )
    assert specs[0]["formats"] == ["gcp_prod_autograph_gpg"]
