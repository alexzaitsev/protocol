import json
from datetime import date

from app import mcp
from data.db import fetchrow_rls
from pydantic import BaseModel, Field
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
    units: str = Field(description="measurement system (e.g. metric)")
    currency: str | None = Field(description="currency code (e.g. CAD)")
    date_format: str = Field(description="preferred date display format")
    communication: str | None = Field(description="communication style preferences")


USER_ERROR = json.dumps({"error": "user not found"})


@mcp.resource(
    uri="user://profile",
    name="User Basic Demographics",
    description=(
        f"Basic demographics of the current user.\n{describe_schema(UserProfile)}"
    ),
    mime_type="application/json",
)
async def user_profile() -> str:
    row = await fetchrow_rls("SELECT * FROM person.users")
    if row is None:
        return USER_ERROR
    return UserProfile(**dict(row)).model_dump_json()


@mcp.resource(
    uri="user://health-profile",
    name="User Health Profile",
    description=(
        "Comprehensive health profile of the current user.\n"
        f"{describe_schema(UserHealthProfile)}"
    ),
    mime_type="application/json",
)
async def user_health_profile() -> str:
    row = await fetchrow_rls("SELECT * FROM person.health_profiles")
    if row is None:
        return USER_ERROR
    return UserHealthProfile(**dict(row)).model_dump_json()


@mcp.resource(
    uri="user://preferences",
    name="User Preferences",
    description=(
        "Preferences and settings of the current user.\n"
        f"{describe_schema(UserPreferences)}"
    ),
    mime_type="application/json",
)
async def user_preferences() -> str:
    row = await fetchrow_rls("SELECT * FROM person.preferences")
    if row is None:
        return USER_ERROR
    return UserPreferences(**dict(row)).model_dump_json()
