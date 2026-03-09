import pandas as pd
from datetime import date, timedelta
from reporting.patient_tracking import clean_recruitment_data

def store_latest_visit(
    df,
    latest_visit
):
    for _, row in df.iterrows():
        subject = row.get("Subject")
        clinic_id = row["Center Unique Id"]
        center = row["site"]
        doctor = row["Subject Responsible Doctor"]
        visit_date = pd.to_datetime(row["dateVisit"]).date()

        if (
            subject not in latest_visit
            or visit_date > latest_visit[subject][0]
        ):
            latest_visit[subject] = (visit_date, clinic_id, center, doctor)

    return latest_visit

def check_patient_visits_valid(
        latest_visit
):
    missed = {}
    due = {}
    today = date.today()
    cutoff = timedelta(days=230)
    earliest = timedelta(days=130)

    for patient_id, (visit_date, clinic_id, center, doctor) in latest_visit.items():

        # Ensure pure date (remove time component)
        if hasattr(visit_date, "date"):
            visit_date = visit_date.date()

        delta = today - visit_date
        due_date = visit_date + cutoff
        temp_data = (
                clinic_id,
                center,
                doctor,
                visit_date,
                due_date,
            )
        if delta > cutoff:
            missed[patient_id] = temp_data
        elif earliest < delta <= cutoff:
            due[patient_id] = temp_data


    missed_visit_df = pd.DataFrame(
        [
            (patient_id, clinic_id, center, doctor, visit_date, due_date)
            for patient_id, (clinic_id, center, doctor, visit_date, due_date)
            in missed.items()
        ],
        columns=["Subject ID", "Clinic ID", "Center Project Id", "Subject Responsible Doctor", "Last Visit", "Due Date"]
    )

    due_visit_df = pd.DataFrame(
        [
            (patient_id, clinic_id, center, doctor, visit_date, due_date)
            for patient_id, (clinic_id, center, doctor, visit_date, due_date)
            in due.items()
        ],
        columns=["Subject ID", "Clinic ID", "Center Project Id", "Subject Responsible Doctor", "Last Visit", "Due Date"]
    )

    return missed_visit_df, due_visit_df

def visit_transpose(visit, start_date):
    # empty check
    if not visit:
        return pd.DataFrame(columns=["Visit Date", "Clinic"])

    df = pd.DataFrame(visit).transpose()
    df.columns = ["Visit Date", "Clinic"]
    df = clean_recruitment_data(df, start_date)
    return df