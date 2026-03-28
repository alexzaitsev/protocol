import json
from datetime import date

from app import mcp
from data.db import fetchrow_rls
from pydantic import BaseModel, Field
from utils.db import build_update, dump_models
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


USER_ERROR = json.dumps({"error": "user not found"})


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
        return USER_ERROR
    return UserProfile(**dict(row)).model_dump_json()


@mcp.tool(name="get_user_profile", description=_tool_desc(PROFILE_DESC))
async def get_user_profile() -> str:
    return await user_profile()


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
        return USER_ERROR
    return UserHealthProfile(**dict(row)).model_dump_json()


@mcp.tool(name="get_user_health_profile", description=_tool_desc(HEALTH_PROFILE_DESC))
async def get_user_health_profile() -> str:
    return await user_health_profile()


@mcp.tool(
    name="update_user_health_profile",
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
) -> str:
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
        return json.dumps({"error": "no fields provided"})
    row = await fetchrow_rls(query, *args)
    if row is None:
        return USER_ERROR
    return UserHealthProfile(**dict(row)).model_dump_json()


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
        return USER_ERROR
    return UserPreferences(**dict(row)).model_dump_json()


@mcp.tool(name="get_user_preferences", description=_tool_desc(PREFERENCES_DESC))
async def get_user_preferences() -> str:
    return await user_preferences()


@mcp.tool(
    name="update_user_preferences",
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
) -> str:
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
        return json.dumps({"error": "no fields provided"})
    row = await fetchrow_rls(query, *args)
    if row is None:
        return USER_ERROR
    return UserPreferences(**dict(row)).model_dump_json()
