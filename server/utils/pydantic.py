# Copyright 2026 Alex Zaitsev
# SPDX-License-Identifier: AGPL-3.0-only

import json
import types
from typing import Any, Union, get_args, get_origin

from pydantic import BaseModel


def describe_schema(model: type[BaseModel]) -> str:
    """One-line-per-field schema description for LLM resource descriptions."""
    lines = ["Fields:"]
    _append_fields(lines, model, indent=1)
    return "\n".join(lines)


def _append_fields(lines: list[str], model: type[BaseModel], indent: int) -> None:
    """Recursively append field descriptions with indentation."""
    prefix = "  " * (indent - 1)
    for name, field_info in model.model_fields.items():
        annotation = field_info.annotation
        optional, annotation = _unwrap_optional(annotation)
        type_str = _format_field(annotation, optional)
        desc = f" — {field_info.description}" if field_info.description else ""
        lines.append(f"{prefix}- {name}: {type_str}{desc}")
        nested = _nested_model(annotation)
        if nested is not None:
            _append_fields(lines, nested, indent + 1)


def _unwrap_optional(annotation: Any) -> tuple[bool, Any]:
    """If annotation is T | None, return (True, T). Otherwise (False, annotation)."""
    if get_origin(annotation) is Union:
        args = [a for a in get_args(annotation) if a is not types.NoneType]
        if len(args) == 1:
            return True, args[0]
    return False, annotation


def _format_field(annotation: Any, optional: bool) -> str:
    origin = get_origin(annotation)
    prefix = "optional " if optional else ""

    if origin is list:
        (inner,) = get_args(annotation)
        return f"{prefix}list of {_type_name(inner, plural=True)}"

    return f"{prefix}{_type_name(annotation)}"


def _nested_model(annotation: Any) -> type[BaseModel] | None:
    """Extract BaseModel subclass from annotation, if present."""
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return annotation
    if get_origin(annotation) is list:
        (inner,) = get_args(annotation)
        if isinstance(inner, type) and issubclass(inner, BaseModel):
            return inner
    return None


_PLURAL = {
    "str": "strings",
    "int": "ints",
    "float": "floats",
    "bool": "bools",
    "date": "dates",
}


def _type_name(t: Any, *, plural: bool = False) -> str:
    if isinstance(t, type):
        name = t.__name__
        if plural:
            return _PLURAL.get(name, f"{name}s")
        return name
    return str(t)


def deref_schema(model: type[BaseModel]) -> str:
    """Inline $ref pointers and strip noise so LLMs see a flat schema."""
    schema = model.model_json_schema()
    defs = schema.pop("$defs", {})

    def _resolve(node: Any) -> Any:
        if isinstance(node, dict):
            if "$ref" in node:
                ref_name = node["$ref"].rsplit("/", 1)[-1]
                return _resolve(defs[ref_name])
            return {k: _resolve(v) for k, v in node.items() if k != "title"}
        if isinstance(node, list):
            return [_resolve(item) for item in node]
        return node

    return json.dumps(_resolve(schema))
