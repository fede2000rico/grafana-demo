
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
CSV_BASE_DIR = '/data/csv'

# Configurable list of columns to strictly treat as Tags (strings)
# All other non-numeric columns will be treated as String Fields or Tags based on logic below
TAG_COLUMNS = ['job_id', 'job_name', 'status', 'step_name', 'log_level']
TIME_COLUMNS = ['start_time', 'timestamp', 'time']

def ensure_bucket(client, bucket_name):
    buckets_api = client.buckets_api()
    bucket = buckets_api.find_bucket_by_name(bucket_name)
    if bucket:
        print(f"Bucket '{bucket_name}' already exists.")
    else:
        org_api = client.organizations_api()
        org = org_api.find_organizations(org=INFLUX_ORG)[0]
        buckets_api.create_bucket(bucket_name=bucket_name, org_id=org.id)
        print(f"Created bucket '{bucket_name}'.")

def parse_time(row):
    for tc in TIME_COLUMNS:
        if tc in row:
            try:
                return datetime.fromisoformat(row[tc])
            except ValueError:
                pass
    return datetime.utcnow()

def write_csv_to_influx(write_api, file_path, measurement_name, bucket_name=INFLUX_BUCKET, extra_tags=None):
    if extra_tags is None:
        extra_tags = {}
        
    print(f"Seeding {measurement_name} from {file_path}...")
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        points = []
        for row in reader:
            try:
                timestamp = parse_time(row)
                
                point = Point(measurement_name).time(timestamp, WritePrecision.NS)
                
                # Add extra tags (e.g. from filename)
                for k, v in extra_tags.items():
                    point.tag(k, v)
                
                for col, val in row.items():
                    # Skip time columns
                    if col in TIME_COLUMNS:
                        continue
                        
                    # Skip empty values
                    if val is None or val == '':
                        continue

                    # Decisions: Tag or Field?
                    if col in TAG_COLUMNS:
                        point.tag(col, val)
                    else:
                        # Try parsing as number
                        try:
                            # Try int first
                            num_val = int(val)
                            point.field(col, num_val)
                        except ValueError:
                            try:
                                num_val = float(val)
                                point.field(col, num_val)
                            except ValueError:
                                # Fallback to string field
                                point.field(col, val)
                
                points.append(point)
            except Exception as e:
                print(f"Error parsing row in {file_path}: {e}")

        if points:
            write_api.write(bucket=bucket_name, org=INFLUX_ORG, record=points)
            print(f"Inserted {len(points)} points into '{measurement_name}' measurement in '{bucket_name}'.")

def seed_recap(write_api):
    recap_file = os.path.join(CSV_BASE_DIR, 'recap.csv')
    if os.path.exists(recap_file):
        write_csv_to_influx(write_api, recap_file, "recap", bucket_name=INFLUX_RECAP_BUCKET)

def seed_job_details(write_api):
    job_files = glob.glob(os.path.join(CSV_BASE_DIR, 'job_details', '*.csv'))
    print(f"Found {len(job_files)} job detail files.")
    
    for file_path in job_files:
        job_id = os.path.basename(file_path).replace('.csv', '')
        # Pass job_id as an extra tag since it might not be in the CSV content
        write_csv_to_influx(write_api, file_path, "job_details", extra_tags={'job_id': job_id})

if __name__ == "__main__":
    print("Starting Dynamic InfluxDB seed...")
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    
    try:
        ensure_bucket(client, INFLUX_RECAP_BUCKET)
        write_api = client.write_api(write_options=SYNCHRONOUS)
        seed_recap(write_api)
        seed_job_details(write_api)
        print("InfluxDB seed completed successfully.")
    except Exception as e:
        print(f"Error seeding InfluxDB: {e}")
    finally:
        client.close()
