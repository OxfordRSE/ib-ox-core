from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SuppressionCode(str, Enum):
    SMALL_N = "<5"


class FrequencyResult(BaseModel):
    csv: str
    suppressions: dict[str, dict[int, SuppressionCode]]


class MeansResult(BaseModel):
    csv: str
    count_csv: str
    suppressions: dict[str, dict[int, SuppressionCode]]


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserScope(BaseModel):
    """Pre-filter applied to all queries for this user. Dict of column -> list of allowed values."""

    filters: dict[str, list[str]] = Field(default_factory=dict)


class UserCreate(BaseModel):
    username: str
    password: str
    scope: UserScope = Field(default_factory=UserScope)
    is_admin: bool = False


class UserRead(BaseModel):
    id: int
    username: str
    scope: UserScope
    is_active: bool
    is_admin: bool = False
    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    password: Optional[str] = None
    scope: Optional[UserScope] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None


class FilterOp(str, Enum):
    EQ = "eq"
    IN = "in"
    NE = "ne"
    GT = "gt"
    LT = "lt"
    GTE = "gte"
    LTE = "lte"


class Filter(BaseModel):
    column: str
    op: FilterOp
    value: str | int | float | list[str | int | float]


class FrequencyQuery(BaseModel):
    """Query for a frequency table.

    group_by: columns to group by (must be whitelisted categorical columns)
    filters: additional filters to apply
    value_column: the column to count (optional; if omitted, count rows with distinct uid)
    """

    group_by: list[str]
    filters: list[Filter] = Field(default_factory=list)
    value_column: Optional[str] = None


class MeansQuery(BaseModel):
    """Query for a means table.

    group_by: columns to group by
    value_columns: columns to average
    filters: additional filters
    """

    group_by: list[str]
    value_columns: list[str]
    filters: list[Filter] = Field(default_factory=list)
