import pandas as pd
import numpy as np
import math
from tempfile import NamedTemporaryFile
import statistics

def store_visit(
    patient_df
):
    patient_data = {}
    clinic_data = {}
    for _, row in patient_df.iterrows():
        subject = row.get("Subject")
        clinic_id = row["site"]
        visit_date = pd.to_datetime(row["dateVisit"]).date()
        patient_data[subject] = (visit_date, clinic_id)
        clinic_data[clinic_id] = visit_date
    return patient_data

def clean_recruitment_data(
    df,
    study_start=None
):
    df = df.copy()
    df["Visit Date"] = pd.to_datetime(
        df["Visit Date"],
        errors="coerce"
    )
    df["Clinic"] = df["Clinic"].astype(str).str.strip()

    # ---- Remove invalid rows ----
    df = df[df["Visit Date"].notna()]
    df = df[df["Clinic"] != ""]
    df = df[df["Clinic"].notna()]
    today = pd.Timestamp.today().normalize()
    df = df[df["Visit Date"] <= today]
    if study_start:
        study_start = pd.to_datetime(study_start)
        df = df[df["Visit Date"] >= study_start]
    df = df[~df.index.duplicated(keep="first")]
    return df

def plot_df(
    df,
    plt
):
    # Ensure datetime and sort
    df["Visit Date"] = pd.to_datetime(df["Visit Date"])
    df = df.sort_values("Visit Date")

    # Count per day and cumulative sum
    total_cumulative = (
        df.groupby("Visit Date")
          .size()
          .cumsum()
    )

    # Control the plot size
    fig1, ax = plt.subplots(figsize=(10, 5))
    ax.plot(
        total_cumulative.index,
        total_cumulative.values,
        linewidth=2,
        label="Total Recruitment"
    )

    # Graph characteristics
    ax.set_title("Total Recruitment", fontsize=14, weight="bold")
    ax.set_xlabel("Recruitment Date")
    ax.set_ylabel("Total Patients")
    ax.set_ylim(0, ax.get_ylim()[1])
    tmp_total = NamedTemporaryFile(delete=False, suffix=".png")
    fig1.savefig(tmp_total.name, dpi=300)
    plt.close(fig1)
    return tmp_total

def plot_df_center(
    df,
    plt
):
    # Count per day per clinic
    center_daily = (
        df.groupby(["Visit Date", "Clinic"])
        .size()
        .reset_index(name="Count")
    )

    # Pivot to wide format
    pivot_df = center_daily.pivot(
        index="Visit Date",
        columns="Clinic",
        values="Count"
    ).fillna(0)

    # Make it continuous by filling missing dates
    pivot_df = pivot_df.asfreq("D", fill_value=0)
    center_cumulative = pivot_df.cumsum()
    fig2, ax = plt.subplots(
        figsize=(12, 6),
        constrained_layout=True
    )

    # Plot the data
    for clinic in center_cumulative.columns:
        ax.plot(
            center_cumulative.index,
            center_cumulative[clinic],
            linewidth=1.8,
            label=clinic
        )

    ax.set_title("Cumulative Recruitment by Centre", fontsize=14, weight="bold")
    ax.set_xlabel("Visit Date")
    ax.set_ylabel("Cumulative Patients")
    ax.set_ylim(0, ax.get_ylim()[1])
    ax.grid(True, linestyle="--", alpha=0.4)

    # Dynamic Legend Font Size
    n_centres = len(center_cumulative.columns)
    if n_centres <= 5:
        legend_size = 15
    elif n_centres <= 10:
        legend_size = 13
    else:
        legend_size = 10
    ax.legend(
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        fontsize=legend_size,
        frameon=False
    )

    tmp_centre = NamedTemporaryFile(delete=False, suffix=".png")
    fig2.savefig(tmp_centre.name, dpi=300)
    plt.close(fig2)
    return tmp_centre

def plot_df_follow_ups(
    visit_group,
    missed_visit,
    due_visit,
    plt
):
    visit_labels = ["Visit 1", "Visit 2", "Visit 3", "Visit 4"]
    fig, ax = plt.subplots(figsize=(12, 7), constrained_layout=True)

    # Get ALL unique centers and map to colours
    all_centers = pd.concat(
        [v for v in visit_group if v is not None and not v.empty]
    )["Clinic"].unique()
    color_map = {
        center: plt.cm.tab20(i % 20)
        for i, center in enumerate(all_centers)
    }

    # Plot stacked visits
    x_positions = np.arange(len(visit_labels))
    for i, visit_df in enumerate(visit_group):
        if visit_df is None or visit_df.empty:
            continue
        counts = (
            visit_df["Clinic"]
            .value_counts()
            .sort_values(ascending=False)
        )
        bottom = 0
        for center, value in counts.items():
            ax.bar(
                x_positions[i],
                value,
                bottom=bottom,
                color=color_map[center],
                label=center if i == 0 else ""  # avoid duplicate legend entries
            )
            bottom += value

    # Missed & Due Visits
    missed_count = len(missed_visit) if missed_visit is not None else 0
    due_count = len(due_visit) if due_visit is not None else 0
    ax.bar(len(visit_labels) + 1, due_count)
    ax.bar(len(visit_labels) + 2, missed_count)

    # Formatting
    xticks = list(x_positions) + [len(visit_labels) + 1, len(visit_labels) + 2]
    xlabels = visit_labels + ["Due", "Missed"]
    ax.set_xticks(xticks)
    ax.set_xticklabels(xlabels)
    ax.set_ylabel("Number of Patients")
    ax.set_title("Follow-Up Visits by Center")
    ax.set_ylim(bottom=0)
    ax.legend(
        title="Center",
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
        borderaxespad=0
    )

    # Save figure for imputing into the Excel file
    tmp_centre = NamedTemporaryFile(delete=False, suffix=".png")
    fig.savefig(tmp_centre.name, dpi=300)
    plt.close(fig)
    return tmp_centre

