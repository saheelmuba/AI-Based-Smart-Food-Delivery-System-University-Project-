import os
import json
import pickle
import pandas as pd


def load_csv(path):
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path)


def load_json(path):
    if not os.path.exists(path):
        return pd.DataFrame()
    with open(path, "r", encoding="utf-8") as reader:
        data = json.load(reader)
    return pd.json_normalize(data)


def load_xlsx(path):
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_excel(path, engine="openpyxl")


def load_pickle(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as fh:
        return pickle.load(fh)


def infer_medical_reference_data():
    csv_path = os.path.join(os.getcwd(), "datasets", "medical_records.csv")
    json_path = os.path.join(os.getcwd(), "datasets", "medical_records.json")
    xlsx_path = os.path.join(os.getcwd(), "datasets", "medical_records.xlsx")
    csv_frame = load_csv(csv_path)
    json_frame = load_json(json_path)
    xlsx_frame = load_xlsx(xlsx_path)
    frames = [frame for frame in [csv_frame, json_frame, xlsx_frame] if not frame.empty]
    if not frames:
        return pd.DataFrame()
    merged = pd.concat(frames, ignore_index=True, sort=False)
    return merged.drop_duplicates()


def load_medical_dataset():
    medical_df = infer_medical_reference_data()
    if medical_df.empty:
        medical_df = pd.DataFrame(
            [
                {
                    "patient_name": "Ava Patel",
                    "age": 34,
                    "condition": "Hypertension",
                    "visit_date": "2026-05-01",
                    "physician": "Dr. Lee",
                    "notes": "Adjusted medication and recommended follow-up in 4 weeks.",
                },
                {
                    "patient_name": "Miguel Diaz",
                    "age": 52,
                    "condition": "Type 2 Diabetes",
                    "visit_date": "2026-05-06",
                    "physician": "Dr. Ahmad",
                    "notes": "Reviewed glucose log and optimized diet plan.",
                },
                {
                    "patient_name": "Sofia Nguyen",
                    "age": 27,
                    "condition": "Asthma",
                    "visit_date": "2026-05-08",
                    "physician": "Dr. Kim",
                    "notes": "Updated inhaler regimen and education materials.",
                },
            ]
        )
    return medical_df
