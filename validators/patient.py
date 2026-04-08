import pandas as pd
from validators.common_checks import (valid_val_range_check,
                                      non_empty_check,
                                      valid_date_check,
                                      binary_check,
                                      add_issue)

def validate_patient(
    df,
    visit_type
):
    required_patient_issues = []
    optional_patient_issues = []

    for _ , row in df.iterrows():
        # Variables that are dependent on which visit they are attending
        if visit_type == 0:
            # Initial visit
            add_issue(required_patient_issues, valid_val_range_check(row, "YOB", 1925, pd.Timestamp.now().year))
            add_issue(required_patient_issues, valid_val_range_check(row, "ethnic", 0, 9))
            if row["ethnic"] == 9 and pd.isna(row["ethnicOth"]):
                add_issue(required_patient_issues, {
                    "ID": row["Subject"],
                    "Issue": "Ethnic Other chosen, no value",
                    "Column": "ethnicOth"
                })
            if row["ageVisit"] > 17:
                add_issue(optional_patient_issues, valid_val_range_check(row, "docTimes", 0, 50))
                add_issue(required_patient_issues, valid_val_range_check(row, "yearsAD", 0, row["ageVisit"]))
                add_issue(required_patient_issues, binary_check(row, "AllRhin"))
                if row["AllRhin"] == 1 and not (
                        row["AllRhins1"] == 1 or row["AllRhins2"] == 1 or row["AllRhins3"] == 1):
                    add_issue(required_patient_issues, {
                        "ID": row["Subject"],
                        "Issue": "Allergic Rhinitis Error",
                        "Column": "AllRhins1, 2 or 3"
                    })
                add_issue(required_patient_issues, binary_check(row, "AllAsth"))
                if row["AllAsth"] == 1 and not (
                        row["AllAsths1"] == 1 or row["AllAsths2"] == 1 or row["AllAsths3"] == 1):
                    add_issue(required_patient_issues, {
                        "ID": row["Subject"],
                        "Issue": "Asthma Error",
                        "Column": "AllAsths1, 2 or 3"
                    })
            else:
                add_issue(optional_patient_issues, valid_val_range_check(row, "docTimesChild", 0, 50))
                add_issue(optional_patient_issues, valid_val_range_check(row, "monthsAD", 0, (row["ageVisit"] * 12)))
                add_issue(required_patient_issues, binary_check(row, "AllRhinChild"))
                add_issue(required_patient_issues, binary_check(row, "AllAsthChild"))
            fam_his_check: list[str] = ["FamHis1", "FamHis2", "FamHis3", "FamHis4", "FamHis5"]
            fam_hist_tot = 0
            for val in fam_his_check:
                if not pd.isna(row[val]):
                    add_issue(required_patient_issues, binary_check(row, val))
                    fam_hist_tot += 1
            if fam_hist_tot == 0:
                add_issue(required_patient_issues, {
                    "ID": row["Subject"],
                    "Issue": "Family History Error",
                    "Column": "FamHis1 through 5"
                })
            if row["ageVisit"] < 7:
                preg_tot = 0
                preg_var = ["PregAntib", "PregOthMed", "PregTobac", "PregAlco", "PregOthSubs"]
                for val in preg_var:
                    if row[val] == 1:
                        preg_tot += 1
                        if val == "PregOthSubs":
                            add_issue(required_patient_issues, non_empty_check(row, "PregOthSubs"))
                            add_issue(required_patient_issues, non_empty_check(row, "PregMothOth"))
                if preg_tot == 0:
                    add_issue(required_patient_issues, non_empty_check(row, "PregNone"))
                    if not row["PregNone"] == 1:
                        add_issue(required_patient_issues, {
                            "ID": row["Subject"],
                            "Issue": "Pregnancy selection incorrect",
                            "Column": "PregNone"
                        })
                add_issue(required_patient_issues, valid_val_range_check(row, "ChildDel", 0, 2))
                add_issue(optional_patient_issues, valid_val_range_check(row, "ChildOrd", 0, 5))
                if row["ChildOrd"] == 5:
                    add_issue(optional_patient_issues, non_empty_check(row, "ChildOrdOth"))
                add_issue(optional_patient_issues, valid_val_range_check(row, "ChildFed", 1, 3))
                if not pd.isna(row["ChildAgeEat"]):
                    add_issue(optional_patient_issues, valid_val_range_check(row, "ChildAgeEat", 0, 24))
                if not pd.isna(row["ChildSkin"]):
                    add_issue(optional_patient_issues, binary_check(row, "ChildSkin"))
                    if row["ChildSkin"] == 1:
                        add_issue(optional_patient_issues, valid_val_range_check(row, "ChildSkinYes", 1, 24))
        else:
            # Follow-up Visit
            if row["ageVisit"] < 7:
                add_issue(optional_patient_issues, binary_check(row, "ChildMoist"))
                if not pd.isna(row["ChildMoist"]) and row["ChildMoist"] == 1:
                    add_issue(optional_patient_issues, valid_val_range_check(row, "ChildMoistYes", 0, 30))


        # Page 1:
        if row["Dropout"] == 1 and (
                pd.isna(row["Dropout Status"]) or pd.isna(row["Dropout Comment"]) or pd.isna(row["Dropout Date"])):
            required_patient_issues.append({
                "ID": row["Subject"],
                "Issue": "Missing Values",
                "Column": "Dropout"
            })
        add_issue(required_patient_issues, valid_date_check(row, "dateVisit"))
        add_issue(required_patient_issues, valid_val_range_check(row, "ageVisit", 0, 120))
        add_issue(required_patient_issues, valid_val_range_check(row, "ageVisit", 0, 120))
        if abs(row["ageVisit"] - row["ageVisit"]) > 1:
            add_issue(required_patient_issues, {
                "ID": row["Subject"],
                "Issue": "Age Discrepancy",
                "Column": "ageVisit"
            })
        add_issue(required_patient_issues, valid_val_range_check(row, "height", 1, 300))
        add_issue(required_patient_issues,valid_val_range_check(row, "weight", 1, 200))
        if row["ageVisit"] > 17:
            add_issue(required_patient_issues, non_empty_check(row, "BMI"))
            if pd.isna(row["Educ"]):
                add_issue(optional_patient_issues, valid_val_range_check(row, "Educ", 0, 10))
            else:
                add_issue(optional_patient_issues, {
                    "ID": row["Subject"],
                    "Issue": "No education information was entered",
                    "Column": "Education"
                })
            add_issue(required_patient_issues, valid_val_range_check(row, "SmokeS", 0, 5))
            add_issue(optional_patient_issues, binary_check(row, "EmpSta"))
            if row["EmpSta"] == 1:
                add_issue(optional_patient_issues, valid_val_range_check(row, "EmpStaJ",1,4))
        else:
            add_issue(optional_patient_issues, valid_val_range_check(row, "EducChild", 0, 10))
            add_issue(optional_patient_issues, valid_val_range_check(row, "EducMoth", 0, 10))
            add_issue(optional_patient_issues, valid_val_range_check(row, "EducFath", 0, 10))
            if pd.isna(row["EducChild"]) and pd.isna(row["EducMoth"]) and pd.isna(row["EducFath"]):
                add_issue(optional_patient_issues, {
                    "ID": row["Subject"],
                    "Issue": "No education information was entered",
                    "Column": "Education"
                })
            add_issue(required_patient_issues, binary_check(row, "SmokeSec"))
            add_issue(optional_patient_issues, binary_check(row, "EmpStaMoth"))
            if row["EmpSta"] == 1:
                add_issue(optional_patient_issues, valid_val_range_check(row, "EmpStaJMoth",1,4))
            add_issue(optional_patient_issues, binary_check(row, "EmpStaFath"))
            if row["EmpSta"] == 1:
                add_issue(optional_patient_issues, valid_val_range_check(row, "EmpStaJFath",1,4))
        if 12 < row["ageVisit"] < 18:
            add_issue(required_patient_issues, valid_val_range_check(row, "SmokeUnder", 0, 5))
        add_issue(optional_patient_issues, non_empty_check(row, "resid"))
        add_issue(required_patient_issues, binary_check(row, "LiveGreen"))
        add_issue(required_patient_issues, binary_check(row, "LiveGen"))

        if not pd.isna(row["House"]):
            add_issue(optional_patient_issues, valid_val_range_check(row, "House", 1, 10))
        else:
            add_issue(optional_patient_issues, {
                "ID": row["Subject"],
                "Issue": "Household size not enterered",
                "Column": "House"
            })
        if not pd.isna(row["IncFam"]):
            add_issue(optional_patient_issues, valid_val_range_check(row, "IncFam", 0, 20))
        fam_check: list[str] = ["Fami1", "Fami2", "Fami3", "Fami4", "Fami5", "Fami6"]
        for val in fam_check:
            if not pd.isna(row[val]):
                add_issue(optional_patient_issues, binary_check(row, val))
                if val == "Fami5" and row[val] == 1:
                    add_issue(optional_patient_issues, valid_val_range_check(row, val, 1, 20))

        # Page 2:
        if row["ageVisit"] > 17:
            add_issue(required_patient_issues, valid_val_range_check(row, "DocVis12", 0,50))
            add_issue(optional_patient_issues, binary_check(row, "hospIn3M"))
            if (not pd.isna(row["hospIn3M"])) and row["hospIn3M"] == 1 and pd.isna(row["hospIn3MDay"]):
                add_issue(optional_patient_issues, {
                    "ID": row["Subject"],
                    "Issue": "Days in hospital Error",
                    "Column": "hospIn3MDay"
                })
        elif 3 < row["ageVisit"] < 18:
            add_issue(optional_patient_issues, valid_val_range_check(row, "schoolDays", 0, 100))
            if (not pd.isna(row["schoolProd"])) and row["schoolProd"] == -1:
                add_issue(optional_patient_issues, {
                    "ID": row["Subject"],
                    "Issue": "Productivity Days not answered",
                    "Column": "hospIn3MDay"
                })
            add_issue(optional_patient_issues, valid_val_range_check(row, "schoolProd", -1, 10))
        else:
            add_issue(required_patient_issues, valid_val_range_check(row, "DocVis12Child", 0, 50))
            add_issue(required_patient_issues, binary_check(row, "hospIn3MCh"))
            if (not pd.isna(row["hospIn3MCh"])) and row["hospIn3MCh"] == 1 and pd.isna(row["hospIn3MDay"]):
                add_issue(required_patient_issues, {
                    "ID": row["Subject"],
                    "Issue": "Child Days in hospital Error",
                    "Column": "hospIn3MDay"
                })
        add_issue(optional_patient_issues, binary_check(row, "treatAffec"))
        add_issue(optional_patient_issues, binary_check(row, "accessAffec"))

        # Page 3:
        if row["ageVisit"] < 7:
            # Check this when Anna checks the data output
            if visit_type == 0:
                if not pd.isna(row["ChildDayCare"]):
                    add_issue(optional_patient_issues, binary_check(row, "ChildDayCare"))
                    if row["ChildDayCare"] == 1:
                        add_issue(optional_patient_issues, valid_val_range_check(row, "ChildDayCareYes", 1, 7))
                if not pd.isna(row["ChildBath"]):
                    add_issue(optional_patient_issues, binary_check(row, "ChildBath"))
            else:
                if not pd.isna(row["ChildDayCare"]):
                    add_issue(optional_patient_issues, valid_val_range_check(row, "ChildDayCare", 1,2))
                    if row["ChildDayCare"] == 1:
                        add_issue(optional_patient_issues, valid_val_range_check(row, "ChildDayCareYes", 1, 7))
                if not pd.isna(row["ChildBath"]):
                    add_issue(optional_patient_issues, valid_val_range_check(row, "ChildBath", 1 ,2))
        elif row["ageVisit"] > 15:
            if not pd.isna(row["employ"]):
                add_issue(required_patient_issues, binary_check(row, "employ"))
                if row["employ"] == 1:
                    add_issue(required_patient_issues, valid_val_range_check(row, "hoursQ2", 0, 100))
                    add_issue(required_patient_issues, valid_val_range_check(row, "hoursQ3", 0, 100))
                    add_issue(required_patient_issues, valid_val_range_check(row, "hoursQ4", 0, 100))
                    add_issue(required_patient_issues, valid_val_range_check(row, "prodQ5", -1, 10))
                    add_issue(required_patient_issues, valid_val_range_check(row, "regQ6", -1, 10))

        # Page 4 Body Map:
        body_map_fields = [
            "front-scalp", "front-hair-line", "front-eyes", "front-ears", "front-nose",
            "front-teeth", "front-lower-jaw-region", "front-neck",
            "back-scalp", "back-neck", "back-back-of-neck",
            "front-decollete", "front-chest", "back-upper-back",
            "front-abdomen", "back-flank_left", "back-flank_right", "back-lower-back",
            "front-shoulder-region_right", "front-upper-arm_right", "front-axilla_right",
            "front-elbow_right", "front-lower-arm_right", "front-wrists_right",
            "front-palms_right", "front-hypothenar-region_right", "front-thenar-region_right",
            "front-fingers_right", "back-shoulder-region_right", "back-upper-arm_right",
            "back-axilla_right", "back-elbow_right", "back-lower-arm_right",
            "back-wrists_right", "back-palms_right", "back-fingers_right", "back-finger-nail_right",
            "front-shoulder-region_left", "front-upper-arm_left", "front-axilla_left",
            "front-elbow_left", "front-lower-arm_left", "front-wrists_left",
            "front-palms_left", "front-hypothenar-region_left", "front-thenar-region_left",
            "front-fingers_left", "back-shoulder-region_left", "back-upper-arm_left",
            "back-axilla_left", "back-elbow_left", "back-lower-arm_left", "back-wrists_left",
            "back-palms_left", "back-fingers_left", "back-finger-nail_left",
            "front-genital-region", "front-genital-region-out", "front-genital-region-out-extra_right",
            "front-upper-leg_right", "front-knee_right", "front-lower-leg_right",
            "front-ankle-joint_right", "front-back-of-the-feet_right", "front-forefoot_right",
            "front-toe_right", "front-genital-region-out-extra_left",
            "front-upper-leg_left", "front-knee_left", "front-lower-leg_left",
            "front-ankle-joint_left", "front-back-of-the-feet_left", "front-forefoot_left",
            "front-toe_left", "back-gluteos_right", "back-perineum",
            "back-upper-leg_right", "back-hollow-of-the-knee_right", "back-lower-leg_right",
            "back-ankle-joint_right", "back-heel_right", "back-sole_right",
            "back-gluteos_left", "back-anus", "back-upper-leg_left",
            "back-hollow-of-the-knee_left", "back-lower-leg_left", "back-ankle-joint_left",
            "back-heel_left", "back-sole_left"
        ]
        if non_empty_check(row, "BodyMapGADA-biological sex"):
            error_message = "Incomplete on page 4 check rest of patient"
            add_issue(required_patient_issues, {
                "ID": row["Subject"],
                "Issue": error_message,
                "Column": "Page 4"
            })
            return required_patient_issues, optional_patient_issues
        add_issue(required_patient_issues, binary_check(row, "BodyMapGADA-biological sex"))
        if not(row["BodyMapGADA-age"] == "adult"
                or row["BodyMapGADA-age"] == "baby"
                or row["BodyMapGADA-age"] == "child1to4"
                or row["BodyMapGADA-age"] == "child5to9"
                or row["BodyMapGADA-age"] == "teen"):
            add_issue(required_patient_issues, {
                "ID": row["Subject"],
                "Issue": "body map definition issue",
                "Column": "BodyMapGADA-age"
            })
        for val in body_map_fields:
            add_issue(required_patient_issues, binary_check(row, val))
        add_issue(required_patient_issues, valid_val_range_check(row, "BSAmap", 0, 200))

        # Page 5 Recap:
        if row["ageVisit"] > 11:
            if not pd.isna(row["Rec1"]):
                recap_variables = ["Rec1", "Rec2", "Rec3", "Rec4", "Rec6", "Rec7"]
                if visit_type == 0:
                    recap_variables.extend(["Rec5"])
                else:
                    recap_variables.extend(["AERec5"])
                tot = 0
                for val in recap_variables:
                    add_issue(required_patient_issues, valid_val_range_check(row, val, 0, 4))
                    tot += row[val]
                if tot != row["RecTotal"]:
                    add_issue(required_patient_issues, {
                        "ID": row["Subject"],
                        "Issue": "RECAP total is incorrect",
                        "Column": "RecTotal"
                    })
            else:
                add_issue(required_patient_issues, {
                    "ID": row["Subject"],
                    "Issue": "Check, RECAP not entered",
                    "Column": "Rec1"
                })
        elif row["ageVisit"] < 12:
            if not pd.isna(row["RecKid1"]):
                recap_kid_variables = ["RecKid1", "RecKid2", "RecKid3", "RecKid4", "RecKid5", "RecKid6", "RecKid7"]
                tot = 0
                for val in recap_kid_variables:
                    add_issue(required_patient_issues, valid_val_range_check(row, val, 0, 4))
                    tot += row[val]
                if tot != row["RecKidTotal"]:
                    add_issue(required_patient_issues, {
                        "ID": row["Subject"],
                        "Issue": "RECAP Kid total is incorrect",
                        "Column": "RecKidTotal"
                    })
            else:
                add_issue(required_patient_issues, {
                    "ID": row["Subject"],
                    "Issue": "Check, RECAP Kid not entered",
                    "Column": "RecKid1"
                })

        # Page 6
        add_issue(required_patient_issues, valid_val_range_check(row, "NRSItch", -1, 10))
        add_issue(required_patient_issues, valid_val_range_check(row, "NRSSleep", -1, 10))
        add_issue(required_patient_issues, valid_val_range_check(row, "NRSPain", -1, 10))

        # Page 7
        if row["ageVisit"] > 15 and not pd.isna(row["dl1qi"]):
            dlqi_adult = ["dl1qi", "dl2qi", "dl3qi", "dl4qi", "dl5qi", "dl6qi", "dl8qi", "dl9qi", "dl10qi"]
            for val in dlqi_adult:
                add_issue(required_patient_issues, valid_val_range_check(row, val, 0 ,4))
            # must have one of either 7 selected
            if non_empty_check(row, "dl7Aqi") and non_empty_check(row, "dl7Bqi"):
                add_issue(required_patient_issues, {
                    "ID": row["Subject"],
                    "Issue": "DLQI Question 7 check",
                    "Column": "dl7Aqi"
                })
            elif non_empty_check(row, "dl7Aqi"):
                add_issue(required_patient_issues, valid_val_range_check(row, "dl7Bqi", 0, 3))
            else:
                add_issue(required_patient_issues, valid_val_range_check(row, "dl7Aqi", 0, 3))
            add_issue(required_patient_issues, valid_val_range_check(row, "dlqi", 0, 30))
        elif 3 < row["ageVisit"] < 16 and not pd.isna(row["dl1qiCh"]):
            dlqi_teen = ["dl1qiCh", "dl2qiCh", "dl3qiCh", "dl4qiCh", "dl5qiCh", "dl6qiCh", "dl8qiCh", "dl9qiCh", "dl10qiCh"]
            for val in dlqi_teen:
                add_issue(required_patient_issues, valid_val_range_check(row, val, 0 ,4))
            # must have one of either 7 selected
            if non_empty_check(row, "dl7AqiCh") and non_empty_check(row, "dl7BqiCh"):
                add_issue(required_patient_issues, {
                    "ID": row["Subject"],
                    "Issue": "DLQI Question 7 check",
                    "Column": "dl7AqiCh"
                })
            elif non_empty_check(row, "dl7AqiCh"):
                add_issue(required_patient_issues, valid_val_range_check(row, "dl7BqiCh", 0, 4))
            else:
                add_issue(required_patient_issues, valid_val_range_check(row, "dl7AqiCh", 0, 4))
            add_issue(required_patient_issues, valid_val_range_check(row, "CDLQI", 0, 30))
        elif 0 < row["ageVisit"] < 4 and not pd.isna(row["dl1qiInf"]):
            dlqi_inf = ["dl1qiInf", "dl2qiInf", "dl3qiInf", "dl4qiInf", "dl5qiInf", "dl6qiInf", "dl7qiInf", "dl8qiInf", "dl9qiInf", "dl10qiInf"]
            for val in dlqi_inf:
                add_issue(required_patient_issues, valid_val_range_check(row, val, 0 ,4))
            add_issue(required_patient_issues, valid_val_range_check(row, "IDQOL", 0, 30))
        if not pd.isna( row["dermSev"] ):
            add_issue(required_patient_issues, valid_val_range_check(row, "dermSev",0, 4))
    return required_patient_issues, optional_patient_issues
