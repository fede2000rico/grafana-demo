import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
import os
import datetime

# Configuration
token = "my-super-secret-auth-token"
org = "grafana_org"
url = "http://influxdb:8086"

client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)
query_api = client.query_api()

def run_query(name, query):
    print(f"\n--- Testing: {name} ---")
    try:
        tables = query_api.query(query, org=org)
        if len(tables) == 0:
            print("RESULT: NO DATA FOUND (0 tables returned)")
            return
        
        row_count = 0
        for table in tables:
            for record in table.records:
                row_count += 1
                if row_count <= 3: # Print first 3 rows
                    print(f"Record: {record.values}")
        print(f"RESULT: {row_count} records found.")
    except Exception as e:
        print(f"RESULT: ERROR - {e}")

# 1. Verify Recap Data Range
query_recap_range = '''
from(bucket: "recap_bucket")
  |> range(start: -10y)
  |> filter(fn: (r) => r["_measurement"] == "recap_data")
  |> keep(columns: ["_time", "job_id", "start", "end"])
  |> limit(n: 5)
'''
run_query("Recap Data Check", query_recap_range)

# 2. Verify Job ID Variable Query
query_job_ids = '''
from(bucket: "recap_bucket")
  |> range(start: -10y)
  |> filter(fn: (r) => r["_measurement"] == "recap_data")
  |> keep(columns: ["job_id"])
  |> group()
  |> distinct(column: "job_id")
  |> limit(n: 5)
'''
run_query("Job ID Variable", query_job_ids)

# 3. Verify Job Start Variable (for a specific ID - replace with one found above)
# We will just grab the first ID found in the previous step if possible, but here we'll use a generic check
query_job_start = '''
from(bucket: "recap_bucket")
  |> range(start: -10y)
  |> filter(fn: (r) => r["_measurement"] == "recap_data")
  |> filter(fn: (r) => r["_field"] == "start")
  |> last()
  |> limit(n: 1)
'''
run_query("Job Start Field Check", query_job_start)

# 4. Verify Run Data (Grafana Bucket)
query_run_data = '''
from(bucket: "grafana_bucket")
  |> range(start: -10y)
  |> filter(fn: (r) => r["_measurement"] == "run_data")
  |> limit(n: 5)
'''
run_query("Run Data Check", query_run_data)
