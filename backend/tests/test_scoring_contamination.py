from app.contamination import ContaminationIndex, protected_strings
from app.scoring import LanguageDetector, chrf, clean_output, detect_script, language_ok


def test_clean_output_strips_wrapping_quotes_only():
    assert clean_output("  « texte »  ") == "texte"
    assert clean_output('"a" et "b"') == '"a" et "b"'


def test_chrf_identity_and_absence():
    assert chrf("abc def", ["abc def"]) == 100.0
    assert chrf("", ["abc"]) == 0.0
    assert chrf("abc", []) is None


def test_detect_script():
    assert detect_script("ⴰⵣⵓⵍ") == "tifinagh"
    assert detect_script("مرحبا بكم") == "arabic"
    assert detect_script("ɛ ɣ ḥ abc") == "latin"
    assert detect_script("123 !") is None


def test_heuristic_detector_never_claims_kabyle():
    detector = LanguageDetector(None)
    assert detector.detect("je ne sais pas ce que tu dis").lang == "fra"
    assert detector.detect("مرحبا بكم").lang == "ara"
    assert detector.detect("ɛ ɣ ḥ abc xyz").lang is None


def test_language_ok_flags_obvious_failures_only():
    detector = LanguageDetector(None)
    french = detector.detect("je ne sais pas ce que tu dis")
    assert language_ok("kab", french, "latin", "latin") is False
    unknown = detector.detect("ɛ ɣ ḥ abc xyz")
    assert language_ok("kab", unknown, "latin", "latin") is None
    assert language_ok("kab", unknown, "latin", "tifinagh") is False
    assert language_ok("fr", french, "latin", "latin") is True


def test_contamination_exact_and_near_duplicates():
    records = [{"id": "t1", "prompt": "Traduis : « La maison de mon grand-père est très grande. »",
                "references": ["ref-courte"]}]  # fmt: skip
    index = ContaminationIndex(protected_strings(records))
    assert index.check("REF-COURTE !").kind == "exact"
    near = index.check("Traduis : « La maison de mon grand-père est très grande »")
    assert near is not None and near.test_id == "t1"
    assert index.check("Une phrase totalement différente du test.") is None
    assert index.check("ref") is None
