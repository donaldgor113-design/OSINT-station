from pydantic import BaseModel, ConfigDict, Field

ENTITY_TYPES = {
    "location",
    "person",
    "company",
    "ip",
    "domain",
    "phone",
    "document",
    "media",
}


class GeoProperty(BaseModel):
    coordinates: list[float] = Field(default_factory=lambda: [0.0, 0.0])
    city: str = ""
    country: str = ""
    address: str = ""


class TemporalProperty(BaseModel):
    created: str | None = None
    updated: str | None = None
    observed_at: str | None = None


class DigitalFootprint(BaseModel):
    emails: list[str] = Field(default_factory=list)
    phones: list[str] = Field(default_factory=list)
    social_accounts: list[str] = Field(default_factory=list)
    ip_addresses: list[str] = Field(default_factory=list)


class Source(BaseModel):
    name: str
    confidence: float = 0.5
    last_verified: str | None = None


class Metadata(BaseModel):
    sources: list[Source] = Field(default_factory=list)
    completeness: float = 0.0
    risk_level: str = "low"  # low | medium | high


class Properties(BaseModel):
    model_config = ConfigDict(extra="allow")

    geo: GeoProperty | None = None
    temporal: TemporalProperty | None = None
    digital_footprint: DigitalFootprint | None = None
    metadata: Metadata | None = None
    domain: dict | None = None
    company: dict | None = None
    document: dict | None = None


class Relation(BaseModel):
    target_id: str
    type: str
    confidence: float = 0.0


class UniversalEntityCreate(BaseModel):
    entity_type: str
    entity_name: str
    entity_id: str | None = None  # computed from key fields when omitted
    properties: Properties | None = None
    relations: list[Relation] = Field(default_factory=list)
    raw_data: dict = Field(default_factory=dict)


class UniversalEntityRead(UniversalEntityCreate):
    id: int


class SearchRequest(BaseModel):
    query: str
    source: str = "auto"
    workspace_id: int
    force_tier: str | None = None
    min_confidence: float = 0.6


class SearchResponse(BaseModel):
    query: str
    source: str
    results: list[UniversalEntityRead]


class TierInfo(BaseModel):
    """Зведення по одному рівні каскаду."""

    name: str
    entities_count: int = 0
    confidence: float = 0.0
    duration_ms: int = 0
    skipped: bool = False
    skip_reason: str | None = None
    error: str | None = None


class CascadeSearchResponse(BaseModel):
    """Відповідь каскадного пошуку (зберігає `results` для сумісності)."""

    query: str
    source: str
    query_type: str
    intent: str
    confidence: float
    results: list[UniversalEntityRead]
    tiers: list[TierInfo] = Field(default_factory=list)
    stopped_at: str | None = None


class AnalyzeRequest(BaseModel):
    workspace_id: int
    entity_ids: list[str] = Field(default_factory=list)
    provider: str = "mock"


class AnalyzeResponse(BaseModel):
    summary: str
    cross_check: str
    anomalies: list[str] = Field(default_factory=list)
