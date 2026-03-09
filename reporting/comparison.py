import pandas as pd

def _add_exists_flag(
    current_df,
    previous_df,
    key_columns
):
    if current_df.empty:
        current_df["Exists_Last_Month"] = False
        return current_df

    merge_df = current_df.merge(
        previous_df[key_columns],
        on=key_columns,
        how="left",
        indicator=True
    )

    current_df["Exists_Last_Month"] = merge_df["_merge"] == "both"
    return current_df

def compare_previous_month(
    missed_visit_df,
    due_visit_df,
    issues_df_req,
    issues_df_opt,
    prev_file
):
    if not prev_file:
    # ---- No previous file → nothing existed last month ----
        for df in (missed_visit_df, due_visit_df, issues_df_req, issues_df_opt):
            df["Exists Last Month"] = False
        return missed_visit_df, due_visit_df, issues_df_req, issues_df_opt

    # ---- Load previous sheets once ----
    previous_sheets = pd.read_excel(
        prev_file,
        sheet_name=[
            "Patient Visit Missed",
            "Patient Visit Due",
            "Required Data Point Issues",
            "Optional Data Point Issues",
        ]
    )

    visit_columns = ["Subject ID", "Last Visit"]
    issues_columns = ["ID", "Column"]

    # ---- Ensure datetime consistency ----
    for df in (missed_visit_df, due_visit_df):
        if "Last Visit" in df.columns:
            df["Last Visit"] = pd.to_datetime(df["Last Visit"], errors="coerce")

    for df in (
        previous_sheets["Patient Visit Missed"],
        previous_sheets["Patient Visit Due"],
    ):
        if "Last Visit" in df.columns:
            df["Last Visit"] = pd.to_datetime(df["Last Visit"], errors="coerce")

    # ---- Apply comparison ----
    missed_visit_df = _add_exists_flag(
        missed_visit_df,
        previous_sheets["Patient Visit Missed"],
        visit_columns
    )

    due_visit_df = _add_exists_flag(
        due_visit_df,
        previous_sheets["Patient Visit Due"],
        visit_columns
    )

    issues_df_req = _add_exists_flag(
        issues_df_req,
        previous_sheets["Required Data Point Issues"],
        issues_columns
    )

    issues_df_opt = _add_exists_flag(
        issues_df_opt,
        previous_sheets["Optional Data Point Issues"],
        issues_columns
    )

    for df_ in [missed_visit_df, due_visit_df]:
        df_["Last Visit"] = pd.to_datetime(df_["Last Visit"]).dt.date
        df_["Due Date"] = pd.to_datetime(df_["Due Date"]).dt.date

    return missed_visit_df, due_visit_df, issues_df_req, issues_df_opt

def load_associated_data(
    info_file
):
    if not info_file:
    # ---- No previous file → nothing existed last month ----
        return "No file found"

    # ---- Load previous sheets once ----
    previous_sheets = pd.read_excel(
        info_file,
        sheet_name=[
            "P1",
            "A1",
        ]
    )
    return previous_sheets

def append_associated_info(
    df_list,
    file_info
):
    match_col_df = "Column"

    extracted_columns = [
        "Page in CRF",
        "Questions",
        "Type",
        "Format",
        "Range",
        "Options"
    ]

    duplicates = file_info["Variable name"][
        file_info["Variable name"].duplicated()
    ]

    if not duplicates.empty:
        print("WARNING: Duplicate variable names found in file_info:")
        print(duplicates.unique())

    # Build a fast lookup dictionary from file_info
    lookup = (
        file_info
        .set_index("Variable name")[extracted_columns]
        .to_dict(orient="index")
    )

    updated_list = []

    for row in df_list:

        variable_name = row.get(match_col_df)

        extra_info = lookup.get(variable_name, {})

        # Add extracted columns (None if no match found)
        for col in extracted_columns:
            row[col] = extra_info.get(col)

        updated_list.append(row)

    return updated_list



