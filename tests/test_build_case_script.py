from pathlib import Path

from scripts.build_case import load_seed_file


def test_load_seed_file_normalizes_outcome_alias(tmp_path):
    path = tmp_path / "seed.jsonl"
    path.write_text('{"outcome": "worsening", "difficulty": "hard", "Primary Site": "C34.1"}\n')

    entries = load_seed_file(path)

    assert len(entries) == 1
    entry = entries[0]
    assert entry["intended_outcome"] == "worsening"
    assert "outcome" not in entry
    assert entry["difficulty"] == "hard"
    assert entry["raw_variables"]["Primary Site"] == "C34.1"


def test_load_seed_file_keeps_intended_outcome(tmp_path):
    path = tmp_path / "seed.jsonl"
    path.write_text('{"intended_outcome": "improving", "case_type": "chronic"}\n')

    entries = load_seed_file(path)

    assert entries[0]["intended_outcome"] == "improving"
    assert entries[0]["case_type"] == "chronic"
