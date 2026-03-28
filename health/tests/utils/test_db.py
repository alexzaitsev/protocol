from pydantic import BaseModel

from utils.db import build_update, dump_models


class Condition(BaseModel):
    name: str
    status: str
    notes: str | None = None


class FamilyCondition(BaseModel):
    condition: str
    relative: str


class Substance(BaseModel):
    name: str
    frequency: str
    notes: str | None = None


class TestBuildUpdate:
    def test_single_field(self):
        query, args = build_update("person.preferences", {"location": "Toronto"})
        assert query == "UPDATE person.preferences SET location = $1 RETURNING *"
        assert args == ["Toronto"]

    def test_multiple_fields(self):
        query, args = build_update(
            "person.preferences", {"location": "Toronto", "language": "fr"}
        )
        assert query == (
            "UPDATE person.preferences SET location = $1, language = $2 RETURNING *"
        )
        assert args == ["Toronto", "fr"]

    def test_filters_none(self):
        query, args = build_update(
            "person.preferences",
            {"location": "Toronto", "language": None, "units": "imperial"},
        )
        assert "language" not in query
        assert args == ["Toronto", "imperial"]

    def test_all_none_returns_empty(self):
        query, args = build_update(
            "person.preferences", {"location": None, "language": None}
        )
        assert query == ""
        assert args == []


class TestDumpModels:
    def test_conditions(self):
        items = [Condition(name="asthma", status="active", notes=None)]
        result = dump_models(items)
        assert result == [{"name": "asthma", "status": "active", "notes": None}]

    def test_family_conditions(self):
        items = [FamilyCondition(condition="diabetes", relative="father")]
        result = dump_models(items)
        assert result == [{"condition": "diabetes", "relative": "father"}]

    def test_substances(self):
        items = [Substance(name="caffeine", frequency="daily", notes="2 cups")]
        result = dump_models(items)
        assert result == [{"name": "caffeine", "frequency": "daily", "notes": "2 cups"}]

    def test_empty_list(self):
        assert dump_models([]) == []
