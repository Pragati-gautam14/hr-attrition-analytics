CELLS = [
("md", """# HR Attrition Analytics — Walkthrough
**Business question:** Why do employees leave, what does it cost, which groups are at highest risk, and is pay fair?

**Data:** IBM HR Analytics Employee Attrition sample — 1,470 employees, 35 attributes.
SQL (DuckDB) builds the clean model and KPI tables; Python (SciPy, scikit-learn, statsmodels) handles tests, segmentation and the pay-equity regression."""),
("code", "import duckdb, pandas as pd, json\npd.set_option('display.width', 180); pd.set_option('display.max_colwidth', 90)\ncon = duckdb.connect('../data/hr.duckdb', read_only=True)\nq = lambda s: con.sql(s).df()\nT = '../outputs/tables/'"),
("md", "## 1. Data quality and KPIs"),
("code", "display(q('SELECT * FROM data_quality_log'))\nq('SELECT * FROM headline_kpis').T"),
("md", "Replacement cost assumes **50% of annual salary per leaver**, the conservative end of the commonly cited 50–200% range."),
("md", "## 2. Attrition drivers"),
("code", "q(\"SELECT * FROM attrition_by_dimension WHERE dimension IN ('Overtime','Tenure band','Income band','Stock option level','Marital status','Business travel')\")"),
("md", "![drivers](../outputs/charts/01_attrition_by_driver.png)"),
("code", "q('SELECT * FROM overtime_level_matrix')"),
("md", "![overtime](../outputs/charts/02_overtime_by_level.png)"),
("code", "q('SELECT * FROM role_scorecard')"),
("md", "![roles](../outputs/charts/03_attrition_by_role.png)\n![sat](../outputs/charts/04_satisfaction.png)"),
("code", "pd.read_csv(T + 'leaver_vs_stayer_profile.csv')"),
("md", "## 3. Which differences are statistically significant?"),
("code", "pd.read_csv(T + 'driver_significance_tests.csv')"),
("md", "## 4. Explainable flight-risk segments\nA shallow decision tree gives rules HR can act on. Logistic regression is the accuracy benchmark."),
("code", "display(pd.read_csv(T + 'model_performance.csv'))\npd.read_csv(T + 'flight_risk_segments.csv')"),
("code", "print(open(T + 'decision_tree_rules.txt').read())"),
("md", "## 5. What-if and pay equity"),
("code", "s = json.loads(open(T + 'analysis_summary.json').read())\ns"),
("md", """## 6. Recommendations
1. **Cap and monitor overtime for job-level-1 staff.** Their attrition is 53% with overtime vs 16% without; this lever alone is worth ≈83 avoided exits.
2. **Early-career retention package.** For employees under 40 in their first 3 years, extend stock-option grants (no-stock attrition is 24% vs 8–9% with level 1–2 grants).
3. **Review pay for Sales Representatives and Laboratory Technicians.** Both have median pay below $3K a month and attrition of 40% and 24%.
4. **Act on survey signals.** Employees who score work-life balance or environment satisfaction at 1 are early warnings and should get a manager follow-up.
5. **Pay equity:** no significant adjusted gender gap. Keep running this check every review cycle."""),
]
