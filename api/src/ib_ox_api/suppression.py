import pandas as pd

from ib_ox_api.models import SuppressionCode


def count_students(df: pd.DataFrame) -> int:
    """Count the number of distinct students (uid) in a DataFrame."""
    if "uid" not in df.columns or df.empty:
        return 0
    return int(df["uid"].nunique())


def suppress_frequency_table(
    df: pd.DataFrame,
    group_cols: list[str],
    value_col: str | None,
    min_n: int,
) -> tuple[pd.DataFrame, dict[str, dict[int, SuppressionCode]]]:
    """Compute a frequency table and suppress cells where distinct student count < min_n.

    If value_col is None, count distinct uids per group.
    If value_col is provided, produce a cross-tab of group_cols × value_col values
    where each cell contains the count of distinct students.

    Returns (result_df, suppressions) where suppressions maps
    column_name -> {row_index: SuppressionCode}.
    """
    suppressions: dict[str, dict[int, SuppressionCode]] = {}

    if value_col is None:
        # Simple count of distinct students per group combination
        agg = (
            df.groupby(group_cols)["uid"]
            .nunique()
            .reset_index()
            .rename(columns={"uid": "n"})
        )
        for idx, row in agg.iterrows():
            if row["n"] < min_n:
                agg.at[idx, "n"] = float("nan")
                suppressions.setdefault("n", {})[int(idx)] = SuppressionCode.SMALL_N
        return agg, suppressions

    # Cross-tab: group_cols × value_col, cells = distinct student count
    pivot_groups = group_cols + [value_col]
    uid_counts = (
        df.groupby(pivot_groups)["uid"]
        .nunique()
        .reset_index()
        .rename(columns={"uid": "n"})
    )

    # Pivot so value_col becomes columns
    if len(group_cols) == 1:
        index_col = group_cols[0]
    else:
        # Create a composite index column for pivot
        uid_counts["_group"] = uid_counts[group_cols].astype(str).agg(" | ".join, axis=1)
        index_col = "_group"

    result = uid_counts.pivot_table(
        index=index_col,
        columns=value_col,
        values="n",
        aggfunc="sum",
    ).reset_index()
    result.columns.name = None

    # Suppress cells
    value_categories = [c for c in result.columns if c != index_col]
    for col in value_categories:
        col_suppressions: dict[int, SuppressionCode] = {}
        for idx, val in result[col].items():
            if pd.isna(val) or val < min_n:
                result.at[idx, col] = float("nan")
                col_suppressions[int(idx)] = SuppressionCode.SMALL_N
        if col_suppressions:
            suppressions[str(col)] = col_suppressions

    return result, suppressions


def suppress_means_table(
    df: pd.DataFrame,
    group_cols: list[str],
    value_cols: list[str],
    min_n: int,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, dict[int, SuppressionCode]]]:
    """Compute means and counts per group, suppressing cells where student count < min_n.

    Returns (means_df, counts_df, suppressions).
    """
    suppressions: dict[str, dict[int, SuppressionCode]] = {}

    # Student counts per group per value column
    # A student may have answered different subsets of questions, so count per value_col separately.
    groups = df.groupby(group_cols)

    means_parts: dict[str, pd.Series] = {}
    counts_parts: dict[str, pd.Series] = {}

    for col in value_cols:
        sub = df.dropna(subset=[col])
        g = sub.groupby(group_cols)
        counts_parts[col] = g["uid"].nunique()
        means_parts[col] = g[col].mean()

    # Build DataFrames
    means_df = pd.DataFrame(means_parts)
    counts_df = pd.DataFrame(counts_parts)

    # Reset index so group_cols become regular columns
    means_df = means_df.reset_index()
    counts_df = counts_df.reset_index()

    # Suppress cells where count < min_n
    for col in value_cols:
        col_suppressions: dict[int, SuppressionCode] = {}
        for idx in counts_df.index:
            n = counts_df.at[idx, col]
            if pd.isna(n) or n < min_n:
                means_df.at[idx, col] = float("nan")
                counts_df.at[idx, col] = float("nan")
                col_suppressions[int(idx)] = SuppressionCode.SMALL_N
        if col_suppressions:
            suppressions[col] = col_suppressions

    return means_df, counts_df, suppressions
