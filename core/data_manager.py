"""
Sensor Data Ingestion, Dataset Management, and Real-Time Telemetry Streaming Module
Implements:
- Industrial dataset loader (Testbed Motor-Pump, NASA IMS Bearing, Helical Gearbox)
- Strict CSV validation engine with schema, bounds, and missing value checks
- Real-time telemetry streaming simulation with playback controls (play, pause, speed, seek)
- Dynamic anomaly injection for live testing and demonstration
"""

import os
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

class DataManager:
    REQUIRED_COLUMNS = [
        "timestamp", "vibration_radial", "vibration_axial", 
        "temperature", "current", "speed_rpm"
    ]
    OPTIONAL_COLUMNS = ["operating_hours", "pressure", "acoustic_db"]

    PHYSICAL_BOUNDS = {
        "vibration_radial": (0.0, 50.0),    # mm/s
        "vibration_axial": (0.0, 50.0),     # mm/s
        "temperature": (-10.0, 180.0),      # °C
        "current": (0.0, 100.0),            # A
        "speed_rpm": (0.0, 15000.0),        # RPM
        "pressure": (0.0, 100.0),           # bar
        "acoustic_db": (0.0, 160.0)         # dB
    }

    def __init__(self, datasets_dir: str = "datasets"):
        self.datasets_dir = datasets_dir
        self.active_dataset_name = "testbed_motor_pump_run.csv"
        self.active_df: Optional[pd.DataFrame] = None
        self.current_index = 0
        self.is_streaming = True
        self.playback_speed = 1.0
        self.injected_anomaly: Optional[str] = None
        
        # Available equipment registry
        self.machines = [
            {
                "id": "MTR-PUMP-5.5KW-01",
                "name": "5.5 kW Induction Motor - Centrifugal Pump Unit #1",
                "type": "Motor-Pump Assembly",
                "rated_power": "5.5 kW / 400V / 50 Hz",
                "nominal_rpm": 1440,
                "dataset": "testbed_motor_pump_run.csv",
                "location": "Pumping Station Bay 3",
                "status": "Online"
            },
            {
                "id": "IMS-BEARING-BENCH-02",
                "name": "NASA IMS Bearing Endurance Testbed #2",
                "type": "Rotating Shaft Bearing Testbed",
                "rated_power": "7.5 kW Drive",
                "nominal_rpm": 2000,
                "dataset": "ims_bearing_degradation.csv",
                "location": "Prognostics R&D Lab",
                "status": "Online"
            },
            {
                "id": "GBX-HELICAL-03",
                "name": "Industrial Helical Reduction Gearbox #3",
                "type": "Single-Stage Helical Gearbox",
                "rated_power": "11.0 kW Drive",
                "nominal_rpm": 1440,
                "dataset": "gearbox_unbalance_run.csv",
                "location": "Extruder Line Alpha",
                "status": "Online"
            }
        ]
        self.active_machine_id = self.machines[0]["id"]
        self.load_dataset(self.active_dataset_name)

    def load_dataset(self, filename: str) -> bool:
        """Load specified CSV dataset from datasets directory."""
        path = os.path.join(self.datasets_dir, filename)
        if not os.path.exists(path):
            return False
        
        try:
            df = pd.read_csv(path)
            # Ensure optional columns exist
            for col in self.OPTIONAL_COLUMNS:
                if col not in df.columns:
                    if col == "pressure":
                        df[col] = 4.0
                    elif col == "acoustic_db":
                        df[col] = 35.0
                    elif col == "operating_hours":
                        df[col] = [1200.0 + i for i in range(len(df))]
                        
            self.active_df = df
            self.active_dataset_name = filename
            self.current_index = 0
            return True
        except Exception as e:
            print(f"Error loading dataset {filename}: {e}")
            return False

    def validate_csv(self, file_content_str: str) -> Dict[str, Any]:
        """
        Strict validation of user-uploaded sensor CSV:
        - Validates headers against REQUIRED_COLUMNS
        - Validates data types
        - Checks for missing/null values
        - Enforces physical realistic bounds
        """
        import io
        try:
            df = pd.read_csv(io.StringIO(file_content_str))
        except Exception as e:
            return {
                "valid": False,
                "error": f"Failed to parse CSV format: {str(e)}",
                "row_count": 0
            }

        # Check required columns
        missing_cols = [c for c in self.REQUIRED_COLUMNS if c not in df.columns]
        if missing_cols:
            return {
                "valid": False,
                "error": f"Missing required sensor columns: {', '.join(missing_cols)}. Expected columns: {', '.join(self.REQUIRED_COLUMNS)}",
                "row_count": len(df)
            }

        if len(df) == 0:
            return {"valid": False, "error": "Dataset is empty (0 rows).", "row_count": 0}

        # Check numeric conversions and bounds
        errors = []
        for col in self.REQUIRED_COLUMNS[1:]:  # skip timestamp
            if not pd.api.types.is_numeric_dtype(df[col]):
                try:
                    df[col] = pd.to_numeric(df[col])
                except Exception:
                    errors.append(f"Column '{col}' contains non-numeric values.")
                    continue
            
            # Check nulls
            null_count = df[col].isnull().sum()
            if null_count > 0:
                errors.append(f"Column '{col}' has {null_count} missing (NaN) values.")

            # Check bounds
            if col in self.PHYSICAL_BOUNDS:
                low, high = self.PHYSICAL_BOUNDS[col]
                out_of_bounds = ((df[col] < low) | (df[col] > high)).sum()
                if out_of_bounds > 0:
                    errors.append(f"Column '{col}' contains {out_of_bounds} values outside physical range [{low}, {high}].")

        if errors:
            return {
                "valid": False,
                "error": "; ".join(errors[:3]) + (f" (and {len(errors)-3} more issues)" if len(errors) > 3 else ""),
                "row_count": len(df)
            }

        return {
            "valid": True,
            "error": None,
            "row_count": len(df),
            "columns": list(df.columns),
            "time_range": f"{df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}",
            "message": f"Dataset validated successfully: {len(df)} telemetry snapshots verified."
        }

    def save_uploaded_dataset(self, filename: str, content: str) -> Dict[str, Any]:
        """Validate and save user-uploaded sensor dataset."""
        val_res = self.validate_csv(content)
        if not val_res["valid"]:
            return val_res
        
        target_path = os.path.join(self.datasets_dir, filename)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        self.load_dataset(filename)
        return {
            "valid": True,
            "message": f"Uploaded dataset '{filename}' loaded successfully.",
            "row_count": val_res["row_count"]
        }

    def select_machine(self, machine_id: str) -> Optional[Dict[str, Any]]:
        """Select active equipment machine and switch its dataset."""
        for m in self.machines:
            if m["id"] == machine_id:
                self.active_machine_id = machine_id
                self.load_dataset(m["dataset"])
                return m
        return None

    def get_current_machine(self) -> Dict[str, Any]:
        """Return metadata for currently selected machine."""
        for m in self.machines:
            if m["id"] == self.active_machine_id:
                return m
        return self.machines[0]

    def get_next_telemetry_frame(self) -> Dict[str, Any]:
        """
        Advance streaming index and return current telemetry record.
        Applies any dynamic live anomaly injection.
        """
        if self.active_df is None or len(self.active_df) == 0:
            return {}
        
        row = self.active_df.iloc[self.current_index].to_dict()
        
        if self.is_streaming:
            self.current_index = (self.current_index + 1) % len(self.active_df)

        # Apply anomaly injection if triggered by user
        if self.injected_anomaly == "bearing_spall":
            row["vibration_radial"] = round(row.get("vibration_radial", 0.8) + 3.8, 3)
            row["temperature"] = round(row.get("temperature", 42.0) + 24.0, 2)
            row["acoustic_db"] = round(row.get("acoustic_db", 35.0) + 25.0, 1)
        elif self.injected_anomaly == "unbalance":
            row["vibration_radial"] = round(row.get("vibration_radial", 0.8) + 2.5, 3)
            row["vibration_axial"] = round(row.get("vibration_axial", 0.4) + 1.2, 3)
        elif self.injected_anomaly == "thermal_overload":
            row["temperature"] = round(row.get("temperature", 42.0) + 40.0, 2)
            row["current"] = round(row.get("current", 8.5) + 4.5, 2)

        return row

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return recent historical telemetry records up to limit."""
        if self.active_df is None:
            return []
        
        end_idx = max(1, self.current_index)
        start_idx = max(0, end_idx - limit)
        sub_df = self.active_df.iloc[start_idx:end_idx]
        return sub_df.to_dict(orient="records")

    def seek_frame(self, index: int) -> int:
        """Seek to a specific frame in dataset."""
        if self.active_df is not None and len(self.active_df) > 0:
            self.current_index = max(0, min(len(self.active_df) - 1, index))
        return self.current_index

    def inject_anomaly(self, anomaly_type: Optional[str]) -> str:
        """Inject or clear live simulated anomaly."""
        self.injected_anomaly = anomaly_type
        return f"Anomaly state set to: {anomaly_type or 'None (Cleared)'}"

    def reset_demo(self) -> Dict[str, Any]:
        """Restore initial nominal demonstration state."""
        self.injected_anomaly = None
        self.current_index = 0
        self.is_streaming = True
        self.playback_speed = 1.0
        self.active_machine_id = self.machines[0]["id"]
        # Reload default machine's nominal dataset
        machine = self.get_current_machine()
        self.load_dataset(machine.get("dataset", "testbed_motor_pump_run.csv"))
        return {
            "success": True,
            "message": "Demonstration state reset to nominal baseline.",
            "current_index": self.current_index,
            "active_anomaly": None,
            "is_streaming": True,
            "playback_speed": 1.0,
            "machine": machine
        }

    def list_available_datasets(self) -> List[Dict[str, Any]]:
        """Return metadata for all available datasets in datasets/ directory."""
        datasets = []
        if not os.path.exists(self.datasets_dir):
            return datasets

        descriptions = {
            "testbed_motor_pump_run.csv": {
                "name": "5.5 kW Motor-Pump Baseline",
                "desc": "Synchronized laboratory baseline run covering nominal 5.5 kW motor and centrifugal pump operations."
            },
            "ims_bearing_degradation.csv": {
                "name": "NASA IMS Bearing Run-to-Failure",
                "desc": "Accelerated endurance bearing wear dataset exhibiting inner-race spalling (BPFI) and harmonic growth."
            },
            "gearbox_unbalance_run.csv": {
                "name": "Industrial Helical Gearbox Run",
                "desc": "Helical reduction gearbox run-time telemetry capturing rotational 1X unbalance and harmonic distortion."
            }
        }

        for fname in sorted(os.listdir(self.datasets_dir)):
            if fname.endswith(".csv"):
                fpath = os.path.join(self.datasets_dir, fname)
                try:
                    file_size = os.path.getsize(fpath)
                    size_kb = round(file_size / 1024.0, 1)
                    # Quick read of first row and length
                    df_sample = pd.read_csv(fpath)
                    row_count = len(df_sample)
                    cols = list(df_sample.columns)
                    t_range = f"{df_sample['timestamp'].iloc[0]} to {df_sample['timestamp'].iloc[-1]}" if "timestamp" in df_sample.columns and row_count > 0 else "N/A"
                    
                    meta = descriptions.get(fname, {
                        "name": fname.replace("_", " ").replace(".csv", "").title(),
                        "desc": f"Industrial sensor telemetry stream ({row_count} rows, {len(cols)} channels)."
                    })

                    datasets.append({
                        "name": meta["name"],
                        "description": meta["desc"],
                        "filename": fname,
                        "size_bytes": file_size,
                        "size_kb": size_kb,
                        "row_count": row_count,
                        "columns": cols,
                        "time_range": t_range,
                        "is_active": (fname == self.active_dataset_name)
                    })
                except Exception as e:
                    datasets.append({
                        "name": fname,
                        "description": f"Error reading dataset: {str(e)}",
                        "filename": fname,
                        "size_bytes": 0,
                        "size_kb": 0.0,
                        "row_count": 0,
                        "columns": [],
                        "time_range": "Unreadable",
                        "is_active": False
                    })
        return datasets
