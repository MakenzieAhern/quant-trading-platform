from collections.abc import Mapping
from typing import Any

from app.data.catalog.checksums import canonical_sha256


def reproducibility_hash(values: Mapping[str, Any]) -> str:
    return canonical_sha256(values)
