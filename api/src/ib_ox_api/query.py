import io

import pandas as pd

from ib_ox_api.models import (
    Filter,
    FilterOp,
    FrequencyQuery,
    FrequencyResult,
    MeansQuery,
    MeansResult,
    UserScope,
)
from ib_ox_api.suppression import suppress_frequency_table, suppress_means_table

# Columns allowed in group_by (categorical)
CATEGORICAL_WHITELIST: set[str] = {
    "school",
    "yearGroup",
    "class",
    "sex",
    "ethnicity",
    "wave",
    "d_city",
    "d_country",
}

# Columns allowed in value_columns for means (numeric)
NUMERIC_WHITELIST: set[str] = {
    "phq9_1",
    "phq9_2",
    "phq9_3",
    "phq9_4",
    "phq9_5",
    "phq9_6",
    "phq9_7",
    "phq9_8",
    "phq9_9",
    "d_age",
}


def _df_to_csv(df: pd.DataFrame) -> str:
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


def validate_frequency_query(query: FrequencyQuery, df_columns: set[str]) -> None:
    """Raise ValueError if the query references disallowed or missing columns."""
    for col in query.group_by:
        if col not in CATEGORICAL_WHITELIST:
            raise ValueError(
                f"Column '{col}' is not allowed in group_by. "
                f"Allowed: {sorted(CATEGORICAL_WHITELIST)}"
            )
        if col not in df_columns:
            raise ValueError(f"Column '{col}' does not exist in the dataset.")

    if query.value_column is not None:
        if query.value_column not in CATEGORICAL_WHITELIST:
            raise ValueError(
                f"value_column '{query.value_column}' is not in the allowed categorical columns. "
                f"Allowed: {sorted(CATEGORICAL_WHITELIST)}"
            )
        if query.value_column not in df_columns:
            raise ValueError(
                f"value_column '{query.value_column}' does not exist in the dataset."
            )

    for f in query.filters:
        if f.column not in df_columns:
            raise ValueError(f"Filter column '{f.column}' does not exist in the dataset.")


def validate_means_query(query: MeansQuery, df_columns: set[str]) -> None:
    """Raise ValueError if the query references disallowed or missing columns."""
    for col in query.group_by:
        if col not in CATEGORICAL_WHITELIST:
            raise ValueError(
                f"Column '{col}' is not allowed in group_by. "
                f"Allowed: {sorted(CATEGORICAL_WHITELIST)}"
            )
        if col not in df_columns:
            raise ValueError(f"Column '{col}' does not exist in the dataset.")

    for col in query.value_columns:
        if col not in NUMERIC_WHITELIST:
            raise ValueError(
                f"Column '{col}' is not allowed in value_columns. "
                f"Allowed: {sorted(NUMERIC_WHITELIST)}"
            )
        if col not in df_columns:
            raise ValueError(f"Column '{col}' does not exist in the dataset.")

    for f in query.filters:
        if f.column not in df_columns:
            raise ValueError(f"Filter column '{f.column}' does not exist in the dataset.")


def apply_user_scope(df: pd.DataFrame, scope: UserScope) -> pd.DataFrame:
    """Apply the user's pre-filters to the DataFrame."""
    for col, allowed_values in scope.filters.items():
        if col not in df.columns:
            continue
        df = df[df[col].astype(str).isin([str(v) for v in allowed_values])]
    return df


def _apply_single_filter(df: pd.DataFrame, f: Filter) -> pd.DataFrame:
    col = f.column
    val = f.value
    op = f.op

    if op == FilterOp.EQ:
        return df[df[col].astype(str) == str(val)]
    if op == FilterOp.NE:
        return df[df[col].astype(str) != str(val)]
    if op == FilterOp.IN:
        values = val if isinstance(val, list) else [val]
        str_values = [str(v) for v in values]
        return df[df[col].astype(str).isin(str_values)]
    if op == FilterOp.GT:
        return df[pd.to_numeric(df[col], errors="coerce") > float(val)]  # type: ignore[arg-type]
    if op == FilterOp.LT:
        return df[pd.to_numeric(df[col], errors="coerce") < float(val)]  # type: ignore[arg-type]
    if op == FilterOp.GTE:
        return df[pd.to_numeric(df[col], errors="coerce") >= float(val)]  # type: ignore[arg-type]
    if op == FilterOp.LTE:
        return df[pd.to_numeric(df[col], errors="coerce") <= float(val)]  # type: ignore[arg-type]
    return df


def apply_filters(df: pd.DataFrame, filters: list[Filter]) -> pd.DataFrame:
    for f in filters:
        df = _apply_single_filter(df, f)
    return df


def execute_frequency_query(
    df: pd.DataFrame,
    query: FrequencyQuery,
    scope: UserScope,
    min_n: int,
) -> FrequencyResult:
    df = apply_user_scope(df, scope)
    df = apply_filters(df, query.filters)

    result_df, suppressions = suppress_frequency_table(
        df=df,
        group_cols=query.group_by,
        value_col=query.value_column,
        min_n=min_n,
    )

    # Convert SuppressionCode values to serialisable form
    serialisable: dict[str, dict[int, str]] = {
        col: {idx: code.value for idx, code in codes.items()}
        for col, codes in suppressions.items()
    }

    return FrequencyResult(
        csv=_df_to_csv(result_df),
        suppressions=serialisable,  # type: ignore[arg-type]
    )


def execute_means_query(
    df: pd.DataFrame,
    query: MeansQuery,
    scope: UserScope,
    min_n: int,
) -> MeansResult:
    df = apply_user_scope(df, scope)
    df = apply_filters(df, query.filters)

    means_df, counts_df, suppressions = suppress_means_table(
        df=df,
        group_cols=query.group_by,
        value_cols=query.value_columns,
        min_n=min_n,
    )

    serialisable: dict[str, dict[int, str]] = {
        col: {idx: code.value for idx, code in codes.items()}
        for col, codes in suppressions.items()
    }

    return MeansResult(
        csv=_df_to_csv(means_df),
        count_csv=_df_to_csv(counts_df),
        suppressions=serialisable,  # type: ignore[arg-type]
    )
