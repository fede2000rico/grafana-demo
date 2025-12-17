
import csv
import random
import os
from datetime import datetime, timedelta
import uuid

# Configuration
NUM_JOBS = 20
RECAP_FILE = 'data/csv/recap.csv'
JOB_DETAILS_DIR = 'data/csv/job_details'

def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

def generate_recap():
    ensure_dir(RECAP_FILE)
    headers = ['job_id', 'job_name', 'status', 'start_time', 'end_time', 'duration_seconds', 'total_records', 'error_count']
    
    jobs = []
    statuses = ['SUCCESS', 'FAILURE', 'WARNING']
    
    start_date = datetime.now() - timedelta(days=30)
    
    with open(RECAP_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        
        for i in range(NUM_JOBS):
            job_id = str(uuid.uuid4())
            job_name = f"Batch_Process_{random.randint(1, 5)}"
            status = random.choices(statuses, weights=[0.7, 0.1, 0.2])[0]
            
            # Randomize time
            start_time = start_date + timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
            duration = random.randint(60, 3600)
            end_time = start_time + timedelta(seconds=duration)
            
            total_records = random.randint(100, 10000)
            error_count = 0
            if status != 'SUCCESS':
                error_count = random.randint(1, 50)
            
            writer.writerow([
                job_id, job_name, status, 
                start_time.isoformat(), end_time.isoformat(), 
                duration, total_records, error_count
            ])
            
            jobs.append({
                'job_id': job_id,
                'start_time': start_time,
                'duration': duration,
                'status': status
            })
            
    return jobs

def generate_job_details(jobs):
    ensure_dir(os.path.join(JOB_DETAILS_DIR, 'dummy'))
    
    detail_headers = ['timestamp', 'step_name', 'metric_a_value', 'metric_b_value', 'log_level', 'message']
    steps = ['Initialization', 'Data Fetching', 'Processing', 'Validation', 'Archiving']
    log_levels = ['INFO', 'DEBUG', 'WARN', 'ERROR']
    
    for job in jobs:
        job_id = job['job_id']
        filename = os.path.join(JOB_DETAILS_DIR, f"{job_id}.csv")
        
        start_time = job['start_time']
        duration = job['duration']
        step_interval = duration / len(steps)
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(detail_headers)
            
            current_time = start_time
            
            for step in steps:
                # Generate multiple entries per step
                num_entries = random.randint(5, 15)
                for _ in range(num_entries):
                    current_time += timedelta(seconds=random.randint(1, int(step_interval/num_entries)))
                    
                    metric_a = random.uniform(0, 100)
                    metric_b = random.uniform(0, 50)
                    
                    log_level = 'INFO'
                    if job['status'] in ['FAILURE', 'WARNING'] and random.random() < 0.1:
                         log_level = 'ERROR' if job['status'] == 'FAILURE' else 'WARN'
                    
                    message = f"Executing {step} - processed chunk {random.randint(1, 100)}"
                    
                    writer.writerow([
                        current_time.isoformat(),
                        step,
                        f"{metric_a:.2f}",
                        f"{metric_b:.2f}",
                        log_level,
                        message
                    ])

if __name__ == "__main__":
    print("Generating data...")
    jobs_data = generate_recap()
    generate_job_details(jobs_data)
    print("Data generation complete.")
