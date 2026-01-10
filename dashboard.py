import sys
import csv
from datetime import datetime
from collections import deque
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QSlider, QCheckBox)

import pyqtgraph as pg
import pyqtgraph.exporters
from worker import SensorWorker

class ParticleDashboard(QMainWindow):
    def __init__(self):
        super().__init__()

        # 1. Window Setup
        self.setWindowTitle("Particle Flux Monitor - v1.0")
        self.resize(900, 600)

        # --- GLOBAL STYLESHEET ---
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                }
            QLabel {
                color: #0aac00;
                font-family: "Consolas", "Courier New", monospace;
                }
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:checked {
                background-color: #e74c3c;
            }
        """)

    
        # 2. The Central Layout (The "Container")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # 3. Add a placeholder widget (Just to see something)
        self.label = QLabel("SYSTEM READY")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Add styles (CSS-like syntax is supported in Qt)
        self.label.setStyleSheet("font-size: 24px; margin-bottom: 10px;")
        self.layout.addWidget(self.label)
       
        #threshold slider
        self.slider_label = QLabel("Trigger Threshold: 500")
        self.layout.addWidget(self.slider_label)

        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setMinimum(0)
        self.threshold_slider.setMaximum(1023)
        self.threshold_slider.setValue(500)

        self.threshold_slider.valueChanged.connect(self.update_slider_label)
        self.layout.addWidget(self.threshold_slider)

        self.led_is_on = False
        # plot widget
        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setBackground('#1e1e1e')
        self.graph_widget.setTitle("LDR Output", color="#bdc3c7", size="12pt")

        styles = {'color': '#bdc3c7', 'font-size': '12px'}
        self.graph_widget.setLabel('left', 'Raw Signal', units='0-1023', **styles)
        self.graph_widget.setLabel('bottom', 'Time Sample', **styles)
        self.graph_widget.showGrid(x=True, y=True, alpha=0.3)

        self.data_buffer =[]
        self.data_line = self.graph_widget.plot([], [], pen=pg.mkPen(color='#00e5ff', width=2))
        self.layout.addWidget(self.graph_widget)


        # Create a control Button
        self.btn_start = QPushButton("INITIALIZE ACQUISITION")
        self.btn_start.setCheckable(True)
        self.btn_start.clicked.connect(self.toggle_acquisition)
        self.layout.addWidget(self.btn_start)

        #Mode switch Raw <-> voltage
        self.chk_volts = QCheckBox("Show as Volts (0-5V)")
        self.chk_volts.setStyleSheet("color: #ecf0f1; font-size: 14px;")
        self.layout.addWidget(self.chk_volts)

        #smoothing switch
        self.chk_smooth = QCheckBox("Enable Signal Smoothing")
        self.chk_smooth.setStyleSheet("color: #ecf0f1; font-size: 14px;")
        self.layout.addWidget(self.chk_smooth)

        self.smoothing_buffer = deque(maxlen=10)

        # save a screenshot button
        self.btn_screenshot = QPushButton("SAVE SNAP")
        self.btn_screenshot.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold")
        self.btn_screenshot.clicked.connect(self.save_screenshot)
        self.layout.addWidget(self.btn_screenshot)

        #log file
        self.csv_file = None
        self.csv_write = None

    # Logic functions
    
    def toggle_acquisition(self):
        #check if button is pressed or released

        if self.btn_start.isChecked():
           arduino_port = "/dev/cu.usbmodem14401"
           self.worker = SensorWorker(arduino_port)
           self.worker.data_signal.connect(self.update_display)
           
           self.btn_start.setText("HALT ACQUISITION")
           self.label.setText(">>> ACQUIRING DATA <<<")
           self.label.setStyleSheet("color: #00e5ff; font-size: 24px; font-weight: bold;")

           #create a unique filename based on current time
           timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
           filename = f"particle_log_{timestamp}.csv"

           self.csv_file = open(filename, mode='w', newline='')
           self.csv_writer = csv.writer(self.csv_file)

           self.csv_writer.writerow(["Timestamp", "Flux_Value"])
           print(f"DEBUG: Recording to {filename}")
           #self.worker.is_running = True
           self.worker.start()

        else:
            self.btn_start.setText("INITIALIZE ACQUISITION")
            self.label.setText("SYSTEM READY")
            self.label.setStyleSheet("color: #ecf0f1; font-size: 24px;")
            self.worker.stop()

            if hasattr(self, 'worker'):
                self.worker.stop()
                self.worker.wait()

            if self.csv_file:
                self.csv_file.close()
                self.csv_file = None
                print("DEBUG: File closed safely.")

    def update_display(self, val):
        #apply smoothing
        if self.chk_smooth.isChecked():
            self.smoothing_buffer.append(val)
            val_to_plot = sum(self.smoothing_buffer) / len(self.smoothing_buffer)
        else:
            val_to_plot = val
            self.smoothing_buffer.clear()

        if self.chk_volts.isChecked():
            display_val = val_to_plot * (5.0 / 1023.0)
            self.graph_widget.setLabel('left', 'Voltage', units='V')
            self.graph_widget.setYRange(0, 5)
        else:
            display_val = val_to_plot
            self.graph_widget.setLabel('left', 'Raw ADC', units='0-1023')
            self.graph_widget.setYRange(0., 1024.)


        #this function receives the data from signal
        self.data_buffer.append(display_val)
        if len(self.data_buffer) > 100:
            self.data_buffer.pop(0)

        self.data_line.setData(self.data_buffer)

        if self.csv_writer:
            current_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            self.csv_writer.writerow([current_time, display_val])

        #control logic
        if hasattr(self, 'worker') and self.worker.isRunning():
            threshold = self.threshold_slider.value()

            if val_to_plot < threshold and not self.led_is_on:
                self.worker.send_command('H')
                self.led_is_on = True
                self.label.setText(">>> ALERT: LOW LIGHT <<<")
                self.label.setStyleSheet("color: #e74c3c; font-size: 24px; font-weight: bold;")

            elif val_to_plot >= threshold and self.led_is_on:
                self.worker.send_command('L')
                self.led_is_on = False
                self.label.setText(">>> ACQUIRING DATA <<<")
                self.label.setStyleSheet("color: #00e5ff; font-size: 24px; font-weight: bold;")


    def update_slider_label(self, value):
        self.slider_label.setText(f"Trigger Threshold: {value}")

    def save_screenshot(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        exporter = pg.exporters.ImageExporter(self.graph_widget.plotItem)

        exporter.parameters()['width'] = 1000
        exporter.export(filename)

        self.label.setText(f"SAVED: {filename}")


