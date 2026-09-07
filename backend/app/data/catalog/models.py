from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.common import UtcDateTime
from app.domain.markets import Exchange


class DatasetPartition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    relative_path: str = Field(min_length=1)
    media_type: str = Field(pattern=r"^(text/csv|application/vnd\.apache\.parquet)$")
    row_count: int = Field(ge=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_relative_path(self) -> "DatasetPartition":
        if self.relative_path.startswith("/") or "\\" in self.relative_path:
            raise ValueError("partition path must be a relative POSIX path")
        if ".." in self.relative_path.split("/"):
            raise ValueError("partition path must not contain parent traversal")
        return self


class DatasetManifest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: str = "1.0"
    dataset_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{2,127}$")
    provider: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    retrieval_timestamp: UtcDateTime
    coverage_start: date
    coverage_end: date
    security_count: int = Field(ge=0)
    symbols: tuple[str, ...]
    exchanges: tuple[Exchange, ...]
    fields: tuple[str, ...]
    adjustment_method: str = Field(min_length=1)
    rule_version: str = Field(min_length=1)
    source_lineage: tuple[str, ...]
    partitions: tuple[DatasetPartition, ...]
    canonical_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    known_limitations: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_manifest(self) -> "DatasetManifest":
        if self.coverage_end < self.coverage_start:
            raise ValueError("coverage_end must not precede coverage_start")
        if self.symbols != tuple(sorted(set(self.symbols))):
            raise ValueError("symbols must be unique and sorted")
        paths = tuple(partition.relative_path for partition in self.partitions)
        if paths != tuple(sorted(set(paths))):
            raise ValueError("partitions must have unique sorted paths")
        return self

    def canonical_payload(self) -> dict[str, object]:
        payload = self.model_dump(mode="json")
        payload.pop("canonical_sha256")
        return payload


class DatasetRevisionError(ValueError):
    pass
