
## Input Data Format

Place all CSV files inside the `/data/` folder.

Required Columns:
- timestamp (date-time)
- kwh (energy consumption)
- building* (auto-generated if missing)
- month* (auto-extracted from filename)

Example filename:
admin_block_2024-01.csv

## Pipeline Workflow

### 1. Data Ingestion & Validation
- Reads all CSVs from `/data/`
- Adds missing `building` and `month`
- Checks `timestamp` and `kwh`
- Logs invalid files
- Combines everything into one DataFrame

### 2. Aggregation Functions
- Daily totals → calculate_daily_totals()
- Weekly totals → calculate_weekly_aggregates()
- Building summaries → building_wise_summary()

### 3. OOP Modeling
Classes:
- MeterReading
- Building
- BuildingManager

These create building-wise final consumption reports.

### 4. Dashboard Generation
The script generates `dashboard.png` with:
- Daily consumption line plot
- Building-wise bar chart
- Scatter plot of all readings

### 5. Output Exports
Generated files:
- cleaned_energy_data.csv
- building_summary.csv
- summary.txt
- dashboard.png

## How to Run

Run the Python script:

