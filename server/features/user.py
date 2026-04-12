# Copyright 2026 Alex Zaitsev
# SPDX-License-Identifier: AGPL-3.0-only

from datetime import date

from app import mcp
from data.db import fetchrow_rls
from fastmcp.exceptions import ToolError
from pydantic import BaseModel, Field
from utils.db import build_update, dump_models
from utils.mcp_annotations import READ, WRITE
from utils.pydantic import describe_schema


class UserProfile(BaseModel):
    name: str = Field(alias="display_name", description="user's name")
    sex: str = Field(description="biological sex")
    date_of_birth: date = Field(description="DOB in YYYY-MM-DD format")


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


class UserHealthProfile(BaseModel):
    conditions: list[Condition] = Field(description="medical conditions")
    family_history: list[FamilyCondition] = Field(description="hereditary risks")
    substances: list[Substance] = Field(
        description="consumed substances: caffeine, alcohol, etc."
    )
    diet_notes: str | None = Field(description="eating habits and dietary patterns")
    activity_notes: str | None = Field(
        description="physical activity and exercise routine"
    )
    safety_checks: list[str] = Field(
        description="topics to verify before making health recommendations"
    )
    methodology_notes: str | None = Field(
        description="preferred health philosophy or framework AI should follow"
    )
    health_priorities: list[str] = Field(description="ranked health goals for the user")


class UserPreferences(BaseModel):
    location: str | None = Field(description="city, region, country")
    occupation: str | None = Field(description="user's job or profession")
    language: str = Field(description="language preference (ISO 639-1 code)")
    units: str = Field(description="measurement system (metric or imperial)")
    currency: str = Field(description="currency code (e.g. CAD)")
    date_format: str = Field(description="preferred date display format")
    communication: str | None = Field(description="communication style preferences")


class UserContext(BaseModel):
    profile: UserProfile
    health_profile: UserHealthProfile
    preferences: UserPreferences


def _tool_desc(desc: str) -> str:
    return f"Get {desc[0].lower()}{desc[1:]}"


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

PROFILE_DESC = (
    f"Basic demographics of the current user.\n{describe_schema(UserProfile)}"
)


@mcp.resource(
    uri="user://profile",
    name="User Basic Demographics",
    description=PROFILE_DESC,
    mime_type="application/json",
)
async def user_profile() -> str:
    row = await fetchrow_rls("SELECT * FROM person.users")
    if row is None:
        return '{"error": "user not found"}'
    return UserProfile(**dict(row)).model_dump_json()


@mcp.tool(
    name="get_user_profile",
    title="Get User Profile",
    annotations=READ,
    description=_tool_desc(PROFILE_DESC),
)
async def get_user_profile() -> UserProfile:
    row = await fetchrow_rls("SELECT * FROM person.users")
    if row is None:
        raise ToolError("user not found")
    return UserProfile(**dict(row))


# ---------------------------------------------------------------------------
# Health profile
# ---------------------------------------------------------------------------

HEALTH_PROFILE_DESC = (
    f"Comprehensive health profile of the current user.\n"
    f"{describe_schema(UserHealthProfile)}"
)


@mcp.resource(
    uri="user://health-profile",
    name="User Health Profile",
    description=HEALTH_PROFILE_DESC,
    mime_type="application/json",
)
async def user_health_profile() -> str:
    row = await fetchrow_rls("SELECT * FROM person.health_profiles")
    if row is None:
        return '{"error": "user not found"}'
    return UserHealthProfile(**dict(row)).model_dump_json()


@mcp.tool(
    name="get_user_health_profile",
    title="Get User Health Profile",
    annotations=READ,
    description=_tool_desc(HEALTH_PROFILE_DESC),
)
async def get_user_health_profile() -> UserHealthProfile:
    row = await fetchrow_rls("SELECT * FROM person.health_profiles")
    if row is None:
        raise ToolError("user not found")
    return UserHealthProfile(**dict(row))


