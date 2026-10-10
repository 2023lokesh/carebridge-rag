"""Prevent production public freeze manifest from drifting from private DEV loader contract."""
import json
import re
from collections import Counter
from pathlib import Path


def test_published_frozen_manifest_matches_loader_contract():
    p = Path(__file__).resolve().parents[1] / "data" / "frozen_split_manifest.json"
    m = json.loads(p.read_text(encoding="utf-8"))
    assert re.fullmatch(r"[0-9a-f]{64}", m["dev_sha256"])
    assert len(m["dev_ids"]) == len(set(m["dev_ids"])) == 24
    assert len(m["test_ids"]) == len(set(m["test_ids"])) == 16
    assert set(m["dev_ids"]).isdisjoint(m["test_ids"])
    categories = m["counts_by_category"]
    assert {k: v["dev"] for k, v in categories.items()} == m["category_dev"]
    assert {k: v["test"] for k, v in categories.items()} == m["category_test"]
    assert sum(v["dev"] for v in categories.values()) == m["dev_count"] == 24
    assert sum(v["test"] for v in categories.values()) == m["test_count"] == 16
    assert "question" not in m and "gold_answer" not in m
