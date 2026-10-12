from app.core.normalization import compute_entity_id, merge_entity
from app.models.universal_entity import UniversalEntity
from app.schemas.universal_entity import (
    Metadata,
    Properties,
    Source,
    UniversalEntityCreate,
)


def test_entity_id_is_deterministic():
    assert compute_entity_id("ip", ["1.2.3.4"]) == compute_entity_id("ip", ["1.2.3.4"])


def test_entity_id_normalizes_case_and_whitespace():
    a = compute_entity_id("domain", [" Example.com "])
    b = compute_entity_id("domain", ["example.com"])
    assert a == b


def test_entity_id_differs_by_type_and_key():
    assert compute_entity_id("ip", ["1.2.3.4"]) != compute_entity_id("domain", ["1.2.3.4"])
    assert compute_entity_id("ip", ["1.2.3.4"]) != compute_entity_id("ip", ["1.2.3.5"])


def test_entity_id_has_sha256_length():
    entity_id = compute_entity_id("person", ["Jane Doe", "1990-01-01"])
    assert len(entity_id) == 64


def test_merge_entity_updates_company_field():
    existing = UniversalEntity(
        workspace_id=1,
        entity_type="company",
        entity_id="x",
        entity_name="Old",
        properties={"company": {"edrpou": None, "address": ""}, "metadata": {"sources": []}},
        relations=[],
        raw_data={},
    )
    incoming = UniversalEntityCreate(
        entity_type="company",
        entity_id="x",
        entity_name="New",
        properties=Properties(
            company={"edrpou": "12345678", "address": "Київ"},
            metadata=Metadata(sources=[Source(name="company_profile")]),
        ),
        raw_data={"company_profile": {}},
    )
    merge_entity(existing, incoming)
    assert existing.properties["company"]["edrpou"] == "12345678"
    assert existing.properties["company"]["address"] == "Київ"
