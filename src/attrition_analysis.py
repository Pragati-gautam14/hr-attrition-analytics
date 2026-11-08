"""
Statistical analysis of attrition:
 1. Significance tests for every driver (chi-square / Mann-Whitney U)
 2. Explainable flight-risk rules (decision tree) + logistic regression benchmark
 3. What-if: attrition avoided if overtime employees left at the non-overtime rate of their job level
 4. Pay-equity check: raw vs adjusted gender pay gap (OLS on log income)
Run after run_pipeline.py:  python src/attrition_analysis.py
"""
from pathlib import Path
import json
import duckdb
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.stats import chi2_contingency, mannwhitneyu
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "tables"
SEED = 42
df = duckdb.connect(str(ROOT / "data" / "hr.duckdb"), read_only=True).table("employees").df()
df["overtime"] = df.overtime.astype(int)

# ---------- 1. Significance tests ----------
CAT = ["overtime", "marital_status", "job_role", "job_level", "stock_option_level", "business_travel", "department",
       "env_satisfaction", "job_satisfaction", "work_life_balance", "job_involvement", "education_field", "gender",
       "education_level", "performance_rating"]
NUM = ["monthly_income", "age", "total_working_years", "years_at_company", "years_in_role", "years_with_manager",
       "distance_km", "num_companies_worked", "salary_hike_pct", "years_since_promotion", "trainings_last_year"]
rows = []
for c in CAT:
    ct = pd.crosstab(df[c], df.attrited); chi2, p, _, _ = chi2_contingency(ct)
    rows.append(dict(feature=c, test="chi-square", p_value=p, effect_size=np.sqrt(chi2 / (ct.values.sum() * (min(ct.shape) - 1)))))
for c in NUM:
    a, b = df.loc[df.attrited == 1, c], df.loc[df.attrited == 0, c]
    u, p = mannwhitneyu(a, b)
    rows.append(dict(feature=c, test="Mann-Whitney U", p_value=p, effect_size=1 - 2 * u / (len(a) * len(b)),
                     median_leavers=a.median(), median_stayers=b.median()))
tests = pd.DataFrame(rows)
tests["abs_effect"] = tests.effect_size.abs()
tests = tests.sort_values("abs_effect", ascending=False).drop(columns="abs_effect")
tests["significant_at_5pct"] = tests.p_value < 0.05
tests["effect_size"] = tests.effect_size.round(3)
tests["p_value"] = tests.p_value.map(lambda v: f"{v:.2e}")
tests.to_csv(OUT / "driver_significance_tests.csv", index=False)

# ---------- 2. Explainable rules + benchmark ----------
feats_cat = ["marital_status", "business_travel", "department", "job_role"]
feats_num = ["overtime", "monthly_income", "age", "total_working_years", "years_at_company", "stock_option_level",
             "job_level", "env_satisfaction", "job_satisfaction", "work_life_balance", "job_involvement",
             "distance_km", "num_companies_worked", "years_since_promotion", "years_with_manager"]
X = pd.get_dummies(df[feats_cat + feats_num], columns=feats_cat, drop_first=False, dtype=int)
y = df.attrited
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, stratify=y, random_state=SEED)
cv = StratifiedKFold(5, shuffle=True, random_state=SEED)

tree = DecisionTreeClassifier(max_depth=3, min_samples_leaf=30, class_weight="balanced", random_state=SEED)
tree_cv = cross_val_score(tree, Xtr, ytr, cv=cv, scoring="roc_auc").mean()
tree.fit(Xtr, ytr)
tree_auc = roc_auc_score(yte, tree.predict_proba(Xte)[:, 1])
rules_txt = export_text(tree, feature_names=list(X.columns), decimals=1)
(OUT / "decision_tree_rules.txt").write_text(rules_txt)

# Leaf-level segments described on the full workforce
leaf = tree.apply(X)
seg = (pd.DataFrame({"leaf": leaf, "attrited": y}).groupby("leaf")
         .agg(employees=("attrited", "size"), leavers=("attrited", "sum")))
seg["attrition_rate_pct"] = (100 * seg.leavers / seg.employees).round(1)

