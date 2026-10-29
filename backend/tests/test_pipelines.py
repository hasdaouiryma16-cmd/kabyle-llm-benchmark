import random
from collections import Counter

from app.contamination import ContaminationIndex, protected_strings
from pipelines.check_contamination import candidates
from pipelines.common import write_jsonl
from pipelines.prepare import SFT_TEMPLATES, clean, filter_pairs, sft_records

TEST_SET = [{"id": "t1", "prompt": "Traduis : « Le soleil se lève sur la montagne enneigée. »",
             "source_text": "Le soleil se lève sur la montagne enneigée.",
             "references": ["ref-secrete"]}]  # fmt: skip


def guard():
    return ContaminationIndex(protected_strings(TEST_SET))


def test_clean_normalizes_unicode_and_spaces():
    assert clean("  ḥ  a\t b ") == "ḥ a b"


def test_filter_pairs_removes_invalid_duplicates_and_test_sentences():
    stats: Counter = Counter()
    raw = [
        ("tatoeba", "Il pleut.", "kab-1"),
        ("tatoeba", "Il pleut.", "kab-1"),  # doublon
        ("tatoeba", "x" * 400, "kab-2"),  # trop long
        ("tatoeba", "مرحبا", "kab-3"),  # mauvaise écriture
        (
            "tatoeba",
            "Le soleil se lève sur la montagne enneigée !",
            "kab-4",
        ),  # quasi-doublon du test
        ("tatoeba", "Bonjour.", "REF-SECRETE"),  # référence du test
    ]
    kept = filter_pairs(raw, guard(), stats)
    assert [p["kab"] for p in kept] == ["kab-1"]
    assert stats["removed_duplicate"] == 1
    assert stats["removed_invalid"] == 2
    assert stats["removed_contamination"] == 2


def test_sft_records_cover_both_directions():
    stats: Counter = Counter()
    pairs = [{"fr": "Il pleut.", "kab": "kab-1", "source": "t"}]
    records = sft_records(pairs, random.Random(0), guard(), stats)
    assert len(records) == 2
    assert records[0]["messages"][1]["content"] == "kab-1"
    assert records[1]["messages"][1]["content"] == "Il pleut."
    assert stats == {"kept": 2}


def test_sft_records_drop_prompts_matching_a_test_prompt():
    # Consigne de test = gabarit d'entraînement + phrase : la consigne générée est écartée
    test_set = [
        {"id": f"t{i}", "prompt": template.format(src=src)}
        for i, (template, src) in enumerate(
            (t, src)
            for direction, src in (("fr_kab", "Il pleut."), ("kab_fr", "kab-1"))
            for t in SFT_TEMPLATES[direction]
        )
    ]
    stats: Counter = Counter()
    pairs = [{"fr": "Il pleut.", "kab": "kab-1", "source": "t"}]
    index = ContaminationIndex(protected_strings(test_set))
    assert sft_records(pairs, random.Random(0), index, stats) == []
    assert stats == {"removed_contamination": 2}


def test_check_contamination_scans_every_output(tmp_path):
    write_jsonl(tmp_path / "fewshot_pool.jsonl", [{"fr": "a", "kab": "b"}])
    write_jsonl(tmp_path / "sft_train.jsonl", [{"messages": [{"role": "user", "content": "c"}]}])
    (tmp_path / "mono_kab.txt").write_text("d\n", encoding="utf-8")
    assert sorted(text for _, text in candidates(tmp_path)) == ["a", "b", "c", "d"]
