import pandas as pd

def add_issue(
    issues,
    err
):
    if isinstance(err, dict) and err:
        issues.append(err)

def valid_val_range_check(
    row,
    column,
    min_val,
    max_val
):
    value = row.get(column)
    if pd.isna(value):
        return None
    if not (min_val <= value <= max_val):
        return {
            "ID": row["Subject"],
            "Issue": "Value out of range",
            "Column": column
        }
    return None

def non_empty_check(
    row,
    column
):
    if pd.isna(row[column]):
        err_val = {
            "ID": row["Subject"],
            "Issue": "Missing Values",
            "Column": column
        }
        return err_val
    else:
        return None

def binary_check(
    row,
    column
):
    err = non_empty_check(row, column)
    if err:
        return err
    else:
        if (row[column] > 1) or (row[column] < 0):
            err_val = {
                "ID": row["Subject"],
                "Issue": "Not a binary integer result",
                "Column": column
            }
            return err_val
        else:
            return None

def valid_date_check(
    row,
    column
):
    try:
        # Check missing
        if pd.isna(row[column]) or str(row[column]).strip() == "":
            return {
                "ID": row["Subject"],
                "Issue": "Missing or empty date",
                "Column": column
            }

        # Attempt to parse date
        pd.to_datetime(row[column], errors="raise")

        return None  # valid date

    except Exception:
        return {
            "ID": row["Subject"],
            "Issue": "Invalid date format",
            "Column": column
        }

def valid_date_check_month_year(
    row,
    column
):
    try:
        # Check missing
        if pd.isna(row[column]) or str(row[column]).strip() == "":
            return {
                "ID": row["Subject"],
                "Issue": "Missing or empty date",
                "Column": column
            }

        # Attempt to parse date
        year = str(row[column])[0:4]
        month = str(row[column])[5:7]
        if not(1930 < int(year) <= pd.Timestamp.now().year):
            raise Exception("Year")
        if not(month == "nk" or (1 <= int(month) <= 12)):
            raise Exception("Month")
        return None  # valid date

    except Exception:
        return {
            "ID": row["Subject"],
            "Issue": "Invalid date format",
            "Column": column
        }

def therapy_check(
    row,
    val
):
    issues = []
    if pd.isna(row[val[0]]):
        issues.append({
            "ID": row["Subject"],
            "Issue": "Values for selected drug " + val[0][0:3] + " not included",
            "Column": val
        })
        return issues
    add_issue(issues, valid_date_check_month_year(row, val[0]))
    if pd.isna(row[val[1]]):
        add_issue(issues, binary_check(row, val[2]))
    else:
        add_issue(issues, valid_date_check_month_year(row, val[1]))
    add_issue(issues, valid_val_range_check(row, val[3], 0, 4))
    add_issue(issues, valid_val_range_check(row, val[4], 1, 3))
    if row[val[4]] == 3:
        add_issue(issues, non_empty_check(row, val[5]))
    if "LOTstart" in val[0]:
        add_issue(issues, non_empty_check(row, val[6]))
    return issues

def process_group(
    row,
    pr_field,
    options,
    group_name,
    other_key=None,
    other_text=None
):
    issues = []
    if pd.isna(row[pr_field]) or row[pr_field] == 0:
        return 0, issues
    count = 1
    if sum(row[val] for val in options) == 0:
        issues.append({
            "ID": row["Subject"],
            "Issue": f"{group_name} Comorbidities not selected",
            "Column": f"{group_name}...."
        })

    for opt in options:
        add_issue(issues, binary_check(row, opt))
        if other_key and opt == other_key and row[other_key] == 1:
            add_issue(issues, non_empty_check(row, other_text))

    return count, issues

def process_group_systemic(
    row,
    list_key,
    key_dictionary
):
    issues = []
    for key in list_key:
        temp = key_dictionary.get(key)
        if row[key] == 1:
            temp_issues = []
            add_issue(issues, valid_val_range_check(row, temp[0], 1, 2000))
            add_issue(issues, valid_val_range_check(row, temp[1], 1, 3))
            add_issue(issues, valid_date_check(row, temp[2]))
            if not(pd.isna(row[temp[3]])):
                if  row[temp[3]] == 0:
                    add_issue(issues, valid_date_check(row, temp[4]))
                    add_issue(issues, valid_val_range_check(row, temp[5], 0, 4))
                    for val in range(6, 10):
                        add_issue(issues, binary_check(row, temp[val]))
                    if not (pd.isna(row[temp[11]])):
                        add_issue(issues, non_empty_check(row, temp[11]))
                    if "BioOth" in key or "OthNon" in key:
                        add_issue(issues, non_empty_check(row, temp[12]))
                else:
                    add_issue(issues, binary_check(row, temp[3]))

    return issues

def append_issues(
    req_issues,
    opt_issues,
    path_name,
    required,
    optional
):
    # Required block
    add_issue(req_issues, {
        "ID": path_name,
        "Issue": "required",
        "Column": " "
    })
    req_issues.extend(required)
    add_issue(req_issues, {"ID": " ", "Issue": " ", "Column": " "})

    # Optional block
    add_issue(opt_issues, {
        "ID": path_name,
        "Issue": "optional",
        "Column": " "
    })
    opt_issues.extend(optional)
    add_issue(opt_issues, {"ID": " ", "Issue": " ", "Column": " "})
    return req_issues, opt_issues