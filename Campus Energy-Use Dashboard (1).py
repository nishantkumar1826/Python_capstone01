import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime

# ================== PATH SETUP ==================

# Folder jahan yeh .py file rakha hai
BASE_DIR = Path(__file__).resolve().parent


# ============================================================
# TASK 1 — DATA INGESTION & VALIDATION
# ============================================================

def load_energy_data(data_folder="data"):
    """
    Reads all CSV files from data_folder (relative to this script)
    and returns a combined DataFrame plus a list of log messages.
    """
    data_path = (BASE_DIR / data_folder).resolve()
    logs = []

    if not data_path.exists():
        raise FileNotFoundError(f"Data folder not found: {data_path}")

    all_rows = []

    print("Searching for CSV files in:", data_path)
    csv_files = list(data_path.glob("*.csv"))
    print("CSV files found:", [f.name for f in csv_files])

    for file in csv_files:
        try:
            df = pd.read_csv(file, on_bad_lines="skip")

            # filename example: admin_block_2024-01.csv
            parts = file.stem.split("_")
            building_name = parts[0] if parts else "Unknown"
            month_from_name = parts[-1] if parts else "Unknown"

            if "building" not in df.columns:
                df["building"] = building_name
            if "month" not in df.columns:
                df["month"] = month_from_name

            if "timestamp" not in df.columns or "kwh" not in df.columns:
                logs.append(f"Skipped {file.name}: missing 'timestamp' or 'kwh'")
                continue

            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
            df = df.dropna(subset=["timestamp", "kwh"])

            all_rows.append(df)

        except Exception as e:
            logs.append(f"Error reading {file.name}: {e}")

    if len(all_rows) == 0:
        raise ValueError(
            "No valid CSV files found in data folder. "
            "Ensure .csv files have 'timestamp' and 'kwh' columns."
        )

    df_combined = pd.concat(all_rows, ignore_index=True)
    return df_combined, logs


# ============================================================
# TASK 2 — CORE AGGREGATION FUNCTIONS
# ============================================================

def calculate_daily_totals(df):
    """Daily totals for the whole campus."""
    df = df.set_index("timestamp")
    return df.resample("D")["kwh"].sum()


def calculate_weekly_aggregates(df):
    """Weekly totals for the whole campus."""
    df = df.set_index("timestamp")
    return df.resample("W")["kwh"].sum()


def building_wise_summary(df):
    """
    Summary per building:
    mean, min, max, total consumption.
    """
    summary = df.groupby("building")["kwh"].agg(["mean", "min", "max", "sum"])
    summary.rename(columns={"sum": "total_kwh"}, inplace=True)
    return summary


# ============================================================
# TASK 3 — OBJECT-ORIENTED MODELING
# ============================================================

class MeterReading:
    def __init__(self, timestamp, kwh):
        self.timestamp = timestamp
        self.kwh = kwh


class Building:
    def __init__(self, name):
        self.name = name
        self.meter_readings = []

    def add_reading(self, reading: MeterReading):
        self.meter_readings.append(reading)

    def calculate_total_consumption(self):
        return sum(r.kwh for r in self.meter_readings)

    def generate_report(self):
        total = self.calculate_total_consumption()
        return f"{self.name}: Total Consumption = {total:.2f} kWh"


class BuildingManager:
    def __init__(self):
        self.buildings = {}

    def load_from_dataframe(self, df):
        for _, row in df.iterrows():
            bname = row["building"]
            if bname not in self.buildings:
                self.buildings[bname] = Building(bname)

            reading = MeterReading(row["timestamp"], row["kwh"])
            self.buildings[bname].add_reading(reading)

    def generate_all_reports(self):
        return [b.generate_report() for b in self.buildings.values()]


# ============================================================
# TASK 4 — VISUALIZATION DASHBOARD
# ============================================================

def generate_dashboard(df, daily_totals, weekly_totals, summary):
    """
    Creates a PNG with:
    - Line: daily campus consumption
    - Bar: total usage per building
    - Scatter: individual readings (time vs kWh)
    Saved as dashboard.png in the same folder as this script.
    """
    fig, axes = plt.subplots(3, 1, figsize=(12, 14))

    # 1. Line plot of daily totals (whole campus)
    axes[0].plot(daily_totals.index, daily_totals.values)
    axes[0].set_title("Daily Campus Electricity Consumption")
    axes[0].set_ylabel("kWh")

    # 2. Bar chart of total usage per building
    x_positions = range(len(summary.index))
    axes[1].bar(x_positions, summary["total_kwh"])
    axes[1].set_title("Total Consumption per Building")
    axes[1].set_ylabel("kWh")
    axes[1].set_xticks(x_positions)
    axes[1].set_xticklabels(summary.index, rotation=45, ha="right")

    # 3. Scatter: timestamp vs kWh (all readings)
    axes[2].scatter(df["timestamp"], df["kwh"], s=8)
    axes[2].set_title("Individual Meter Readings Over Time")
    axes[2].set_ylabel("kWh")
    axes[2].set_xlabel("Time")

    plt.tight_layout()
    out_path = BASE_DIR / "dashboard.png"
    plt.savefig(out_path)
    plt.close()
    print(f"Saved dashboard: {out_path}")


# ============================================================
# TASK 5 — EXPORT & SUMMARY REPORT
# ============================================================

def write_outputs(df, summary, daily_totals, weekly_totals):
    cleaned_path = BASE_DIR / "cleaned_energy_data.csv"
    summary_path = BASE_DIR / "building_summary.csv"
    report_path = BASE_DIR / "summary.txt"

    # 1. Export cleaned dataset
    df.to_csv(cleaned_path, index=False)

    # 2. Export building summary
    summary.to_csv(summary_path)

    # 3. Text summary report
    total_consumption = df["kwh"].sum()
    highest_building = summary["total_kwh"].idxmax()
    peak_row = df.loc[df["kwh"].idxmax()]
    peak_time = peak_row["timestamp"]
    peak_value = peak_row["kwh"]

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("CAMPUS ENERGY SUMMARY REPORT\n")
        f.write("-------------------------------------\n")
        f.write(f"Total Campus Consumption: {total_consumption:.2f} kWh\n")
        f.write(f"Highest-Consuming Building: {highest_building}\n")
        f.write(f"Peak Load: {peak_value:.2f} kWh at {peak_time}\n")
        f.write("\nDaily Trend (first 5 days):\n")
        f.write(str(daily_totals.head()))
        f.write("\n\nWeekly Trend (first 5 weeks):\n")
        f.write(str(weekly_totals.head()))
        f.write("\n")

    print(f"Saved cleaned data: {cleaned_path}")
    print(f"Saved summary CSV: {summary_path}")
    print(f"Saved text report: {report_path}")


# ============================================================
# MAIN EXECUTION PIPELINE
# ============================================================

def main():
    print("=== Campus Energy Dashboard ===")

    # Load and validate data
    df, logs = load_energy_data("data")

    print("\nIngestion logs:")
    for log in logs:
        print(" -", log)

    # Aggregations
    daily = calculate_daily_totals(df)
    weekly = calculate_weekly_aggregates(df)
    summary = building_wise_summary(df)

    # OOP building objects
    manager = BuildingManager()
    manager.load_from_dataframe(df)
    reports = manager.generate_all_reports()

    print("\nBuilding Reports:")
    for r in reports:
        print(" -", r)

    # Plots
    generate_dashboard(df, daily, weekly, summary)

    # Exports
    write_outputs(df, summary, daily, weekly)

    print("\nAll files generated in:", BASE_DIR)


if __name__ == "__main__":
    main()
