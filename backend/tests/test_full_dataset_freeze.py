import json

from app.data.catalog.freeze import MARKER
from scripts import freeze_full_dataset


def test_full_dataset_freeze_is_immutable_and_commit_bound(tmp_path, monkeypatch):
    dataset = tmp_path / "cn-a-research-20100101-20251231-v1"
    dataset.mkdir()
    (tmp_path / ".research/freezes").mkdir(parents=True)
    verified = {"dataset_id": dataset.name, "verification": "PASS"}
    monkeypatch.setattr(freeze_full_dataset, "verify", lambda *_: verified)
    monkeypatch.setattr(
        freeze_full_dataset.subprocess,
        "check_output",
        lambda command, **_: "" if "status" in command else "abc123\n",
    )

    first = freeze_full_dataset.freeze(dataset, tmp_path)
    second = freeze_full_dataset.freeze(dataset, tmp_path)

    assert first == second
    assert first["git_commit"] == "abc123"
    assert json.loads((dataset / MARKER).read_bytes()) == first
