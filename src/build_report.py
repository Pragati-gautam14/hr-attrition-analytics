"""README charts (outputs/charts) + interactive dashboard (docs/index.html)."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from viz import C, INK, INK2, plt, save, style_fig, dashboard, table_html

ROOT = Path(__file__).resolve().parents[1]
T = ROOT / "outputs" / "tables"; CH = ROOT / "outputs" / "charts"; CH.mkdir(parents=True, exist_ok=True)
REPO = "https://github.com/Pragati-gautam14/hr-attrition-analytics"
rd = lambda n: pd.read_csv(T / f"{n}.csv")
k = rd("headline_kpis").iloc[0]; dim = rd("attrition_by_dimension"); ol = rd("overtime_level_matrix")
roles = rd("role_scorecard"); segs = rd("flight_risk_segments"); prof = rd("leaver_vs_stayer_profile")
perf = rd("model_performance"); pay = rd("pay_equity_check").iloc[0]
S = json.loads((T / "analysis_summary.json").read_text()); wi = S["whatif_overtime"]
avg = k.attrition_rate_pct
ORD = {"Overtime": ["Yes", "No"], "Tenure band": ["0-1 yr", "2-3 yrs", "4-5 yrs", "6-10 yrs", "10+ yrs"],
       "Income band": ["< 3K", "3K-6K", "6K-10K", "10K+"], "Marital status": ["Single", "Married", "Divorced"],
       "Stock option level": ["0", "1", "2", "3"], "Business travel": ["Travel_Frequently", "Travel_Rarely", "Non-Travel"],
       "Job satisfaction": ["1", "2", "3", "4"], "Environment satisfaction": ["1", "2", "3", "4"], "Work-life balance": ["1", "2", "3", "4"]}
get = lambda d: dim[dim.dimension == d].astype({"value": str}).set_index("value").loc[ORD[d]].reset_index()
money = lambda v: f"${v/1e6:.1f}M" if v >= 1e6 else f"${v/1e3:,.0f}K"

# ---------- PNGs ----------
panels = ["Overtime", "Tenure band", "Income band", "Stock option level"]
titles = ["Overtime", "Years at company", "Monthly income", "Stock option level"]
fig, axes = plt.subplots(1, 4, figsize=(14, 3.8), sharey=True)
for ax, d, t in zip(axes, panels, titles):
    s = get(d); ax.bar(s.value, s.attrition_rate_pct, color=C[0], width=0.6); ax.axhline(avg, color=INK2, ls="--", lw=0.9)
    for i, v in enumerate(s.attrition_rate_pct): ax.text(i, v + 0.8, f"{v:.0f}%", ha="center", fontsize=9, color=INK)
    ax.set_title(t, fontsize=11); ax.tick_params(axis="x", labelsize=8.5); ax.grid(axis="x", visible=False)
axes[0].set_ylabel("Attrition rate %")
fig.suptitle(f"Attrition rate by driver (dashed = {avg}% company average)", x=0.01, ha="left", fontweight="bold", color=INK)
save(fig, CH / "01_attrition_by_driver.png")

pv = ol.pivot(index="job_level", columns="overtime", values="attrition_rate_pct")
fig, ax = plt.subplots(figsize=(9, 3.8)); x = np.arange(len(pv))
ax.bar(x - 0.19, pv["No overtime"], 0.36, color=C[0], label="No overtime")
ax.bar(x + 0.19, pv["Overtime"], 0.36, color=C[1], label="Overtime")
ax.set_xticks(x, [f"Level {i}" for i in pv.index]); ax.legend(frameon=False); ax.grid(axis="x", visible=False)
ax.set_ylabel("Attrition %"); ax.set_title("Overtime triples attrition at entry level (53% vs 16%)")
save(fig, CH / "02_overtime_by_level.png")

r = roles.sort_values("attrition_rate_pct").copy()
r["job_role"] = np.where(r.job_role == "Manager", "Manager (" + r.department.str.replace("Research & Development", "R&D") + ")", r.job_role)
fig, ax = plt.subplots(figsize=(9, 4.5))
ax.barh(r.job_role, r.attrition_rate_pct, color=C[0], height=0.6); ax.axvline(avg, color=INK2, ls="--", lw=0.9)
for i, (v, n) in enumerate(zip(r.attrition_rate_pct, r.headcount)): ax.text(v + 0.5, i, f"{v:.0f}%  (n={n})", va="center", fontsize=8.5, color=INK2)
ax.set_title("Attrition by job role"); ax.grid(axis="y", visible=False); ax.set_xlabel("Attrition %")
save(fig, CH / "03_attrition_by_role.png")

fig, ax = plt.subplots(figsize=(8, 3.8))
for i, d in enumerate(["Job satisfaction", "Environment satisfaction", "Work-life balance"]):
    s = get(d); ax.plot(s.value.astype(int), s.attrition_rate_pct, marker="o", ms=7, lw=2, color=C[i], label=d)
ax.set_xticks([1, 2, 3, 4], ["1 Low", "2", "3", "4 High"]); ax.set_ylabel("Attrition %"); ax.legend(frameon=False)
ax.set_title("Low satisfaction and work-life balance scores mean higher attrition")
save(fig, CH / "04_satisfaction.png")

# ---------- Dashboard ----------
f1 = make_subplots(rows=1, cols=4, shared_yaxes=True, subplot_titles=titles, horizontal_spacing=0.04)
for i, d in enumerate(panels, 1):
    s = get(d)
    f1.add_trace(go.Bar(x=s.value, y=s.attrition_rate_pct, marker_color=C[0], showlegend=False,
                        customdata=np.c_[s.employees, s.leavers, s.est_replacement_cost.fillna(0)],
                        hovertemplate="<b>%{x}</b><br>Attrition %{y}%<br>%{customdata[1]:.0f} of %{customdata[0]} employees<br>Est. replacement cost $%{customdata[2]:,.0f}<extra></extra>"), 1, i)
f1.add_hline(y=avg, line_dash="dash", line_color=INK2, line_width=1); f1.update_yaxes(ticksuffix="%", row=1, col=1)
f1.update_annotations(font_size=12)

f2 = go.Figure([go.Bar(x=[f"Level {i}" for i in pv.index], y=pv[c], name=c, marker_color=col,
                       hovertemplate=f"%{{x}} · {c}<br>Attrition %{{y}}%<extra></extra>")
                for c, col in [("No overtime", C[0]), ("Overtime", C[1])]])
f2.update_layout(barmode="group"); f2.update_yaxes(ticksuffix="%")

f3 = go.Figure(go.Bar(y=r.job_role, x=r.attrition_rate_pct, orientation="h", marker_color=C[0],
                      customdata=np.c_[r.headcount, r.overtime_pct, r.median_monthly_income, r.est_replacement_cost.fillna(0)],
                      hovertemplate="<b>%{y}</b><br>Attrition %{x}%<br>Headcount %{customdata[0]}<br>Overtime %{customdata[1]:.0f}%<br>Median pay $%{customdata[2]:,.0f}/mo<br>Est. cost $%{customdata[3]:,.0f}<extra></extra>"))
f3.add_vline(x=avg, line_dash="dash", line_color=INK2, line_width=1); f3.update_xaxes(ticksuffix="%")

f4 = go.Figure()
for i, d in enumerate(["Job satisfaction", "Environment satisfaction", "Work-life balance"]):
    s = get(d)
    f4.add_trace(go.Scatter(x=["1 Low", "2", "3", "4 High"], y=s.attrition_rate_pct, mode="lines+markers", name=d,
                            line=dict(color=C[i], width=2), marker=dict(size=8),
                            hovertemplate=f"{d} %{{x}}<br>Attrition %{{y}}%<extra></extra>"))
f4.update_yaxes(ticksuffix="%")
for f, h in [(f1, 330), (f2, 320), (f3, 380), (f4, 320)]: style_fig(f, h)
f1.update_layout(margin=dict(l=10, r=10, t=30, b=10))

pretty = lambda s: (s.replace("years_at_company", "Years at company").replace("stock_option_level", "Stock level")
                     .replace("job_level", "Job level").replace("work_life_balance", "Work-life balance")
                     .replace("distance_km", "Distance").replace("NOT overtime", "No overtime").replace("overtime", "Overtime")
                     .replace("age", "Age").replace(" AND ", " · "))
seg_t = segs.assign(rule=segs.rule.map(pretty), leavers=segs.leavers.astype(int))[["rule", "employees", "leavers", "attrition_rate_pct"]]
seg_t.columns = ["Segment (decision-tree rule)", "Employees", "Leavers", "Attrition %"]
rt = roles[["department", "job_role", "headcount", "leavers", "attrition_rate_pct", "overtime_pct", "median_monthly_income", "avg_years_since_promotion"]].copy()
rt["leavers"] = rt.leavers.astype(int); rt["median_monthly_income"] = rt.median_monthly_income.map("{:,.0f}".format)
rt.columns = ["Department", "Role", "Headcount", "Leavers", "Attrition %", "Overtime %", "Median pay / mo", "Yrs since promo"]
top2 = segs.head(2)
top2_emp, top2_lv = int(top2.employees.sum()), int(top2.leavers.sum())
sr = roles.iloc[0]; lt = roles.iloc[1]; t1 = get("Tenure band").iloc[0]; inc = get("Income band")
insights = [
    f"<b>Attrition is {avg}% ({int(k.leavers)} of {int(k.employees):,} employees)</b>, an estimated <b>{money(k.est_replacement_cost)}</b> replacement cost (assuming 50% of annual salary per leaver). First-year attrition is {k.first_year_attrition_pct}%.",
    f"<b>Overtime is the biggest controllable driver:</b> 31% attrition with overtime vs 10% without. At job level 1 it is 53% vs 16%. Bringing overtime employees down to their level's non-overtime rate would avoid ≈{wi['leavers_avoided']:.0f} exits ({wi['pct_of_all_leavers']:.0f}% of leavers, ≈{money(wi['cost_avoided'])}).",
    f"<b>Two flight-risk profiles hold {100*top2_lv/k.leavers:.0f}% of leavers but only {100*top2_emp/k.employees:.0f}% of staff:</b> (1) under 40, under 3 years' tenure, no stock options: {top2.iloc[0].attrition_rate_pct:.0f}% attrition; (2) entry-level staff working overtime: {top2.iloc[1].attrition_rate_pct:.0f}%.",
    f"<b>Role hotspots:</b> Sales Representatives ({sr.attrition_rate_pct:.0f}%) and Laboratory Technicians ({lt.attrition_rate_pct:.0f}%, the most leavers: {int(lt.leavers)}) both have median pay below $3K a month. Employees earning under $3K a month leave at {inc.iloc[0].attrition_rate_pct:.0f}%.",
    "<b>Retention levers:</b> employees with no stock options leave at 24% vs 8–9% with level 1–2 grants. Low work-life balance (score 1) means 31% attrition.",
    f"<b>Pay equity check passed:</b> women's median pay is {abs(pay.raw_median_gap_pct):.0f}% <i>higher</i> than men's. Controlling for job level, experience, department and education, the adjusted gap is {pay.adjusted_gap_pct:.2f}% (p = {pay.p_value:.2f}, not significant).",
]
dashboard("HR Attrition Analytics", "1,470 employees · why people leave, what it costs, and who is at risk",
          [("Headcount", f"{int(k.employees):,}", ""), ("Attrition rate", f"{avg}%", f"{int(k.leavers)} leavers"),
           ("Est. replacement cost", money(k.est_replacement_cost), "at 50% of salary"), ("First-year attrition", f"{k.first_year_attrition_pct}%", "tenure ≤ 1 year"),
           ("Avoidable via overtime", f"≈{wi['leavers_avoided']:.0f}", f"leavers · {money(wi['cost_avoided'])}"), ("Adjusted gender pay gap", f"{pay.adjusted_gap_pct:.2f}%", "not significant")],
          [("Attrition rate by key driver", f"Dashed line = {avg}% company average. Hover for counts and estimated cost.", f1, "full"),
           ("Overtime × job level", "Attrition with and without overtime at each job level", f2, "half"),
           ("Satisfaction scores", "Attrition by survey score (1 = low, 4 = high)", f4, "half"),
           ("Attrition by job role", "Hover for headcount, overtime share and median pay", f3, "full"),
           ("Flight-risk segments", f"Explainable decision-tree rules (test AUC {S['tree_test_auc']:.2f}; full logistic model AUC {S['lr_test_auc']:.2f})", table_html(seg_t, ["Employees", "Leavers", "Attrition %"]), "full"),
           ("Role scorecard for HR business partners", "Ranked by attrition rate", table_html(rt, ["Headcount", "Leavers", "Attrition %", "Overtime %", "Median pay / mo", "Yrs since promo"]), "full")],
          ROOT / "docs" / "index.html", REPO, insights)
print("ok", top2_emp, top2_lv)
