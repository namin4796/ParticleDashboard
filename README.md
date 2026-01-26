# PySensorFlow: Modular IoT Control Dashboard
![License](https://img.shields.io/badge/license-MIT-lightgrey) ![Python](https://img.shields.io/badge/python-3.8%2B-blue) ![Qt](https://img.shields.io/badge/GUI-PyQt6-green)

## Overview
**PySensorFlow** is a hardware-agnostic IoT framework designed to decouple sensor logic from application code. Unlike traditional scripts that hardcode sensor pins, this project uses a **Data-Driven Architecture**. 

Users define their hardware setup in a `config.json` file, and the system dynamically instantiates the correct drivers at runtime using the **Factory Pattern**. This allows for the addition of new sensors without modifying the source code.

## Key Engineering Features
* **Hardware Abstraction Layer (HAL):** Polymorphic `BaseSensor` class allows different sensor types (Analog, Digital, I2C) to share a common interface.
* **Design Patterns:**
    * **Factory Pattern:** Dynamically creates sensor objects based on JSON configuration.
    * **Producer-Consumer:** Uses `QThread` and Signals to separate high-frequency serial data acquisition from the GUI rendering loop.
* **Closed-Loop Control:** Implements real-time feedback logic (Sensor vs. Setpoint) to trigger hardware actuators.
* **Testability:** Includes a `unittest.mock` layer that simulates hardware physics (sine waves, noise) for CI/CD pipelines without physical devices.

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
