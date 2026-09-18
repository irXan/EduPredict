import os
import json
import pandas as pd

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "edupredict"
COLLECTION = "students"

def export_json(data_path="data/processed/edupredict_master_clean.csv", json_path="data/processed/students.json", limit=500):
    df = pd.read_csv(data_path)
    records = df.head(limit).to_dict(orient="records")
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w") as f:
        json.dump(records, f, indent=2)
    print(f"[MONGO] Exported {len(records)} records to {json_path}")
    print(f"[MONGO] Shell: mongoimport --db {DB_NAME} --collection {COLLECTION} --file {json_path} --jsonArray")
    return records

def sync_to_mongodb(data_path="data/processed/edupredict_master_clean.csv", uri=MONGO_URI, limit=None):
    try:
        from pymongo import MongoClient
    except ImportError:
        print("[MONGO] pymongo not installed. Run: pip install pymongo")
        export_json(data_path)
        return False

    df = pd.read_csv(data_path)
    if limit:
        df = df.head(limit)

    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=3000)
        col = client[DB_NAME][COLLECTION]
        result = col.insert_many(df.to_dict(orient="records"))
        print(f"[MONGO] Inserted {len(result.inserted_ids)} records into {DB_NAME}.{COLLECTION}")

        high_risk = col.count_documents({"dropout_risk": "High"})
        total = col.count_documents({})
        print(f"[MONGO] Total documents: {total}")
        print(f"[MONGO] High risk students: {high_risk}")
        print("[MONGO] Compass: connect to mongodb://localhost:27017/edupredict/students")
        print("[MONGO] Shell sample query:")
        print('  > use edupredict')
        print('  > db.students.find({"dropout_risk": "High"}, {"student_id": 1, "course_id": 1, "gpa": 1}).limit(5)')
        client.close()
        return True
    except Exception as e:
        print(f"[MONGO] Mongo server not reachable ({e}) - exporting JSON for mongoimport instead.")
        export_json(data_path)
        return False

if __name__ == "__main__":
    sync_to_mongodb()