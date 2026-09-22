import base64
import hashlib

import pytest

from scripts.probe_cninfo_distributions import verified_javascript


def test_cninfo_javascript_must_match_installed_wheel_record(tmp_path):
    javascript = tmp_path / "akshare/data/cninfo.js"
    javascript.parent.mkdir(parents=True)
    javascript.write_text("function getResCode1() { return 'fixture'; }")
    digest = base64.urlsafe_b64encode(hashlib.sha256(javascript.read_bytes()).digest()).decode()
    record = tmp_path / "akshare-1.0.dist-info/RECORD"
    record.parent.mkdir()
    record.write_text(f"akshare/data/cninfo.js,sha256={digest.rstrip('=')},\n")

    assert verified_javascript(tmp_path) == javascript
    javascript.write_text("tampered")
    with pytest.raises(ValueError, match="PINNED_CNINFO_JAVASCRIPT_CHANGED"):
        verified_javascript(tmp_path)
