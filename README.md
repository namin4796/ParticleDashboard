# Real-Time Particle Flux Dashboard

A multi-threaded data acquisition system built with Python and PyQt6. This application simulates a particle detector connection, visualizes real-time flux intensity, and logs data to CSV for post-processing.

## Features
* **Multithreading:** Dedicated `QThread` worker for non-blocking sensor acquisition.
* **Fault Tolerance:** Simulates sensor noise and handles connection drops (null signal) gracefully.
* **Real-time Visualization:** High-performance plotting using `PyQtGraph`.
* **Data Persistence:** timestamped CSV logging for session data.

## Tech Stack
* **Language:** Python 3.x
* **GUI:** PyQt6
* **Visualization:** PyQtGraph

## How to Run
1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install PyQt6 pyqtgraph
    ```
3.  Run the application:
    ```bash
    python main.py
    ```
