from datetime import UTC, datetime

from scripts.batch_r5_corporate_action_sources import publication_date


def test_cninfo_local_publication_date_does_not_shift_back_one_day():
    epoch = int(datetime(2014, 2, 25, 16, tzinfo=UTC).timestamp() * 1000)
    assert publication_date(epoch) == "2014-02-26"
