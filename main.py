import pandas as pd
import os
import re
from tkinter import filedialog
from validators.patient import validate_patient
from validators.doctor import validate_doctor
from visits.visit_tracker import store_latest_visit, check_patient_visits_valid, visit_transpose
from reporting.patient_tracking import store_visit, clean_recruitment_data
from reporting.excel_builder import build_excel_report
from validators.common_checks import append_issues
from reporting.comparison import load_associated_data, append_associated_info

def validate_excel(
    file_paths,
    prev_file,
    info_file,
    report_dir="LebRAD_Data_Download"
):
    req_issues = []
    opt_issues = []
    latest_visit, earliest_visit = {}, {}
    follow_1, follow_2, follow_3 = {}, {}, {}
    file_infos = {}
    info_data = load_associated_data(info_file)

    for file_path in file_paths:
        df = pd.read_excel(file_path)
        os.makedirs(report_dir, exist_ok=True)
        path_name = ""
        file_lower = file_path.lower()
        match = re.search(r"visit\s*(\d+)\s*-\s*(doctor|patient)", file_lower)
        if match:
            visit_number = match.group(1)
            role = match.group(2).capitalize()
            path_name = f"{role} - Visit {visit_number}"

        is_follow = 1 if "follow" in file_lower else 0
        validators = {
            "patient": validate_patient,
            "doctor": validate_doctor,
        }
        file_infos[path_name] = df[df.columns[0]].count()
        for key, validator in validators.items():
            if key in file_lower:
                required, optional = validator(df, is_follow)

                if key == "patient":
                    latest_visit = store_latest_visit(df, latest_visit)
                    if "Visit 1" in file_path:
                        earliest_visit = store_visit(df)
                    elif "Visit 2" in file_path:
                        follow_1 = store_visit(df)
                    elif "Visit 3" in file_path:
                        follow_2 = store_visit(df)
                    elif "Visit 4" in file_path:
                        follow_3 = store_visit(df)
                    required = append_associated_info(required, info_data["P1"])
                    optional = append_associated_info(optional, info_data["P1"])
                else:
                    required = append_associated_info(required, info_data["A1"])
                    optional = append_associated_info(optional, info_data["A1"])


                req_issues, opt_issues = append_issues(req_issues, opt_issues, path_name, required, optional)
                break

    # Check the latest visit is within the time frame
    # --- Patient Visits ---
    missed_visit_df, due_visit_df = check_patient_visits_valid(latest_visit)

    # --- Produce graphs of patients
    allkeys = list(earliest_visit.keys())
    start_date = earliest_visit[allkeys[0]]
    visit_group = [
        visit_transpose(earliest_visit, start_date[0]),
        visit_transpose(follow_1, start_date[0]),
        visit_transpose(follow_2, start_date[0]),
        visit_transpose(follow_3, start_date[0]),
    ]

    build_excel_report(
        missed_visit_df,
        due_visit_df,
        req_issues,
        opt_issues,
        prev_file,
        visit_group,
        file_infos,
        report_dir
    )

def main():
    files = filedialog.askopenfilenames()
    prev_file = next((f for f in files if "Validation" in f), "")
    info_file = next((f for f in files if "Variables_Notes" in f), "")
    if prev_file:
        files = [f for f in files if f != prev_file]
    if info_file:
        files = [f for f in files if f != info_file]

    validate_excel(files, prev_file, info_file)

if __name__ == "__main__":
    main()
