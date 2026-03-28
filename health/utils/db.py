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


def dump_models(items: Sequence[BaseModel]) -> list[dict]:
    return [item.model_dump() for item in items]
