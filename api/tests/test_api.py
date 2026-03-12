"""Tests for the IB-Oxford API."""

import io

import pandas as pd
import pytest
from fastapi import status


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


def test_health(client):
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


def test_login_valid(auth_client):
    response = auth_client.post(
        "/auth/login",
        data={"username": "testuser", "password": "testpass"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password(auth_client):
    response = auth_client.post(
        "/auth/login",
        data={"username": "testuser", "password": "wrongpass"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_login_unknown_user(auth_client):
    response = auth_client.post(
        "/auth/login",
        data={"username": "nobody", "password": "pass"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------------------------
# Columns
# ---------------------------------------------------------------------------


def test_get_columns(client):
    response = client.get("/data/columns")
    assert response.status_code == status.HTTP_200_OK
    cols = response.json()
    assert "uid" in cols
    assert "school" in cols
    assert "phq9_1" in cols


# ---------------------------------------------------------------------------
# Frequency query
# ---------------------------------------------------------------------------


def test_frequency_query_basic(client):
    payload = {"group_by": ["school"]}
    response = client.post("/query/frequency", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "csv" in data
    assert "suppressions" in data

    # Parse CSV output
    df = pd.read_csv(io.StringIO(data["csv"]))
    assert "school" in df.columns
    assert "n" in df.columns


def test_frequency_query_with_value_column(client):
    payload = {"group_by": ["school"], "value_column": "sex"}
    response = client.post("/query/frequency", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    df = pd.read_csv(io.StringIO(data["csv"]))
    # Cross-tab columns should include sex categories
    assert "school" in df.columns


def test_frequency_query_with_filter(client):
    payload = {
        "group_by": ["school"],
        "filters": [{"column": "school", "op": "eq", "value": "Alpha"}],
    }
    response = client.post("/query/frequency", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    df = pd.read_csv(io.StringIO(data["csv"]))
    assert set(df["school"].dropna()) == {"Alpha"}


def test_frequency_query_invalid_group_by(client):
    payload = {"group_by": ["hashed_password"]}
    response = client.post("/query/frequency", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_frequency_query_nonexistent_column(client):
    payload = {"group_by": ["school"], "filters": [{"column": "nonexistent", "op": "eq", "value": "x"}]}
    response = client.post("/query/frequency", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ---------------------------------------------------------------------------
# Means query
# ---------------------------------------------------------------------------


def test_means_query_basic(client):
    payload = {"group_by": ["school"], "value_columns": ["phq9_1"]}
    response = client.post("/query/means", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "csv" in data
    assert "count_csv" in data

    df_means = pd.read_csv(io.StringIO(data["csv"]))
    assert "school" in df_means.columns
    assert "phq9_1" in df_means.columns


def test_means_query_invalid_value_column(client):
    payload = {"group_by": ["school"], "value_columns": ["hacked_col"]}
    response = client.post("/query/means", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_means_query_invalid_group_by(client):
    payload = {"group_by": ["uid"], "value_columns": ["phq9_1"]}
    response = client.post("/query/means", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ---------------------------------------------------------------------------
# Suppression logic (unit tests)
# ---------------------------------------------------------------------------


def test_suppression_count_students(sample_df):
    from ib_ox_api.suppression import count_students

    assert count_students(sample_df) == 10


def test_suppression_frequency_below_min_n(tiny_df):
    """With only 2 students, frequency table should suppress with min_n=5."""
    from ib_ox_api.suppression import suppress_frequency_table

    result_df, suppressions = suppress_frequency_table(
        tiny_df, group_cols=["school"], value_col=None, min_n=5
    )
    # All counts should be suppressed (NaN)
    assert result_df["n"].isna().all()
    assert "n" in suppressions


def test_suppression_frequency_above_min_n(sample_df):
    """With 8 students in school Alpha, count should NOT be suppressed."""
    from ib_ox_api.suppression import suppress_frequency_table

    alpha_df = sample_df[sample_df["school"] == "Alpha"]
    result_df, suppressions = suppress_frequency_table(
        alpha_df, group_cols=["wave"], value_col=None, min_n=3
    )
    # Should have values (not all NaN)
    assert not result_df["n"].isna().all()


def test_suppression_means_below_min_n(tiny_df):
    from ib_ox_api.suppression import suppress_means_table

    means_df, counts_df, suppressions = suppress_means_table(
        tiny_df, group_cols=["school"], value_cols=["phq9_1"], min_n=5
    )
    assert means_df["phq9_1"].isna().all()
    assert "phq9_1" in suppressions


def test_suppression_means_above_min_n(sample_df):
    from ib_ox_api.suppression import suppress_means_table

    means_df, counts_df, suppressions = suppress_means_table(
        sample_df, group_cols=["school"], value_cols=["phq9_1"], min_n=3
    )
    # Alpha and Beta each have ≥5 students → no suppression
    assert not means_df["phq9_1"].isna().all()


# ---------------------------------------------------------------------------
# Whitelist enforcement (unit tests)
# ---------------------------------------------------------------------------


def test_whitelist_frequency_rejects_uid():
    from ib_ox_api.models import FrequencyQuery
    from ib_ox_api.query import validate_frequency_query

    query = FrequencyQuery(group_by=["uid"])
    with pytest.raises(ValueError, match="not allowed"):
        validate_frequency_query(query, {"uid", "school", "wave"})


def test_whitelist_means_rejects_nonwhitelisted():
    from ib_ox_api.models import MeansQuery
    from ib_ox_api.query import validate_means_query

    query = MeansQuery(group_by=["school"], value_columns=["uid"])
    with pytest.raises(ValueError, match="not allowed"):
        validate_means_query(query, {"uid", "school", "phq9_1"})


def test_whitelist_means_rejects_missing_column():
    from ib_ox_api.models import MeansQuery
    from ib_ox_api.query import validate_means_query

    query = MeansQuery(group_by=["school"], value_columns=["phq9_1"])
    with pytest.raises(ValueError, match="does not exist"):
        validate_means_query(query, {"school"})  # phq9_1 not in df_columns


def test_user_scope_applied(sample_df):
    from ib_ox_api.models import UserScope
    from ib_ox_api.query import apply_user_scope

    scope = UserScope(filters={"school": ["Alpha"]})
    filtered = apply_user_scope(sample_df, scope)
    assert set(filtered["school"].unique()) == {"Alpha"}