def path_rules(t, names):
    tr = t.tree_; out = {}
    def rec(node, conds):
        if tr.children_left[node] == -1:
            out[node] = " AND ".join(conds); return
        f, th = names[tr.feature[node]], tr.threshold[node]
        if set(X[f].unique()) <= {0, 1}:
            l, r = f"NOT {f}", f"{f}"
        else:
            l, r = f"{f} <= {th:.1f}", f"{f} > {th:.1f}"
        rec(tr.children_left[node], conds + [l]); rec(tr.children_right[node], conds + [r])
    rec(0, []); return out
pr = path_rules(tree, list(X.columns))
seg["rule"] = [pr[i] for i in seg.index]
seg = seg.sort_values("attrition_rate_pct", ascending=False).reset_index(drop=True)
seg.to_csv(OUT / "flight_risk_segments.csv", index=False)

cat_cols = feats_cat
lr = Pipeline([("pre", ColumnTransformer([("c", OneHotEncoder(handle_unknown="ignore"), cat_cols),
                                          ("n", StandardScaler(), feats_num)])),
               ("m", LogisticRegression(max_iter=3000, C=0.3, class_weight="balanced"))])
D = df[feats_cat + feats_num]
Dtr, Dte = D.loc[Xtr.index], D.loc[Xte.index]
lr_cv = cross_val_score(lr, Dtr, ytr, cv=cv, scoring="roc_auc").mean()
lr.fit(Dtr, ytr)
lr_auc = roc_auc_score(yte, lr.predict_proba(Dte)[:, 1])
perf = pd.DataFrame([dict(model="Decision tree (depth 3, explainable rules)", cv_auc=round(tree_cv, 3), test_auc=round(tree_auc, 3)),
                     dict(model="Logistic regression (all drivers)", cv_auc=round(lr_cv, 3), test_auc=round(lr_auc, 3))])
perf.to_csv(OUT / "model_performance.csv", index=False)
names = [n.split("__", 1)[1] for n in lr.named_steps["pre"].get_feature_names_out()]
coefs = pd.DataFrame({"feature": names, "coefficient": lr.named_steps["m"].coef_[0]})
coefs["odds_ratio"] = np.exp(coefs.coefficient).round(2); coefs["coefficient"] = coefs.coefficient.round(3)
coefs.sort_values("coefficient", ascending=False).to_csv(OUT / "logistic_odds_ratios.csv", index=False)

# ---------- 3. What-if: overtime ----------
m = df.groupby(["job_level", "overtime"]).agg(n=("attrited", "size"), rate=("attrited", "mean"),
                                               avg_salary=("annual_income", "mean")).unstack("overtime")
ot_n, ot_rate, base_rate = m[("n", 1)], m[("rate", 1)], m[("rate", 0)]
avoided = (ot_n * (ot_rate - base_rate)).clip(lower=0)
avoided_cost = (avoided * m[("avg_salary", 1)] * 0.5)
whatif = dict(leavers_avoided=round(float(avoided.sum()), 0), cost_avoided=round(float(avoided_cost.sum()), 0),
              pct_of_all_leavers=round(100 * float(avoided.sum()) / int(y.sum()), 1))

# ---------- 4. Pay equity ----------
raw_gap = 100 * (1 - df[df.gender == "Female"].monthly_income.median() / df[df.gender == "Male"].monthly_income.median())
ols = smf.ols("np.log(monthly_income) ~ C(gender, Treatment('Male')) + C(job_level) + total_working_years "
              "+ C(department) + C(education_level)", data=df).fit()
key = [k for k in ols.params.index if "gender" in k][0]
adj = dict(raw_median_gap_pct=round(raw_gap, 1),
           adjusted_gap_pct=round(100 * (np.exp(ols.params[key]) - 1), 2),
           p_value=round(float(ols.pvalues[key]), 3), r_squared=round(ols.rsquared, 3))
pd.DataFrame([adj]).to_csv(OUT / "pay_equity_check.csv", index=False)

summary = dict(tree_test_auc=round(tree_auc, 3), lr_test_auc=round(lr_auc, 3), whatif_overtime=whatif, pay_equity=adj)
(OUT / "analysis_summary.json").write_text(json.dumps(summary, indent=2))
print(tests.head(10).to_string(index=False)); print(rules_txt); print(seg.to_string()); print(perf); print(summary)
print(coefs.sort_values('coefficient', ascending=False).head(8).to_string(index=False))
