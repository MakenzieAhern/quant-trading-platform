from datetime import UTC, datetime

from scripts.batch_r5_corporate_action_sources import publication_date


def test_cninfo_local_publication_date_does_not_shift_back_one_day():
    epoch = int(datetime(2014, 2, 25, 16, tzinfo=UTC).timestamp() * 1000)
    assert publication_date(epoch) == "2014-02-26"


def test_batch_reuses_verified_external_pdf_without_download(tmp_path, monkeypatch):
    import json

    from app.data.catalog.checksums import sha256_file
    from scripts import batch_r5_corporate_action_sources as batch

    retained = tmp_path / "retained"
    retained.mkdir()
    source = retained / "notice.pdf"
    source.write_bytes(b"%PDF retained official evidence")
    url = "https://static.cninfo.com.cn/finalpage/2010-01-01/notice.PDF"
    (retained / "notice.pdf.meta.json").write_text(
        json.dumps(
            dict(
                url=url,
                http_status=200,
                sha256=sha256_file(source),
                retrieved_at_utc="2026-09-13T00:00:00Z",
            )
        )
    )
    queue = tmp_path / "queue.json"
    queue.write_text(
        json.dumps(
            [dict(issuer="600000", queue_type="DISTRIBUTION", published_on="2010-01-01", url=url)]
        )
    )
    monkeypatch.setattr(
        batch, "fetch", lambda *args: (_ for _ in ()).throw(AssertionError("must reuse source"))
    )
    report = batch.run(tmp_path / "output", queue=queue, batch="test", source_roots=(retained,))
    assert report["documents"][0]["source_path"] == source.as_posix()
    assert report["failures"] == 0
    assert report == batch.run(
        tmp_path / "output", queue=queue, batch="test", source_roots=(retained,)
    )


def test_batch_opens_circuit_after_consecutive_source_failures(tmp_path, monkeypatch):
    import json

    import pytest

    from scripts import batch_r5_corporate_action_sources as batch

    queue = tmp_path / "queue.json"
    queue.write_text(
        json.dumps(
            [
                {
                    "issuer": "600000",
                    "queue_type": "DISTRIBUTION",
                    "published_on": "2022-01-01",
                    "url": f"https://static.cninfo.com.cn/finalpage/2022-01-01/{i}.PDF",
                }
                for i in range(100)
            ]
        )
    )
    monkeypatch.setattr(batch, "fetch", lambda *args: (_ for _ in ()).throw(OSError("offline")))
    with pytest.raises(RuntimeError, match="ACCESS_CIRCUIT_OPEN"):
        batch.run(tmp_path / "output", queue=queue, batch="test")
