
import csv
import os
import random
import uuid
from datetime import datetime, timedelta
import numpy as np

# Configuration
OUTPUT_DIR = 'data/csv/output_runs'
RECAP_FILE = 'data/csv/recap.csv'
NUM_JOBS = 10
RUNS_PER_JOB = 3
RECIPES = ['Recipe_A', 'Recipe_B', 'Recipe_C']

# Process Parameters
PARAMS = [
    'Active_ActProcVal_All_MainDrive_ActSpeed',
    'Active_ActProcVal_All_MainDrive_ActTorquePercent',
    'Active_ActProcVal_All_MainDrive_ActThroughput',
    'Active_ActProcVal_All_MainDrive_ActPower',
    'Active_ActProcVal_All_MainDrive_ActSME',
    'Active_ActProcVal_All_Endplate_ActPressure'
]

# States
STATE_IDLE = 0
STATE_PRODUCTION = 4
STATES = [0, 1, 2, 3, 4, 5] # Simplified state model

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def generate_run_data(run_id, job_id, recipe_id, start_time):
    duration_minutes = random.randint(30, 120)
    end_time = start_time + timedelta(minutes=duration_minutes)
    
    rows = []
    current_time = start_time
    current_state = STATE_IDLE
    
    warnings = 0
    errors = 0
    warning_names = []
    error_names = []
    
    state_times = {s: 0.0 for s in STATES}
    transition_count = 0
    exits_from_prod = 0
    
    # buffers for aggregation
    param_values_state4 = {p: [] for p in PARAMS}
    
    while current_time < end_time:
        # Simulate State Logic
        if random.random() < 0.05:
            new_state = random.choice(STATES)
            if new_state != current_state:
                transition_count += 1
                if current_state == STATE_PRODUCTION:
                    exits_from_prod += 1
                current_state = new_state
        
        # 1. Process Parameter Row
        row = {
            'Timestamp': current_time.isoformat(),
            'RecipeId': recipe_id,
            'JobId': job_id,
            'RunId': run_id,
            'Active_State_General_StaOperatingState': float(current_state),
            'Name': '', 'Text': '', 'Severity': ''
        }
        
        # Generate Param Values based on state
        for param in PARAMS:
            val = 0.0
            if current_state == STATE_PRODUCTION:
                base = 100.0 if 'Speed' in param else 50.0
                val = base + np.random.normal(0, 5)
                param_values_state4[param].append(val)
            elif current_state != STATE_IDLE:
                val = np.random.normal(10, 2)
            
            row[param] = round(val, 2)
            
        rows.append(row)
        
        # Track Time
        state_times[current_state] += 1.0 # Assuming 1 sec steps
        
        # 2. Random Event Row
        if random.random() < 0.01:
            severity = 'Warning' if random.random() < 0.8 else 'Error'
            name = f"{severity}_{random.randint(1, 10)}"
            text = f"Simulated {severity} occurred"
            
            event_row = {
                'Timestamp': current_time.isoformat(),
                'RecipeId': recipe_id,
                'JobId': job_id,
                'RunId': run_id,
                'Active_State_General_StaOperatingState': float(current_state),
                'Name': name,
                'Text': text,
                'Severity': severity
            }
            # Params are empty for events
            for param in PARAMS:
                event_row[param] = ''
            
            rows.append(event_row)
            
            if severity == 'Warning':
                warnings += 1
                if name not in warning_names: warning_names.append(name)
            else:
                errors += 1
                if name not in error_names: error_names.append(name)

        current_time += timedelta(seconds=1)

    # Calculate Recap Stats
    total_duration_s = (end_time - start_time).total_seconds()
    duration_h = total_duration_s / 3600.0
    prod_time_s = state_times[STATE_PRODUCTION]
    prod_time_h = prod_time_s / 3600.0
    idle_time_h = state_times[STATE_IDLE] / 3600.0
    
    recap_row = {
        'job_id': job_id,
        'run_id': run_id,
        'recipe_id': recipe_id,
        'start': start_time.isoformat(),
        'end': end_time.isoformat(),
        'duration_h': round(duration_h, 4),
        'production_time_h': round(prod_time_h, 4),
        'idle_time_h': round(idle_time_h, 4),
        'production_ratio': round(prod_time_s / total_duration_s if total_duration_s > 0 else 0, 4),
        'transition_count': transition_count,
        'exits_from_prod_state': exits_from_prod,
        'warnings': warnings,
        'errors': errors,
        'all_warning_names': "|".join(warning_names),
        'all_error_names': "|".join(error_names)
    }
    
    # State Times
    for s in STATES:
        recap_row[f"state_{s}_time_s"] = state_times[s]
        
    # Param Stats
    for param in PARAMS:
        vals = param_values_state4[param]
        if vals:
             recap_row[f"state4_{param}_p50"] = round(np.median(vals), 2)
             recap_row[f"state4_{param}_max"] = round(np.max(vals), 2)
        else:
             recap_row[f"state4_{param}_p50"] = 0
             recap_row[f"state4_{param}_max"] = 0

    return rows, recap_row, end_time

def main():
    ensure_dir(OUTPUT_DIR)
    
    # Clean old files
    if os.path.exists(RECAP_FILE): os.remove(RECAP_FILE)
    for f in os.listdir(OUTPUT_DIR):
        os.remove(os.path.join(OUTPUT_DIR, f))

    all_recap_rows = []
    run_counter = 1
    
    current_time = datetime.now() - timedelta(days=2) # Start 2 days ago

    print("Generating data...")
    
    for i in range(NUM_JOBS):
        job_id = str(uuid.uuid4())
        recipe = random.choice(RECIPES)
        
        for j in range(RUNS_PER_JOB):
            run_id = run_counter
            print(f"  Job {i+1}/{NUM_JOBS} - Run {run_id} ({recipe})")
            
            run_rows, recap_row, next_time = generate_run_data(run_id, job_id, recipe, current_time)
            
            # Write Run CSV
            run_file = os.path.join(OUTPUT_DIR, f"{run_id}.csv")
            with open(run_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=run_rows[0].keys())
                writer.writeheader()
                writer.writerows(run_rows)
            
            all_recap_rows.append(recap_row)
            
            current_time = next_time + timedelta(minutes=random.randint(10, 60)) # Gap between runs
            run_counter += 1

    # Write Recap CSV
    if all_recap_rows:
        with open(RECAP_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=all_recap_rows[0].keys())
            writer.writeheader()
            writer.writerows(all_recap_rows)
            
    print(f"Data generation complete. Runs in '{OUTPUT_DIR}', Recap in '{RECAP_FILE}'.")

if __name__ == "__main__":
    main()
