"""Download the IBM HR Employee Attrition sample dataset into data/raw/."""
from pathlib import Path
import urllib.request
URL = "https://raw.githubusercontent.com/IBM/employee-attrition-aif360/master/data/emp_attrition.csv"
OUT = Path(__file__).resolve().parents[1] / "data" / "raw" / "hr_employee_attrition.csv"
if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if not OUT.exists():
        raw = urllib.request.urlopen(URL).read().decode("utf-8-sig")
        OUT.write_text(raw, encoding="utf-8")
    print("data ready:", OUT)