@mcp.tool(
    name="update_user_health_profile",
    title="Update User Health Profile",
    annotations=WRITE,
    description=(
        "Update the current user's health profile. "
        "Only provided fields are changed; omitted fields remain unchanged.\n"
        f"{describe_schema(UserHealthProfile)}"
    ),
)
async def update_user_health_profile(
    conditions: list[Condition] | None = None,
    family_history: list[FamilyCondition] | None = None,
    substances: list[Substance] | None = None,
    diet_notes: str | None = None,
    activity_notes: str | None = None,
    safety_checks: list[str] | None = None,
    methodology_notes: str | None = None,
    health_priorities: list[str] | None = None,
) -> UserHealthProfile:
    fields: dict[str, object] = {
        "conditions": dump_models(conditions) if conditions is not None else None,
        "family_history": (
            dump_models(family_history) if family_history is not None else None
        ),
        "substances": dump_models(substances) if substances is not None else None,
        "diet_notes": diet_notes,
        "activity_notes": activity_notes,
        "safety_checks": safety_checks,
        "methodology_notes": methodology_notes,
        "health_priorities": health_priorities,
    }
    query, args = build_update("person.health_profiles", fields)
    if not query:
        raise ToolError("no fields provided")
    row = await fetchrow_rls(query, *args)
    if row is None:
        raise ToolError("user not found")
    return UserHealthProfile(**dict(row))


# ---------------------------------------------------------------------------
# Preferences
# ---------------------------------------------------------------------------

PREFERENCES_DESC = (
    f"Preferences and settings of the current user.\n{describe_schema(UserPreferences)}"
)


@mcp.resource(
    uri="user://preferences",
    name="User Preferences",
    description=PREFERENCES_DESC,
    mime_type="application/json",
)
async def user_preferences() -> str:
    row = await fetchrow_rls("SELECT * FROM person.preferences")
    if row is None:
        return '{"error": "user not found"}'
    return UserPreferences(**dict(row)).model_dump_json()


@mcp.tool(
    name="get_user_preferences",
    title="Get User Preferences",
    annotations=READ,
    description=_tool_desc(PREFERENCES_DESC),
)
async def get_user_preferences() -> UserPreferences:
    row = await fetchrow_rls("SELECT * FROM person.preferences")
    if row is None:
        raise ToolError("user not found")
    return UserPreferences(**dict(row))


@mcp.tool(
    name="update_user_preferences",
    title="Update User Preferences",
    annotations=WRITE,
    description=(
        "Update the current user's preferences. "
        "Only provided fields are changed; omitted fields remain unchanged.\n"
        f"{describe_schema(UserPreferences)}"
    ),
)
async def update_user_preferences(
    location: str | None = None,
    occupation: str | None = None,
    language: str | None = None,
    units: str | None = None,
    currency: str | None = None,
    date_format: str | None = None,
    communication: str | None = None,
) -> UserPreferences:
    fields: dict[str, object] = {
        "location": location,
        "occupation": occupation,
        "language": language,
        "units": units,
        "currency": currency,
        "date_format": date_format,
        "communication": communication,
    }
    query, args = build_update("person.preferences", fields)
    if not query:
        raise ToolError("no fields provided")
    row = await fetchrow_rls(query, *args)
    if row is None:
        raise ToolError("user not found")
    return UserPreferences(**dict(row))


# ---------------------------------------------------------------------------
# Full context
# ---------------------------------------------------------------------------

CONTEXT_DESC = (
    "Full user context: demographics, health profile, and preferences in one call.\n"
    f"{describe_schema(UserContext)}"
)

_CONTEXT_QUERY = """
SELECT
  u.display_name,
  u.sex,
  u.date_of_birth,
  h.conditions,
  h.family_history,
  h.substances,
  h.diet_notes,
  h.activity_notes,
  h.safety_checks,
  h.methodology_notes,
  h.health_priorities,
  p.location,
  p.occupation,
  p.language,
  p.units,
  p.currency,
  p.date_format,
  p.communication
FROM
  person.users u
  INNER JOIN person.health_profiles h ON h.user_id = u.id
  INNER JOIN person.preferences p ON p.user_id = u.id
"""


@mcp.tool(
    name="get_user_context",
    title="Get Full User Context",
    annotations=READ,
    description=_tool_desc(CONTEXT_DESC),
)
async def get_user_context() -> UserContext:
    row = await fetchrow_rls(_CONTEXT_QUERY)
    if row is None:
        raise ToolError("user not found")
    r = dict(row)
    context = UserContext(
        profile=UserProfile(
            **{k: r[k] for k in ("display_name", "sex", "date_of_birth")}
        ),
        health_profile=UserHealthProfile(
            **{
                k: r[k]
                for k in (
                    "conditions",
                    "family_history",
                    "substances",
                    "diet_notes",
                    "activity_notes",
                    "safety_checks",
                    "methodology_notes",
                    "health_priorities",
                )
            }
        ),
        preferences=UserPreferences(
            **{
                k: r[k]
                for k in (
                    "location",
                    "occupation",
                    "language",
                    "units",
                    "currency",
                    "date_format",
                    "communication",
                )
            }
        ),
    )
    return context
