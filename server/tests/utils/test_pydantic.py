# Copyright 2026 Alex Zaitsev
# SPDX-License-Identifier: AGPL-3.0-only

import json

from pydantic import BaseModel, Field

from utils.pydantic import (
    _model_shape,
    _type_name,
    _unwrap_optional,
    deref_schema,
    describe_schema,
)

# ── Test models ──────────────────────────────────────────────────────


class Simple(BaseModel):
    name: str
    age: int


class WithOptional(BaseModel):
    title: str
    notes: str | None = None


class WithDescription(BaseModel):
    value: int = Field(description="some desc")


class Tag(BaseModel):
    name: str


class Nested(BaseModel):
    tag: Tag
    tags: list[Tag]


class WithScalarList(BaseModel):
    names: list[str]


# ── describe_schema ──────────────────────────────────────────────────


class TestDescribeSchema:
    def test_basic_fields(self):
        result = describe_schema(Simple)
        assert result.startswith("Fields:")
        assert "- name: str" in result
        assert "- age: int" in result

    def test_optional_field(self):
        result = describe_schema(WithOptional)
        assert "- notes: optional str" in result

    def test_field_description(self):
        result = describe_schema(WithDescription)
        assert "— some desc" in result

    def test_nested_model(self):
        result = describe_schema(Nested)
        assert "- tag: {name}" in result

    def test_list_of_models(self):
        result = describe_schema(Nested)
        assert "- tags: [{name}]" in result

    def test_list_of_scalars(self):
        result = describe_schema(WithScalarList)
        assert "- names: list of strings" in result


# ── deref_schema ─────────────────────────────────────────────────────


class TestDerefSchema:
    def test_simple_flat_schema(self):
        result = json.loads(deref_schema(Simple))
        props = result["properties"]
        assert "name" in props
        assert "age" in props
        assert "$ref" not in json.dumps(result)

    def test_nested_refs_resolved(self):
        raw = deref_schema(Nested)
        assert "$ref" not in raw
        result = json.loads(raw)
        tag_props = result["properties"]["tag"]["properties"]
        assert "name" in tag_props

    def test_no_title_keys(self):
        result = json.loads(deref_schema(Simple))

        def _find_title(node):
            if isinstance(node, dict):
                assert "title" not in node, f"found 'title' key in {node}"
                for v in node.values():
                    _find_title(v)
            elif isinstance(node, list):
                for item in node:
                    _find_title(item)

        _find_title(result)


# ── internal helpers ─────────────────────────────────────────────────


class TestUnwrapOptional:
    def test_optional(self):
        is_opt, inner = _unwrap_optional(str | None)
        assert is_opt is True
        assert inner is str

    def test_non_optional(self):
        is_opt, inner = _unwrap_optional(str)
        assert is_opt is False
        assert inner is str


class TestTypeName:
    def test_singular(self):
        assert _type_name(str) == "str"

    def test_plural_known(self):
        assert _type_name(str, plural=True) == "strings"

    def test_plural_unknown(self):
        assert _type_name(Tag, plural=True) == "Tags"


class TestModelShape:
    def test_simple_shape(self):
        assert _model_shape(Simple) == "{name, age}"

    def test_optional_marker(self):
        shape = _model_shape(WithOptional)
        assert "notes?" in shape
        assert "title" in shape
        assert "title?" not in shape
