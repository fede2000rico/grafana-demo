
import pytest
import os
from influxdb_client import InfluxDBClient

# Configuration - reusing environment variables or defaults
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = os.environ.get("INFLUX_TOKEN", "my-super-secret-auth-token")
INFLUX_ORG = "grafana_org"
RECAP_BUCKET = "recap_bucket"
GRAFANA_BUCKET = "grafana_bucket"

@pytest.fixture(scope="module")
def query_api():
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    try:
        yield client.query_api()
    finally:
        client.close()

def test_influx_connection(query_api):
    """Verify that we can connect to InfluxDB and execute a simple query."""
    # Simple query to check bucket existence or simple math
    try:
        tables = query_api.query('buckets()')
        assert len(tables) > 0
    except Exception as e:
        pytest.fail(f"Could not connect to InfluxDB: {e}")

def test_recap_bucket_has_data(query_api):
    """Verify that the recap_bucket has data."""
    query = f'''
    from(bucket: "{RECAP_BUCKET}")
      |> range(start: -365d)
      |> filter(fn: (r) => r["_measurement"] == "recap_data")
      |> limit(n: 1)
    '''
    tables = query_api.query(query)
    assert len(tables) > 0, "Recap bucket is empty"
    assert len(tables[0].records) > 0

def test_grafana_bucket_has_run_data(query_api):
    """Verify that the grafana_bucket has run_data."""
    query = f'''
    from(bucket: "{GRAFANA_BUCKET}")
      |> range(start: -365d)
      |> filter(fn: (r) => r["_measurement"] == "run_data")
      |> limit(n: 1)
    '''
    tables = query_api.query(query)
    assert len(tables) > 0, "Grafana bucket is empty"

def test_job_id_filtering(query_api):
    """Verify that we can filter by JobId (checking the tag case issue)."""
    # 1. Get a distinct Job ID first
    id_query = f'''
    from(bucket: "{RECAP_BUCKET}")
      |> range(start: -365d)
      |> filter(fn: (r) => r["_measurement"] == "recap_data")
      |> keep(columns: ["job_id"])
      |> distinct(column: "job_id")
      |> limit(n: 1)
    '''
    id_tables = query_api.query(id_query)
    assert len(id_tables) > 0
    job_id = id_tables[0].records[0]["_value"]

    # 2. Query run_data using that ID (checking matching logic)
    # Note: run_data uses 'JobId' tag (PascalCase), recap_data uses 'job_id' (snake_case) usually, 
    # but let's verify what filters work. Use the logic from our fix.
    
    run_query = f'''
    from(bucket: "{GRAFANA_BUCKET}")
      |> range(start: -365d)
      |> filter(fn: (r) => r["_measurement"] == "run_data")
      |> filter(fn: (r) => r["JobId"] == "{job_id}")
      |> limit(n: 1)
    '''
    run_tables = query_api.query(run_query)
    assert len(run_tables) > 0, f"No run data found for JobId {job_id}"
