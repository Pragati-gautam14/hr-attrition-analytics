-- =============================================================
-- 02 · ATTRITION KPIs, DRIVERS & COST
-- Replacement-cost assumption: 50% of annual salary per leaver
-- (conservative end of the commonly cited 50-200% range - edit the 0.5 factor to change)
-- =============================================================


CREATE OR REPLACE TABLE headline_kpis AS
SELECT COUNT(*) AS employees, SUM(attrited) AS leavers,
       ROUND(100.0 * AVG(attrited), 1) AS attrition_rate_pct,
       ROUND(0.5 * SUM(annual_income) FILTER (WHERE attrited = 1), 0) AS est_replacement_cost,
       ROUND(AVG(monthly_income) FILTER (WHERE attrited = 1), 0) AS avg_income_leavers,
       ROUND(AVG(monthly_income) FILTER (WHERE attrited = 0), 0) AS avg_income_stayers,
       ROUND(AVG(years_at_company) FILTER (WHERE attrited = 1), 1) AS avg_tenure_leavers,
       ROUND(AVG(years_at_company) FILTER (WHERE attrited = 0), 1) AS avg_tenure_stayers,
       ROUND(100.0 * AVG(attrited) FILTER (WHERE years_at_company <= 1), 1) AS first_year_attrition_pct,
       ROUND(AVG(engagement_index), 2) AS avg_engagement
FROM employees;

CREATE OR REPLACE TABLE attrition_by_dimension AS
WITH d AS (
    SELECT 'Department' AS dimension, department AS value, attrited, annual_income FROM employees
    UNION ALL SELECT 'Job role', job_role, attrited, annual_income FROM employees
    UNION ALL SELECT 'Overtime', CASE WHEN overtime THEN 'Yes' ELSE 'No' END, attrited, annual_income FROM employees
    UNION ALL SELECT 'Job level', job_level::VARCHAR, attrited, annual_income FROM employees
    UNION ALL SELECT 'Income band', income_band, attrited, annual_income FROM employees
    UNION ALL SELECT 'Tenure band', tenure_band, attrited, annual_income FROM employees
    UNION ALL SELECT 'Age band', age_band, attrited, annual_income FROM employees
    UNION ALL SELECT 'Marital status', marital_status, attrited, annual_income FROM employees
    UNION ALL SELECT 'Business travel', business_travel, attrited, annual_income FROM employees
    UNION ALL SELECT 'Stock option level', stock_option_level::VARCHAR, attrited, annual_income FROM employees
    UNION ALL SELECT 'Job satisfaction', job_satisfaction::VARCHAR, attrited, annual_income FROM employees
    UNION ALL SELECT 'Environment satisfaction', env_satisfaction::VARCHAR, attrited, annual_income FROM employees
    UNION ALL SELECT 'Work-life balance', work_life_balance::VARCHAR, attrited, annual_income FROM employees
    UNION ALL SELECT 'Gender', gender, attrited, annual_income FROM employees
)
SELECT dimension, value, COUNT(*) AS employees, SUM(attrited) AS leavers,
       ROUND(100.0 * AVG(attrited), 1) AS attrition_rate_pct,
       ROUND(100.0 * SUM(attrited) / SUM(SUM(attrited)) OVER (PARTITION BY dimension), 1) AS share_of_leavers_pct,
       ROUND(0.5 * SUM(annual_income) FILTER (WHERE attrited = 1), 0) AS est_replacement_cost
FROM d GROUP BY dimension, value
ORDER BY dimension, attrition_rate_pct DESC;

-- Overtime × job level: where burnout bites hardest
CREATE OR REPLACE TABLE overtime_level_matrix AS
SELECT job_level, CASE WHEN overtime THEN 'Overtime' ELSE 'No overtime' END AS overtime,
       COUNT(*) AS employees, ROUND(100.0 * AVG(attrited), 1) AS attrition_rate_pct
FROM employees GROUP BY ALL ORDER BY job_level, overtime;

-- Role-level scorecard for HR business partners
CREATE OR REPLACE TABLE role_scorecard AS
SELECT department, job_role, COUNT(*) AS headcount, SUM(attrited) AS leavers,
       ROUND(100.0 * AVG(attrited), 1) AS attrition_rate_pct,
       ROUND(100.0 * AVG(overtime::INT), 0) AS overtime_pct,
       ROUND(MEDIAN(monthly_income), 0) AS median_monthly_income,
       ROUND(AVG(engagement_index), 2) AS avg_engagement,
       ROUND(AVG(years_since_promotion), 1) AS avg_years_since_promotion,
       ROUND(0.5 * SUM(annual_income) FILTER (WHERE attrited = 1), 0) AS est_replacement_cost,
       RANK() OVER (ORDER BY AVG(attrited) DESC) AS risk_rank
FROM employees GROUP BY department, job_role ORDER BY attrition_rate_pct DESC;

-- Leavers vs stayers profile (mean comparison)
CREATE OR REPLACE TABLE leaver_profile AS
UNPIVOT (
  SELECT CASE WHEN attrited = 1 THEN 'Leavers' ELSE 'Stayers' END AS grp,
         ROUND(AVG(age),1) AS age, ROUND(AVG(monthly_income),0) AS monthly_income,
         ROUND(AVG(years_at_company),1) AS years_at_company, ROUND(AVG(total_working_years),1) AS total_working_years,
         ROUND(AVG(distance_km),1) AS distance_km, ROUND(AVG(job_satisfaction),2) AS job_satisfaction,
         ROUND(AVG(env_satisfaction),2) AS env_satisfaction, ROUND(AVG(work_life_balance),2) AS work_life_balance,
         ROUND(AVG(engagement_index),2) AS engagement_index, ROUND(100*AVG(overtime::INT),1) AS overtime_pct
  FROM employees GROUP BY 1
) ON COLUMNS(* EXCLUDE grp) INTO NAME metric VALUE val;
