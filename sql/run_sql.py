"""Run sql/fan_out.sql in DuckDB and check it against the pandas outputs.

The SQL file is the thing readers copy, so it stays the single source of
truth: I don't paste its queries in here. I split it into statements, run
them in order, and pick up each result set labelled "-- result: <name>".

Then I assert the SQL reproduces notebooks 02 and 03 exactly: pathway counts
to the pathway, percentages to 1e-9, the same lookup row for row, and the
same repeated and dropped providers. Any mismatch raises, so a scripted run
exits non-zero, the same way the reconciliation gate does.

Run from anywhere, after notebooks 00-03:  python sql/run_sql.py
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from _common import GOLD_DIR, REPO_ROOT, STAR_DIR  # noqa: E402

SQL_FILE = REPO_ROOT / "sql" / "fan_out.sql"
OUT = GOLD_DIR / "03_sql"
TOL = 1e-9


def run_sql_file(path: Path) -> dict[str, pd.DataFrame]:
    """Execute every statement in order; return the labelled result sets."""
    text = path.read_text()
    # A statement ends at a semicolon at the end of a line. The file has no
    # semicolons inside strings, so this is all the parsing I need.
    statements = [s for s in re.split(r";[ \t]*(?:\n|$)", text) if re.sub(r"--[^\n]*", "", s).strip()]
    # The preamble's Parquet paths are relative to the repository root.
    os.chdir(REPO_ROOT)
    con = duckdb.connect()
    results = {}
    for stmt in statements:
        label = re.search(r"^--\s*result:\s*(\w+)", stmt, flags=re.M)
        rel = con.execute(stmt)
        if label:
            results[label.group(1)] = rel.df()
    return results


def assert_frames_match(name: str, sql: pd.DataFrame, pandas_: pd.DataFrame, key: list[str],
                        exact: list[str], close: list[str]) -> None:
    s = sql.set_index(key).sort_index()
    p = pandas_.set_index(key).sort_index()
    assert s.index.equals(p.index), f"{name}: different keys"
    for c in exact:
        assert (s[c].astype(object) == p[c].astype(object)).all(), f"{name}: {c} differs"
    worst = max((s[c].astype(float) - p[c].astype(float)).abs().max() for c in close)
    assert worst < TOL, f"{name}: largest difference {worst:.3g} exceeds {TOL}"
    print(f"  {name:<22} {len(s):>4} rows   exact: {', '.join(key + exact)}   "
          f"to 1e-9: {', '.join(close)}   (largest difference {worst:.1e})")


def main() -> None:
    r = run_sql_file(SQL_FILE)
    OUT.mkdir(parents=True, exist_ok=True)
    for name, df in r.items():
        df.to_csv(OUT / f"{name}.csv", index=False)

    # The pandas outputs, written by notebooks 02 and 03.
    pd_correct = pd.read_csv(GOLD_DIR / "00_reconciliation" / "correct_grain_by_tf.csv")
    pd_fanout = pd.read_csv(GOLD_DIR / "01_fan_out" / "fan_out_by_tf.csv")
    pd_lookup = pd.read_csv(GOLD_DIR / "01_fan_out" / "ref_provider_main_icb.csv")
    dim_provider = pd.read_parquet(STAR_DIR / "dim_provider.parquet")
    fact = pd.read_parquet(STAR_DIR / "fact_incomplete_pathways.parquet")


    print("SQL against pandas:")
    # The lookup must be the same rows as notebook 03's, exactly.
    key = ["provider_code", "icb_code"]
    sql_lookup = r["ref_provider_main_icb"]
    assert sorted(map(tuple, sql_lookup[key].values)) == sorted(map(tuple, pd_lookup[key].values)), \
        "lookup rows differ from notebook 03"
    # share_of_trust must agree too. It didn't at first: notebook 03 grouped on
    # the hub name, and the seven NHS England hubs Y56-Y63 have none, so
    # pandas dropped their 6,334 pathways from each trust's total while SQL's
    # GROUP BY kept them. Notebook 03 now groups on the code alone.
    assert_frames_match("ref_provider_main_icb", sql_lookup, pd_lookup, key=key, exact=[],
                        close=["share_of_trust"])
    assert_frames_match("correct_grain_by_tf", r["correct_grain_by_tf"], pd_correct,
                        key=["tf_code"], exact=["tf_name", "pathways", "within_18_pathways"],
                        close=["pct_within_18", "pct_over_18"])
    assert_frames_match("fan_out_by_tf", r["fan_out_by_tf"], pd_fanout,
                        key=["tf_code"], exact=["tf_name", "pathways_correct", "pathways_fanout"],
                        close=["pct_over_18_correct", "pct_over_18_fanout", "gap_points", "denominator_inflation"])

    rows = r["fan_out_rows"].iloc[0]
    assert (rows.fact_rows, rows.rows_after_join) == (len(fact), 564_592), rows
    print(f"  fan_out_rows           fact rows {rows.fact_rows:,} -> {rows.rows_after_join:,} after the join")

    # The check in (e). The expected answers come from the pandas lookup, not
    # from me: providers with more than one row, and providers with none.
    k = pd_lookup.groupby("provider_code").size()
    pd_repeated = sorted(k[k > 1].index)
    pd_dropped = sorted(set(dim_provider.provider_code) - set(pd_lookup.provider_code))
    uniq = r["check_key_unique"].iloc[0]
    repeated = r["check_repeated_keys"]
    dropped = r["check_dropped_providers"]

    assert (uniq.lookup_rows, uniq.providers) == (len(pd_lookup), pd_lookup.provider_code.nunique())
    assert sorted(repeated.provider_code) == pd_repeated
    assert sorted(dropped.provider_code) == pd_dropped
    # And the figures notebook 03 prints: 83 + 4 = 87 repeated, 2 with none.
    assert len(repeated) == 87 and len(dropped) == 2
    dropped_pathways = int(fact[fact.provider_code.isin(dropped.provider_code)].pathways.sum())
    assert dropped_pathways == 16_483

    print("The check that catches it:")
    print(f"  COUNT(*) {uniq.lookup_rows} vs COUNT(DISTINCT provider_code) {uniq.providers}: key is not unique")
    print(f"  providers with more than one row: {len(repeated)} "
          f"({', '.join(f'{n} with {c}' for c, n in repeated.lookup_rows.value_counts().sort_index().items())})")
    print(f"  providers the inner join drops:   {len(dropped)} "
          f"({', '.join(dropped.provider_code)}; {dropped_pathways:,} pathways)")
    print(f"SQL: PASS. Results written to {OUT.relative_to(REPO_ROOT)}/")


if __name__ == "__main__":
    main()
