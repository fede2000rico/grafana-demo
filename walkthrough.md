# Grafana InfluxDB Migration and Dashboard Refactor

## Overview
This workflow tracks the migration of the Grafana backend from MongoDB to InfluxDB v2, the implementation of a new data schema with detailed process parameters, and the refactoring of Grafana dashboards to provide advanced insights.

## Architecture Changes
- **Database**: Replaced MongoDB with **InfluxDB v2.7**.
  - **Bucket Strategy**: 
    - `grafana_bucket`: Stores detailed time-series data (`run_data`) including process parameters (Speed, Torque, Power, etc.) and events.
    - `recap_bucket`: Stores aggregated summary data (`recap_data`) for global analysis (Jobs per recipe, ratios, total errors).
- **Data Ingestion**:
  - `generate_data.py`: Updated to produce `output_runs/{RunId}.csv` and `recap.csv` with a rich schema including simulated "State 4" process deviations and random events.
  - `seed_influx.py`: Completely refactored to be schema-agnostic, dynamically typing fields and handling tags. It now creates buckets automatically and seeds both run details and recap data.

## Grafana Dashboards

### 1. Global Report (`global.json`)
A high-level view of production efficiency and quality.
- **Total Jobs/Errors/Warnings**: Key performance indicators.
- **Jobs per Recipe**: Bar gauge showing production distribution.
- **Recipe vs State Time Heatmap**: A table-based heatmap (colored cells) showing the average time spent in each state (Idle, Production, Cooling) for each Recipe.
- **Process Parameter Analysis**: Heatmap showing the average 50th percentile values for key parameters (Torque, Power, SME, etc.) by Recipe (focusing on Production State 4).

### 2. Job Details (`job.json`)
Deep dive into specific production runs.
- **Job ID Selection**: Dropdown to filter data by Job. The dashboard automatically fetches the job's *start* and *end* times to clip the data exactly to the run duration.
- **Zoom to Job Button**: A dedicated button at the top that updates the dashboard's time range to match the selected Job's duration, ensuring perfect visibility.
- **Operating State Timeline**: Visual timeline of the machine's state (Idle, Production, etc.) over the run.
- **Process Values**: Time-series graphs for:
  - Torque, Power, SME
  - Speed, Pressure
- **State Time Distribution**: Pie chart showing the proportion of time spent in each state for the selected job.
- **Alarm/Event Counts**: Bar gauge summarizing specific warnings and errors that occurred during the run.
- **Annotations**: Visual markers on the timeline for "Error" and "Warning" events.

## Verification
- **Data Generation**: verified `generate_data.py` created CSVs in `data/csv/`.
- **Ingestion**: Verified `seeder` logs showing successful insertion into `grafana_bucket` and `recap_bucket`.
- **Data Integrity**: Verified via Flux query that `recap_data` contains calculated stats and `run_data` contains high-frequency sensor tags.
- **Grafana Provisioning**: Confirmed `Global Report` and `Job Details` are loaded in Grafana via API check.

## Usage
1. **Start Services**: `docker-compose up -d`
2. **Access Grafana**: `http://localhost:3000` (Login is anonymous/Admin).
3. **View Reports**: Navigate to Dashboards > General > Global Report.
4. **View Details**: Click on a Job ID (or select from dropdown) in Job Details.
