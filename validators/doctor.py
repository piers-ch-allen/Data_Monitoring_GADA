import pandas as pd
import numpy as np
from validators.common_checks import (valid_val_range_check,
                                      non_empty_check,
                                      valid_date_check,
                                      binary_check,
                                      therapy_check,
                                      process_group,
                                      process_group_systemic,
                                      add_issue)

def validate_doctor(
    df,
    visit_type
):
    required_doctor_issues = []
    optional_doctor_issues = []

    for _ , row in df.iterrows():
        if visit_type == 1:
            add_issue(required_doctor_issues, valid_val_range_check(row, "visitInfo", 1, 2))
            add_issue(required_doctor_issues, binary_check(row, "changeCom"))
            add_issue(required_doctor_issues, binary_check(row, "prevChange"))
            if row["prevChange"] == 1:
                add_issue(required_doctor_issues, binary_check(row, "discTher"))
        elif visit_type == 0:
            # Page 1
            binary_values = ["IncPatCons", "Pruritus", "Eczema", "EczemaMorph", "EczemaChronHist", "EarlyAge", "AtopyHist", "Xerosis", "AtypVasc", "KerPil", "OculChange", "RegFind", "PeriAccent", "IncPhoto", "PatFollow"]
            for val in binary_values:
                add_issue(required_doctor_issues, binary_check(row, val))
            coexist_variables = ["Scabies", "ScabiesCO", "SebDerm", "SebDermCO", "ContDerm", "ContDermCO", "Ichthyoses", "IchthyosesCO", "CutTCell", "CutTCellCO", "Psoriasis", "PsoriasisCO", "PhotoDerm", "PhotoDermCO", "BullPemph", "BullPemphCO"]
            counter, x = len(coexist_variables), 0
            while x < counter:
                add_issue(required_doctor_issues, binary_check(row, coexist_variables[x]))
                if row[coexist_variables[x]] == 1:
                    add_issue(required_doctor_issues, binary_check(row, coexist_variables[x]))
                x += 2
            add_issue(required_doctor_issues, valid_val_range_check(row, "AtopyIgE", 0, 2))
            # removed to avoid a huge list of errors currently.
            # add_issue(required_doctor_issues, binary_check(row, "photoYes"))

            # Page 2
            # All in combined section

            # Page 3
            if pd.isna(row["fitzType"]):
                if pd.isna(row["fitzTypeM"]):
                    add_issue(required_doctor_issues, {
                        "ID": row["Subject"],
                        "Issue": "Skin type not selected",
                        "Column": "fitzType"
                    })
                else:
                    add_issue(required_doctor_issues, valid_val_range_check(row, "fitzTypeM", 1, 6))
            else:
                add_issue(required_doctor_issues, valid_val_range_check(row, "fitzType", 1, 6))
            add_issue(required_doctor_issues, valid_val_range_check(row, "DiagAD", 1920, pd.Timestamp.now().year))
            add_issue(required_doctor_issues, valid_val_range_check(row, "TreatAD", 1920, pd.Timestamp.now().year))
            if row["age"] < 7:
                add_issue(optional_doctor_issues, valid_val_range_check(row, "ChildBorn", 1, 2))
                if row["ChildBorn"] == 2:
                    add_issue(optional_doctor_issues, valid_val_range_check(row, "ChildBornPreWe", 0, 100))
            skin_infections = ["EczCox", "EczHer", "Folli", "Furun", "Impet", "MolCont", "Shin", "Wart", "InfOth"]
            sum_infections = 0
            for val in skin_infections:
                if not(pd.isna(row[val])):
                    add_issue(optional_doctor_issues, binary_check(row, val))
                    sum_infections += 1
                    if val == "infOth":
                        add_issue(optional_doctor_issues, non_empty_check(row, "SkinInfOth"))
            if sum_infections == 0 and row["InfNone"] == 0:
                add_issue(required_doctor_issues, {
                    "ID": row["Subject"],
                    "Issue": "Skin infections reporting issue",
                    "Column": "InfNone"
                })
            sensitivity_checks = ["SenDust", "SenPol", "SenMol", "SenFood", "SenAnim"]
            sensitivity_food = ["SenMilk", "SenEgg", "SenWheat", "SenFish", "SenSesam", "SenPean", "SenSoya", "SenOth"]
            sensitivity_animal = ["SenDog", "SenCat", "SenHorse", "SenAnimOth"]
            sensitivity_issues = []
            sens_counter = 0
            for val in sensitivity_checks:
                add_issue(sensitivity_issues, valid_val_range_check(row, val, 0,2))
                if row[val] == 1 and val == "SenFood":
                    counter = 0
                    for val2 in sensitivity_food:
                        if val2 == "SenOth" and not(pd.isna(row[val2])):
                            add_issue(required_doctor_issues, binary_check(row, val2))
                            add_issue(required_doctor_issues, non_empty_check(row, "SenOthTxt"))
                            counter += 1
                        elif not(pd.isna(row[val2])):
                            add_issue(required_doctor_issues, binary_check(row, val2))
                            counter += 1
                    if counter == 0:
                        add_issue(required_doctor_issues, {
                            "ID": row["Subject"],
                            "Issue": "No food sensitisation chosen",
                            "Column": "SenFood"
                        })
                elif row[val] == 1 and val == "SenAnim":
                    counter = 0
                    for val2 in sensitivity_animal:
                        if val2 == "SenAnimOth" and not (pd.isna(row[val2])):
                            add_issue(required_doctor_issues, binary_check(row, val2))
                            add_issue(required_doctor_issues, non_empty_check(row, "SenAnimOthTxt"))
                            counter += 1
                        elif not (pd.isna(row[val2])):
                            add_issue(required_doctor_issues, binary_check(row, val2))
                            counter += 1
                    if counter == 0:
                        add_issue(required_doctor_issues, {
                            "ID": row["Subject"],
                            "Issue": "No food sensitisation chosen",
                            "Column": "SenAnim"
                        })

            # Page 4
            therapies = [
                "LAZproduct", "LABrproduct", "LBAproduct", "LCLproduct", "LDUproduct",
                "LKOproduct", "LKOIntproduct", "LLEBproduct", "LMTproduct", "LMYproduct",
                "LTRproduct", "LUPproduct", "Lothtxt", "Lothtxt2"
            ]
            therapies_dict = {
                therapies[0]: ["LAZstart", "LAZend", "LAZcont", "LAZEffic", "LAZSideEf", "LAZPron"],
                therapies[1]: ["LABstart", "LABend", "LABcont", "LABEffic", "LABSideEf", "LABPron"],
                therapies[2]: ["LBAstart", "LBAend", "LBAcont", "LBAEffic", "LBASideEf", "LBAPron"],
                therapies[3]: ["LCLstart", "LCLend", "LCLcont", "LCLEffic", "LCLSideEf", "LCLPron"],
                therapies[4]: ["LDUstart", "LDUend", "LDUcont", "LDUEffic", "LDUSideEf", "LDUPron"],
                therapies[5]: ["LCOstart", "LCOend", "LCOcont", "LCOEffic", "LCOSideEf", "LCOPron"],
                therapies[6]: ["LCOIntstart", "LCOIntend", "LCOIntcont", "LCOIntEffic", "LCOIntSideEf", "LCOIntPron"],
                therapies[7]: ["LLEBstart", "LLEBend", "LLEBcont", "LLEBEffic", "LLEBSideEf", "LLEBPron"],
                therapies[8]: ["LMTstart", "LMTend", "LMTcont", "LMTEffic", "LMTSideEf", "LMTPron"],
                therapies[9]: ["LMYstart", "LMYend", "LMYcont", "LMYEffic", "LMYSideEf", "LMYPron"],
                therapies[10]: ["LTRstart", "LTRend", "LTRcont", "LTREffic", "LTRSideEf", "LTRPron"],
                therapies[11]: ["LUPstart", "LUPend", "LUPcont", "LUPEffic", "LUPSideEf", "LUPPron"],
                therapies[12]: ["LOTstart", "LOTend", "LOTcont", "LOTEffic", "LOTSideEf", "LOTPron", "LOTName"],
                therapies[13]: ["LOTstart2", "LOTend2", "LOTcont2", "LOTEffic2", "LOTSideEf2", "LOTPron2", "LOName2"]
            }
            therapy_counter = 0
            top_therapy_counter = 0
            for val in therapies:
                if row[val] == 1:
                    temp_issues = therapy_check(row, therapies_dict.get(val))
                    required_doctor_issues.extend(temp_issues)
                    therapy_counter += 1
            if therapy_counter == 0 and pd.isna(row["nosyst"]):
                add_issue(required_doctor_issues, {
                    "ID": row["Subject"],
                    "Issue": "No information on systematic therapies given",
                    "Column": "nosyst"
                })
            elif not(pd.isna(row["nosyst"])):
                add_issue(required_doctor_issues, binary_check(row, "nosyst"))
            therapy_values = ["klass1", "klass2", "klass3", "klass4", "PIbhb", "TAbhb", "UVja"]
            for val in therapy_values:
                if not(pd.isna(row[val])):
                    top_therapy_counter += 1
                    add_issue(required_doctor_issues, binary_check(row, val))
                    if val == "TAbhb" and row[val] == 1:
                        add_issue(required_doctor_issues, non_empty_check(row, "TAbhbPerc"))
                    elif val == "UVja" and row[val] == 1:
                        uv = ["PUVAbh", "UVAbh", "UVBbh", "uvb311bh", "uva1bh", "balnobh"]
                        if sum(row[val] for val in uv) == 0:
                            add_issue(required_doctor_issues, {
                                "ID": row["Subject"],
                                "Issue": "UV therapy not chosen",
                                "Column": "UV...."
                            })
                        add_issue(required_doctor_issues, non_empty_check(row, "UKkudaver"))
            if therapy_counter == 0 and pd.isna(row["noTopT"]):
                add_issue(required_doctor_issues, {
                    "ID": row["Subject"],
                    "Issue": "No information on topical therapies given",
                    "Column": "noTopT"
                })
            elif not (pd.isna(row["noTopT"])):
                add_issue(required_doctor_issues, binary_check(row, "noTopT"))


            # Page 6
            req_systemic_keys = [
                "ABproduct",
                "BAproduct",
                "DUproduct",
                "LEBproduct",
                "TRproduct",
                "UPproduct",
                "BioOthproduct"
            ]
            req_systemic_keys_info = {
                req_systemic_keys[0]: [
                    "AbroDosis", "AbroFreq", "AbroStart", "AbroOn", "AbroStop",
                    "AbroEffect", "AbroIR", "AbroRel", "AbroSE", "AbroCD",
                    "AbroRem", "AbroReasOth", "AbroReasOthTxt"
                ],
                req_systemic_keys[1]: [
                    "BADosis", "BAFreq", "BAStart", "BAOn", "BAStop",
                    "BAEffect", "BAIR", "BARel", "BASE", "BACD",
                    "BARem", "BAReasOth", "BAReasOthTxt"
                ],
                req_systemic_keys[2]: [
                    "DUDosis", "DUFreq", "DUStart", "DUOn", "DUStop",
                    "DUEffect", "DUIR", "DURel", "DUSE", "DUCD",
                    "DURem", "DUReasOth", "DUReasOthTxt"
                ],
                req_systemic_keys[3]: [
                    "LEDosis", "LEFreq", "LEStart", "LEOn", "LEStop",
                    "LEEffect", "LEIR", "LERel", "LESE", "LECD",
                    "LERem", "LEReasOth", "LEReasOthTxt"
                ],
                req_systemic_keys[4]: [
                    "TRDosis", "TRFreq", "TRStart", "TROn", "TRStop",
                    "TREffect", "TRIR", "TRRel", "TRSE", "TRCD",
                    "TRRem", "TRReasOth", "TRReasOthTxt"
                ],
                req_systemic_keys[5]: [
                    "UPDosis", "UPFreq", "UPStart", "UPOn", "UPStop",
                    "UPEffect", "UPIR", "UPRel", "UPSE", "UPCD",
                    "UPRem", "UPReasOth", "UPReasOthTxt"
                ],
                req_systemic_keys[6]: [
                    "BioOthDosis", "BioOthFreq", "BioOthStart", "BioOthOn", "BioOthStop",
                    "BioOthEffect", "BioOthIR", "BioOthRel", "BioOthSE", "BioOthCD",
                    "BioOthRem", "BioOthReasOth", "BioOthReasTxt",
                    "BioOthProdTxt"
                ]
            }
            req_systemic_temp_issue = process_group_systemic(row, req_systemic_keys, req_systemic_keys_info)
            required_doctor_issues.extend(req_systemic_temp_issue)
            opt_systemic_keys = [
                "AZproduct",
                "CLproduct",
                "COproduct",
                "COIntproduct",
                "MTproduct",
                "MYproduct",
                "OthNonBioproduct"
            ]
            opt_systemic_keys_info = {
                opt_systemic_keys[0]: [
                    "AZDosis", "AZFreq", "AZStart", "AZOn", "AZStop", "AZEffect", "AZIR", "AZRel", "AZSE",
                    "AZCD", "AZRem", "AZReasOth", "AZReasOthTxt"
                ],
                opt_systemic_keys[1]: [
                    "CLDosis", "CLFreq", "CLStart", "CLOn", "CLStop", "CLEffect", "CLIR", "CLRel",
                    "CLSE", "CLCD", "CLRem", "CLReasOth", "CLReasOthTxt"
                ],
                opt_systemic_keys[2]: [
                    "CODosis", "COFreq", "COStart", "COOn", "COStop", "COEffect", "COIR", "CORel", "COSE",
                    "COCD", "CORem", "COReasOth", "COReasOthTxt"
                ],
                opt_systemic_keys[3]: [
                    "COIntDosis", "COIntFreq", "COIntStart", "COIntOn", "COIntStop", "COIntEffect",
                    "COIntIR", "COIntRel", "COIntSE", "COIntCD", "COIntRem", "COIntReasOth",
                    "COIntReasOthTxt"
                ],
                opt_systemic_keys[4]: [
                    "MTDosis", "MTFreq", "MTStart", "MTOn", "MTStop", "MTEffect", "MTIR", "MTRel",
                    "MTSE", "MTCD", "MTRem", "MTReasOth", "MTReasOthTxt"
                ],
                opt_systemic_keys[5]: [
                    "MYDosis", "MYFreq", "MYStart", "MYOn", "MYStop", "MYEffect", "MYIR", "MYRel",
                    "MYSE", "MYCD", "MYRem", "MYReasOth", "MYReasOthTxt"
                ],
                opt_systemic_keys[6]: [
                    "OthNDosis", "OthNFreq", "OthNStart", "OthNOn", "OthNStop", "OthNEffect", "OthNIR", "OthNRel",
                    "OthNSE", "OthNCD", "OthNRem", "OthNReasOth", "OthNReasTxt", "OthNProdTxt"
                ]
            }
            opt_systemic_temp_issue = process_group_systemic(row, opt_systemic_keys, opt_systemic_keys_info)
            optional_doctor_issues.extend(opt_systemic_temp_issue)

        if row["Dropout"] == 1 and (
            pd.isna(row["Dropout Status"]) or pd.isna(row["Dropout Comment"]) or pd.isna(row["Dropout Date"])):
                        required_doctor_issues.append({
                            "ID": row["Subject"],
                            "Issue": "Missing Values",
                            "Column": "Dropout"
                    })
        add_issue(required_doctor_issues, valid_date_check(row, "dateVisit"))

        # Page 2 inclusion and page 1 follow-up
        add_issue(required_doctor_issues, valid_val_range_check(row, "flareYear", 0, 200))
        phenotype = ["typeDisc", "typeEryth", "typeExt", "typeEye", "typeHandEcz", "typeHead", "typeFlex",
                         "typeFollic"]
        phenotype_sum = 0
        for val in phenotype:
            if not (pd.isna(row[val])):
                phenotype_sum += row[val]
        if phenotype_sum == 0:
            add_issue(required_doctor_issues, {
                "ID": row["Subject"],
                "Issue": "Phenotype not declared",
                "Column": "type...."
            })
        add_issue(required_doctor_issues, valid_val_range_check(row, "IGA", 0, 4))

        # EASI scoring section
        easi_variables_head = ["hderyth", "hdinf", "hdexc", "hdlich", "%head"]
        easi_variables_arms = ["armeryth", "arminf", "armexc", "armlich", "%arms"]
        easi_variables_trunk = ["treryth", "trinf", "trexc", "trlich", "%trunk"]
        easi_variables_legs = ["legeryth", "leginf", "legexc", "leglich", "%legs"]
        easi_calculation, easi_issues = [0.0,0.0,0.0,0.0], []
        for val in range(0,5):
            if val == 4:
                add_issue(easi_issues, valid_val_range_check(row, easi_variables_head[val],0,6))
                add_issue(easi_issues, valid_val_range_check(row, easi_variables_arms[val],0,6))
                add_issue(easi_issues, valid_val_range_check(row, easi_variables_trunk[val],0,6))
                add_issue(easi_issues, valid_val_range_check(row, easi_variables_legs[val],0,6))
                if row["age"] >= 8:
                    easi_calculation[0] = easi_calculation[0] * row[easi_variables_head[val]] * 0.1
                    easi_calculation[3] = easi_calculation[3] * row[easi_variables_legs[val]] * 0.4
                else:
                    easi_calculation[0] = easi_calculation[0] * row[easi_variables_head[val]] * 0.2
                    easi_calculation[3] = easi_calculation[3] * row[easi_variables_legs[val]] * 0.3
                easi_calculation[1] = easi_calculation[1] * row[easi_variables_arms[val]] * 0.2
                easi_calculation[2] = easi_calculation[2] * row[easi_variables_trunk[val]] * 0.3
            else:
                add_issue(easi_issues, valid_val_range_check(row, easi_variables_head[val],0,3))
                easi_calculation[0] += row[easi_variables_head[val]]
                add_issue(easi_issues, valid_val_range_check(row, easi_variables_arms[val],0,3))
                easi_calculation[1] += row[easi_variables_arms[val]]
                add_issue(easi_issues, valid_val_range_check(row, easi_variables_trunk[val],0,3))
                easi_calculation[2] += row[easi_variables_trunk[val]]
                add_issue(easi_issues, valid_val_range_check(row, easi_variables_legs[val],0,3))
                easi_calculation[3] += row[easi_variables_legs[val]]
        if len(easi_issues) > 0:
            add_issue(required_doctor_issues, {
                "ID": row["Subject"],
                "Issue": "EASI individual measurement issues",
                "Column": "check individual EASI measurements"
            })
        else:
            easi_data = np.array(easi_calculation)
            final_score_check = np.round(np.sum(easi_data),1)
            if not(final_score_check == row["easi"]) and row["age"] >= 8:
                add_issue(required_doctor_issues, {
                    "ID": row["Subject"],
                    "Issue": "EASI issues",
                    "Column": "EASI total score issue"
                })
            elif not(final_score_check == row["easiu8"]) and row["age"] < 8:
                add_issue(required_doctor_issues, {
                    "ID": row["Subject"],
                    "Issue": "EASI under 8 issues",
                    "Column": "EASI under 8 total score issue"
                })

        # Page 5 inclusion and page 2 follow-up
        groups = [
            {
                "pr": "AllergPR",
                "options": ["RHI", "AST", "EYE", "CONT", "EOS", "FOOD", "AllergOth"],
                "name": "Allergic",
                "other_key": "FOOD",
                "other_text": "FOODtype",
                "other_key2": "AllergOth",
                "other_text2": "AllergOthTxt"
            },
            {
                "pr": "CardioPR",
                "options": ["AH", "CV", "HFA", "CHD", "CardioOth"],
                "name": "Cardio",
                "other_key": "CardioOth",
                "other_text": "CardioOthTxt"
            },
            {
                "pr": "GastroPR",
                "options": ["CRO", "ULC", "COE", "GastroOth"],
                "name": "Gastro",
                "other_key": "GastroOth",
                "other_text": "GastroOthTxt"
            },
            {
                "pr": "MalPR",
                "options": ["LYMP", "MYE", "LEUK", "BRAN", "GLI", "NMSkin", "MSkin", "MaligOth"],
                "name": "Malignant",
                "other_key": "MaligOth",
                "other_text": "MaligOthTxt"
            },
            {
                "pr": "MetaBPR",
                "options": ["DIA1", "DIA2", "HYPL", "MetaBOth"],
                "name": "Metabolic",
                "other_key": "MetaBOth",
                "other_text": "MetaBOthTxt"
            },
            {
                "pr": "PsychPR",
                "options": ["DEP", "ANX", "ADHD", "PsychOth"],
                "name": "Psychiatric",
                "other_key": "PsychOth",
                "other_text": "PsychOthTxt"
            }
        ]
        if (visit_type == 1 and row["changeCom"] == 1) or visit_type == 0:
            temp_val = -1
            if pd.isna(row["nocormo"]):
                add_issue(optional_doctor_issues, {
                    "ID": row["Subject"],
                    "Issue": "No value for no comorbidities, page not reached",
                    "Column": "nocormo"
                })
            else:
                temp_val = int(row['nocormo'])
            if temp_val != 0 and temp_val != 1:
                add_issue(optional_doctor_issues, {
                    "ID": row["Subject"],
                    "Issue": "Value for comorbidities is incorrectly assigned",
                    "Column": "nocormo"
                })
            else:
                counter = 0
                for g in groups:
                    temp_count, temp_issues = process_group(row,
                                                 g["pr"], g["options"], g["name"],
                                                 g["other_key"], g["other_text"])
                    for val in temp_issues:
                        required_doctor_issues.append(val)
                    counter += temp_count
                    if "other_key2" in g:
                        temp_count, temp_issues = process_group(row,
                                                 g["pr"], g["options"], g["name"],
                                                 g["other_key"], g["other_text"])
                        for val in temp_issues:
                            required_doctor_issues.append(val)
                            counter += temp_count

                # Simple checks
                if not pd.isna(row["ObesPR"]) and row["ObesPR"] == 1:
                    counter += 1
                    add_issue(required_doctor_issues, binary_check(row, "ObesPR"))

                if not pd.isna(row["OtherPR"]) and row["OtherPR"] == 1:
                    counter += 1
                    add_issue(required_doctor_issues, non_empty_check(row, "OtherPRTxt"))

                if not pd.isna(row["PregPR"]) and row["PregPR"] == 1:
                    counter += 1

                # Final check: no comorbidities selected anywhere
                if counter == 0 and temp_val != 1:
                    add_issue(required_doctor_issues, {
                        "ID": row["Subject"],
                        "Issue": "No comorbidities selected and 'no comorbidity' not indicated",
                        "Column": "....PR"
                    })

        # Page 6 inclusion and page 3 follow-up
        systemic_therapies = [
            "AbroDosis", "BADosis", "DUDosis", "LEDosis", "TRDosis", "UPDosis", "BioOthDosis",
            "AZproduct", "CLproduct", "COproduct", "COIntproduct", "MTproduct", "MYproduct", "OthNonBioproduct"
        ]
        systemic_treat_val = 0
        for val in systemic_therapies:
            systemic_treat_val += 1
        if systemic_treat_val == 0 and pd.isna(row["noCurSyst"]):
                add_issue(required_doctor_issues, {
                    "ID": row["Subject"],
                    "Issue": "No information on current systemic therapies given",
                    "Column": "noCurSyst"
                })

        corticosteroids_therapies = ["COClass1", "COClass2", "COClass3", "COClass4", "Pime", "TAC", "UV", "ReactTreat", "ProTreat"]
        treatment_val = 0
        for val in corticosteroids_therapies:
            if not(pd.isna(row[val])):
                if row[val] != 1:
                    add_issue(optional_doctor_issues, {
                        "ID": row["Subject"],
                        "Issue": "current treatment values inconsistent",
                        "Column": "COC...."
                    })
                else:
                    treatment_val += 1
        if treatment_val == 0 and pd.isna(row["noCurTop"]):
                add_issue(required_doctor_issues, {
                    "ID": row["Subject"],
                    "Issue": "No information on current topical therapies given",
                    "Column": "noCurTop"
                })

        if not (pd.isna(row["TAC"])):
            if row["TAC"] != 1:
                add_issue(optional_doctor_issues, {
                    "ID": row["Subject"],
                    "Issue": "Tac values inconsistent",
                    "Column": "Tac...."
                })
            elif not (row["TACPerc"] == 0.1 or row["TacPerc"] == 0.03):
                add_issue(optional_doctor_issues, {
                    "ID": row["Subject"],
                    "Issue": "Tac dose percentage values inconsistent",
                    "Column": "TacPerc"
                })
        if not (pd.isna(row["UV"])):
            if row["UV"] != 1:
                add_issue(optional_doctor_issues, {
                    "ID": row["Subject"],
                    "Issue": "UV values inconsistent",
                    "Column": "UV...."
                })
            elif row["UV"] == 1:
                uv = ["PUVA", "UVA", "UVB", "UVB311", "UVA1", "Baln"]
                if sum(row[val] for val in uv) == 0:
                    add_issue(optional_doctor_issues, {
                        "ID": row["Subject"],
                        "Issue": "UV selected but therapy not chosen",
                        "Column": "UV...."
                    })
                add_issue(optional_doctor_issues, non_empty_check(row, "UVCumDur"))
        if not (pd.isna(row["ReactTreat"])) and not (pd.isna(row["ProTreat"])):
            add_issue(optional_doctor_issues, {
                "ID": row["Subject"],
                "Issue": "Can't select both reactive and proactive treatment",
                "Column": "....Treat"
            })
        elif not (pd.isna(row["ProTreat"])) and row["ProTreat"] != 1:
            add_issue(optional_doctor_issues, {
                "ID": row["Subject"],
                "Issue": "Invalid value for ProTreat",
                "Column": "ProTreat"
            })
        elif not (pd.isna(row["ReactTreat"])) and row["ReactTreat"] != 1:
            add_issue(optional_doctor_issues, {
                "ID": row["Subject"],
                "Issue": "Invalid value for ReactTreat",
                "Column": "ReactTreat"
            })
    return required_doctor_issues, optional_doctor_issues
