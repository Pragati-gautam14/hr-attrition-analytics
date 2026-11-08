"""Raw CSV -> DuckDB SQL models -> outputs/tables + powerbi/.  Run: python src/run_pipeline.py"""
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "hr_employee_attrition.csv"
DB = ROOT / "data" / "hr.duckdb"
OUT = ROOT / "outputs" / "tables"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB))
    con.execute(f"CREATE OR REPLACE TABLE raw_hr AS SELECT * FROM read_csv_auto('{RAW.as_posix()}')")
    for f in sorted((ROOT / "sql").glob("*.sql")):
        print("running", f.name)
        con.execute(f.read_text(encoding="utf-8"))
    for t in ["data_quality_log", "headline_kpis", "attrition_by_dimension", "overtime_level_matrix", "role_scorecard"]:
        con.table(t).df().to_csv(OUT / f"{t}.csv", index=False)
    con.sql("PIVOT leaver_profile ON grp USING first(val) GROUP BY metric").df().to_csv(OUT / "leaver_vs_stayer_profile.csv", index=False)
    con.table("employees").df().to_csv(ROOT / "powerbi" / "employees_clean.csv", index=False)
    con.close()


if __name__ == "__main__":
    main()
