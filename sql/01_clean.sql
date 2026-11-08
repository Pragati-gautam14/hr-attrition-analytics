-- =============================================================
-- 01 · CLEAN & LABEL EMPLOYEE TABLE (1,470 employees)
-- Drops 3 constant columns, decodes 1-4 survey scales to labels,
-- adds analysis bands and an engagement index.
-- =============================================================
CREATE OR REPLACE TABLE employees AS
SELECT
    EmployeeNumber                                         AS employee_id,
    Age AS age,
    CASE WHEN Age < 25 THEN '18-24' WHEN Age < 35 THEN '25-34'
         WHEN Age < 45 THEN '35-44' ELSE '45+' END         AS age_band,
    Gender AS gender, MaritalStatus AS marital_status,
    Department AS department, JobRole AS job_role, JobLevel AS job_level,
    BusinessTravel AS business_travel, DistanceFromHome AS distance_km,
    Education AS education_level, EducationField AS education_field,
    MonthlyIncome AS monthly_income,
    MonthlyIncome * 12                                     AS annual_income,
    CASE WHEN MonthlyIncome < 3000 THEN '< 3K'
         WHEN MonthlyIncome < 6000 THEN '3K-6K'
         WHEN MonthlyIncome < 10000 THEN '6K-10K'
         ELSE '10K+' END                                   AS income_band,
    PercentSalaryHike AS salary_hike_pct, StockOptionLevel AS stock_option_level,
    OverTime = 'Yes'                                       AS overtime,
    NumCompaniesWorked AS num_companies_worked, TotalWorkingYears AS total_working_years,
    TrainingTimesLastYear AS trainings_last_year,
    YearsAtCompany AS years_at_company,
    CASE WHEN YearsAtCompany <= 1 THEN '0-1 yr' WHEN YearsAtCompany <= 3 THEN '2-3 yrs'
         WHEN YearsAtCompany <= 5 THEN '4-5 yrs' WHEN YearsAtCompany <= 10 THEN '6-10 yrs'
         ELSE '10+ yrs' END                                AS tenure_band,
    YearsInCurrentRole AS years_in_role, YearsSinceLastPromotion AS years_since_promotion,
    YearsWithCurrManager AS years_with_manager,
    EnvironmentSatisfaction AS env_satisfaction, JobSatisfaction AS job_satisfaction,
    RelationshipSatisfaction AS relationship_satisfaction, JobInvolvement AS job_involvement,
    WorkLifeBalance AS work_life_balance, PerformanceRating AS performance_rating,
    ROUND((EnvironmentSatisfaction + JobSatisfaction + RelationshipSatisfaction
           + JobInvolvement + WorkLifeBalance) / 5.0, 2)   AS engagement_index,   -- 1 (low) .. 4 (high)
    (Attrition = 'Yes')::INT                               AS attrited
FROM raw_hr;

CREATE OR REPLACE TABLE data_quality_log AS
SELECT 'Employees' AS check_name, COUNT(*)::VARCHAR AS value FROM raw_hr
UNION ALL SELECT 'Duplicate employee IDs', (COUNT(*) - COUNT(DISTINCT EmployeeNumber))::VARCHAR FROM raw_hr
UNION ALL SELECT 'Null values (all columns)', (SELECT SUM(c)::VARCHAR FROM (UNPIVOT (SELECT COUNT(*) - COUNT(COLUMNS(*)) FROM raw_hr) ON COLUMNS(*) INTO NAME col VALUE c))
UNION ALL SELECT 'Constant columns dropped', 'EmployeeCount, Over18, StandardHours';
