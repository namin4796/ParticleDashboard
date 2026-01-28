# PySensorFlow: Dynamic IoT Control Framework
![License](https://img.shields.io/badge/license-MIT-lightgrey) ![Python](https://img.shields.io/badge/python-3.8%2B-blue) ![Architecture](https://img.shields.io/badge/architecture-Data--Driven-orange)

## Overview
**PySensorFlow** is a hardware-agnostic IoT framework designed to decouple sensor logic from application code. Unlike traditional scripts that hardcode sensor pins and variable names, this project uses a **Role-Based Architecture**.

Users define their hardware setup in a `setup.json` file, assigning abstract roles (e.g., `primary`, `threshold`) to physical sensors. The system dynamically instantiates drivers, generates UI plots, and adapts data logging headers at runtime without requiring any Python code changes.

## Key Engineering Features
* **Role-Based Control Logic:** The dashboard control loop is generic. It acts on abstract roles rather than specific hardware IDs:
    * **`primary`**: The active signal driving the control loop (e.g., LDR, Microphone).
    * **`threshold`**: The hardware input setting the trigger limit (e.g., Potentiometer).
    * **`monitor`**: Passive sensors for visualization only (e.g., Temperature).
* **Dynamic Data Logging:** CSV headers and columns are generated automatically based on the active sensor list. Adding a new sensor to the JSON immediately adds a new column to the log file.
* **Factory Pattern:** Dynamically creates sensor objects and UI curves based on configuration.
* **Testability:** Includes a `unittest.mock` layer that simulates complex hardware signals (sine waves, noise) for CI/CD pipelines.

## Configuration (`setup.json`)
The system behavior is controlled entirely by this JSON file.

```json
{
    "port": "COM3",
    "baud_rate": 9600,
    "sensors": [
        {
            "id": "ldr_sensor",
            "name": "Light Sensor",
            "type": "analog",
            "index": 0,
            "role": "primary",
            "smooth": true,
            "convert_volts": false
        },
        {
            "id": "threshold_pot",
            "name": "Control Knob",
            "type": "analog",
            "index": 1,
            "role": "threshold",
            "smooth": false,
            "convet_volts" : false
        },
        {
            "id": "temp_sensor",
            "name": "Temperature Level",
            "type": "analog",
            "index": 2,
            "role": "monitor",
            "smooth": true,
            "convert_volts": true
        }
    ]
}

## Architecture
```text
PySensorFlow/
├── pysensorflow/       # Core Library
│   ├── core.py         # The Engine (Factory & Parser)
│   └── sensors.py      # Polymorphic Sensor Drivers
├── config/
│   └── setup.json      # User-defined Hardware Map
├── dashboard.py        # GUI Application
└── worker.py           # Threaded Acquisition
