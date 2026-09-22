import pytest

from scripts.accept_szse_resumption_scan_reviews import accepted_reviews


def test_visual_review_requires_the_unique_ocr_date():
    digest = "a" * 64
    scan = {
        "documents": [
            {
                "source_sha256": digest,
                "ocr_candidate_dates": ["2011-09-15"],
                "issuer": "000545",
                "title": "股票复牌",
                "url": "u",
                "published_on": "2011-09-15",
                "retrieved_at_utc": "2026-09-19T00:00:00+00:00",
                "ocr_cache_sha256": "b" * 64,
            }
        ]
    }
    review = {
        "source_sha256": digest,
        "resumed_at": "2011-09-15",
        "pdf_page": 1,
        "review_status": "EXACT_DATE_CONFIRMED",
        "execution_open_blocked": False,
    }
    assert accepted_reviews(scan, [review])[0]["resumed_at"] == "2011-09-15"
    with pytest.raises(ValueError, match="UNIQUE_OCR_DATE"):
        accepted_reviews(scan, [{**review, "resumed_at": "2011-09-16"}])