def calc_follow_up_avg(
    visit_group
):
    if len(visit_group) == 0 or visit_group[0].empty:
        return pd.DataFrame(columns=[
            "Visit Date 1", "Visit Date 2", "Visit Date 3", "Visit Date 4",
            "mean_days_v1_to_v2", "mean_days_v2_to_v3", "mean_days_v3_to_v4"
        ])

        # Reset index so patient ID is a column
    visits = [v.reset_index() for v in visit_group]

    # Start with Visit 1
    collated_visit = visits[0].rename(columns={"Visit Date": "Visit Date 1"})

    # Merge subsequent visits
    for i, v in enumerate(visits[1:], start=2):
        if not v.empty:
            collated_visit = collated_visit.merge(
                v[["index", "Visit Date"]].rename(columns={"Visit Date": f"Visit Date {i}"}),
                on="index",
                how="left"
            )
        else:
            # If visit DataFrame is empty, create the column filled with NaT
            collated_visit[f"Visit Date {i}"] = pd.NaT

    # Set index back to patient ID
    collated_visit.set_index("index", inplace=True)

    # Calculate days between visits
    collated_visit["mean_days_v1_to_v2"] = (collated_visit["Visit Date 2"] - collated_visit["Visit Date 1"]).dt.days
    collated_visit["mean_days_v2_to_v3"] = (collated_visit["Visit Date 3"] - collated_visit["Visit Date 2"]).dt.days
    collated_visit["mean_days_v3_to_v4"] = (collated_visit["Visit Date 4"] - collated_visit["Visit Date 3"]).dt.days

    # Calculate the avg follow-up time between visits
    avg_follow_v2_data = collated_visit["mean_days_v1_to_v2"].to_list()
    avg_follow_v2 = [x for x in avg_follow_v2_data if not (isinstance(x, float) and math.isnan(x))]
    if len(avg_follow_v2) > 0:
        avg_follow_v2 = statistics.mean(avg_follow_v2)
    avg_follow_v3_data = collated_visit["mean_days_v2_to_v3"].to_list()
    avg_follow_v3 = [x for x in avg_follow_v3_data if not (isinstance(x, float) and math.isnan(x))]
    if len(avg_follow_v3) > 0:
        avg_follow_v3 = statistics.mean(avg_follow_v3)
    avg_follow_v4_data = collated_visit["mean_days_v3_to_v4"].to_list()
    avg_follow_v4 = [x for x in avg_follow_v4_data if not (isinstance(x, float) and math.isnan(x))]
    if len(avg_follow_v4) > 0:
        avg_follow_v4 = statistics.mean(avg_follow_v4)

    # Calculate the avg follow-up time per center
    collated_clinic_visit = collated_visit[["Clinic", "mean_days_v1_to_v2", "mean_days_v2_to_v3", "mean_days_v3_to_v4"]]
    collated_clinic_visit = collated_clinic_visit.dropna(
        subset=["mean_days_v1_to_v2", "mean_days_v2_to_v3", "mean_days_v3_to_v4"],
        how="all"
    )
    followup_cols = ["mean_days_v1_to_v2", "mean_days_v2_to_v3", "mean_days_v3_to_v4"]

    clinic_summary = (
        collated_clinic_visit
        .groupby("Clinic")[followup_cols]
        .agg(["mean", "count",
              lambda x: x.quantile(0.25),
              lambda x: x.quantile(0.75)])
    )

    clinic_summary.columns = ["mean", "count", "q1", "q3"] * len(followup_cols)
    clinic_summary = clinic_summary.reset_index()

    for i, col in enumerate(followup_cols):
        mean = clinic_summary.iloc[:, 1 + i * 4]
        count = clinic_summary.iloc[:, 2 + i * 4]
        q1 = clinic_summary.iloc[:, 3 + i * 4]
        q3 = clinic_summary.iloc[:, 4 + i * 4]

        clinic_summary[col] = (
                mean.round(1).astype(str)
                + " (" + q1.round(1).astype(str)
                + "–" + q3.round(1).astype(str)
                + ", N=" + count.astype(int).astype(str) + ")"
        )
    clinic_summary = clinic_summary[["Clinic"] + followup_cols]

    return clinic_summary