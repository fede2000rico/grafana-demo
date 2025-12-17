
import csv
import os
import glob
from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# Configuration
INFLUX_URL = "http://influxdb:8086"
INFLUX_TOKEN = "my-super-secret-auth-token"
INFLUX_ORG = "grafana_org"
INFLUX_BUCKET = "grafana_bucket"
INFLUX_RECAP_BUCKET = "recap_bucket"

# Output directory from generating script
CSV_RUNS_DIR = '/data/csv/output_runs'
CSV_RECAP_FILE = '/data/csv/recap.csv'

# Tags for Run Data
RUN_TAGS = ['RecipeId', 'JobId', 'RunId', 'Severity', 'Name']
# Everything else in Run Data is a field (unless empty)

def ensure_buckets(client):
    buckets_api = client.buckets_api()
    org_api = client.organizations_api()
    org = org_api.find_organizations(org=INFLUX_ORG)[0]
    
    for bucket_name in [INFLUX_BUCKET, INFLUX_RECAP_BUCKET]:
        bucket = buckets_api.find_bucket_by_name(bucket_name)
        if bucket:
            print(f"Bucket '{bucket_name}' already exists.")
        else:
            buckets_api.create_bucket(bucket_name=bucket_name, org_id=org.id)
            print(f"Created bucket '{bucket_name}'.")

def parse_time(val):
    try:
        return datetime.fromisoformat(val)
    except:
        return datetime.utcnow() # Fallback

def seed_runs(write_api):
    run_files = glob.glob(os.path.join(CSV_RUNS_DIR, '*.csv'))
    print(f"Found {len(run_files)} run files in {CSV_RUNS_DIR}...")
    
    for file_path in run_files:
        points = []
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    timestamp = parse_time(row['Timestamp'])
                    point = Point("run_data").time(timestamp, WritePrecision.NS)
                    
                    # Add Tags
                    for tag in RUN_TAGS:
                        if row.get(tag):
                            point.tag(tag, row[tag])
                    
                    # Add Fields
                    for k, v in row.items():
                        if k not in RUN_TAGS and k != 'Timestamp':
                            if v and v != '':
                                try:
                                    # Try float/int
                                    point.field(k, float(v))
                                except ValueError:
                                    # Text string
                                    point.field(k, v)
                    
                    points.append(point)
                except Exception as e:
                    print(f"Error parsing row: {e}")
        
        if points:
            # Write in chunks
            chunk_size = 2000
            for i in range(0, len(points), chunk_size):
                write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=points[i:i+chunk_size])
            print(f"  Processed {file_path}: {len(points)} points")

def seed_recap(write_api):
    if not os.path.exists(CSV_RECAP_FILE):
        print(f"Recap file not found: {CSV_RECAP_FILE}")
        return

    print("Seeding recap data...")
    points = []
    with open(CSV_RECAP_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # Use 'start' as timestamp
                timestamp = parse_time(row['start'])
                point = Point("recap_data").time(timestamp, WritePrecision.NS)
                
                # Tags
                point.tag('job_id', row['job_id'])
                point.tag('run_id', row['run_id'])
                point.tag('recipe_id', row['recipe_id'])
                
                # Fields (everything else)
                for k, v in row.items():
                    if k not in ['job_id', 'run_id', 'recipe_id']:
                        if v and v != '':
                            try:
                                point.field(k, float(v))
                            except ValueError:
                                point.field(k, v) # String field like 'all_error_names', 'start', 'end'
                
                points.append(point)
            except Exception as e:
                print(f"Error parsing recap row: {e}")

    if points:
        write_api.write(bucket=INFLUX_RECAP_BUCKET, org=INFLUX_ORG, record=points)
        print(f"Seeded {len(points)} recap rows.")

if __name__ == "__main__":
    print("Starting InfluxDB seed (New Schema)...")
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    
    try:
        ensure_buckets(client)
        write_api = client.write_api(write_options=SYNCHRONOUS)
        
        seed_runs(write_api)
        seed_recap(write_api)
        
        print("Completed.")
    except Exception as e:
        print(f"Fatal Error: {e}")
    finally:
        client.close()
