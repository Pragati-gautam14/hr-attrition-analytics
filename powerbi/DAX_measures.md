# Power BI model & DAX measures

Load `employees_clean.csv` (one row per employee).

```DAX
Headcount              = COUNTROWS ( employees_clean )
Leavers                = CALCULATE ( [Headcount], employees_clean[attrited] = 1 )
Attrition Rate %       = DIVIDE ( [Leavers], [Headcount] )
Replacement Cost       = 0.5 * CALCULATE ( SUM ( employees_clean[annual_income] ), employees_clean[attrited] = 1 )
Overtime Attrition %   = CALCULATE ( [Attrition Rate %], employees_clean[overtime] = TRUE () )
No-OT Attrition %      = CALCULATE ( [Attrition Rate %], employees_clean[overtime] = FALSE () )
Overtime Uplift (pp)   = [Overtime Attrition %] - [No-OT Attrition %]
First-Year Attrition % = CALCULATE ( [Attrition Rate %], employees_clean[years_at_company] <= 1 )
Avg Engagement         = AVERAGE ( employees_clean[engagement_index] )
Attrition vs Company   = [Attrition Rate %] - CALCULATE ( [Attrition Rate %], ALL ( employees_clean ) )
```

Suggested pages: **Overview** (KPI cards, attrition by department and tenure band), **Drivers** (matrix of job_level × overtime, satisfaction line charts), **Role scorecard** (table with conditional formatting on Attrition vs Company).
