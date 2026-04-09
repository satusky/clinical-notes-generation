import pytest

from scripts.generate import resolve_seed_files


def test_resolve_seed_files_rejects_both_inputs():
    with pytest.raises(ValueError, match="either --seed-file or --seed-dir"):
        resolve_seed_files("seed.json", "seeds/")


def test_resolve_seed_files_seed_dir_no_matches(tmp_path):
    with pytest.raises(FileNotFoundError, match="No seed files"):
        resolve_seed_files(None, str(tmp_path))


def test_resolve_seed_files_seed_dir_matches(tmp_path):
    a = tmp_path / "case_seed_1.json"
    b = tmp_path / "foo_seed_2.json"
    c = tmp_path / "ignore.json"
    a.write_text("{}")
    b.write_text("{}")
    c.write_text("{}")

    resolved = resolve_seed_files(None, str(tmp_path))

    assert resolved == sorted([str(a), str(b)])


def test_resolve_seed_files_default_example_case():
    assert resolve_seed_files(None, None) == [None]
