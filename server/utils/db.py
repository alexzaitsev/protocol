# Copyright 2026 Alex Zaitsev
# SPDX-License-Identifier: AGPL-3.0-only

from collections.abc import Sequence

from pydantic import BaseModel


def build_update(table: str, fields: dict[str, object]) -> tuple[str, list[object]]:
    """Build UPDATE ... SET ... RETURNING * from provided (non-None) fields."""
    provided = {k: v for k, v in fields.items() if v is not None}
    if not provided:
        return "", []
    set_parts: list[str] = []
    args: list[object] = []
    for i, (col, val) in enumerate(provided.items(), start=1):
        set_parts.append(f"{col} = ${i}")
        args.append(val)
    return f"UPDATE {table} SET {', '.join(set_parts)} RETURNING *", args


def build_update_where(
    table: str,
    fields: dict[str, object],
    where: dict[str, object],
) -> tuple[str, list[object]]:
    """Build UPDATE ... SET ... WHERE ... RETURNING * from provided (non-None) fields.

    For tables without RLS where an explicit WHERE clause is required.
    """
    provided = {k: v for k, v in fields.items() if v is not None}
    if not provided:
        return "", []
    args: list[object] = []
    set_parts: list[str] = []
    for i, (col, val) in enumerate(provided.items(), start=1):
        set_parts.append(f"{col} = ${i}")
        args.append(val)
    where_parts: list[str] = []
    for col, val in where.items():
        args.append(val)
        where_parts.append(f"{col} = ${len(args)}")
    return (
        f"UPDATE {table} SET {', '.join(set_parts)}"
        f" WHERE {' AND '.join(where_parts)} RETURNING *",
        args,
    )


def dump_models(items: Sequence[BaseModel]) -> list[dict]:
    return [item.model_dump() for item in items]
