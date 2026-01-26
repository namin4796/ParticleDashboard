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

        # this lets the user choose between Manual Mode and Hardware Mode
        self.chk_hw_sync = QCheckBox("Sync Threshold with Hardware Knob")
        self.chk_hw_sync.setStyleSheet("color: #f1c40f; font-weight: bold;")
        self.chk_hw_sync.setChecked(False) # default is manual mode
        self.layout.addWidget(self.chk_hw_sync)

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

        # save recorded data to csv file
        self.chk_record = QCheckBox("Record to CSV")
        self.chk_record.setStyleSheet("color #aaaaaa;")
        self.layout.addWidget(self.chk_record)

        #log file
        self.csv_file = None
        self.csv_write = None

    # Logic functions
    
    def toggle_acquisition(self):
        #check if button is pressed or released

        if self.btn_start.isChecked():
           arduino_port = "/dev/cu.usbmodem14301"
           self.worker = SensorWorker(arduino_port)
           self.worker.data_signal.connect(self.update_display)
           
           self.btn_start.setText("HALT ACQUISITION")
           self.label.setText(">>> ACQUIRING DATA <<<")
           self.label.setStyleSheet("color: #00e5ff; font-size: 24px; font-weight: bold;")

           #create a unique filename based on current time
           timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
           filename = f"data/particle_log_{timestamp}.csv"

           #if self.chk_record.isChecked():
           self.csv_file = open(filename, mode='w', newline='')
           self.csv_write = csv.writer(self.csv_file)

           self.csv_write.writerow(["Timestamp", "Flux_Value"])
           print(f"DEBUG: Recording to {filename}")
           

           self.worker.start()

        else:
            self.btn_start.setText("INITIALIZE ACQUISITION")
            self.label.setText("SYSTEM READY")
            self.label.setStyleSheet("color: #ecf0f1; font-size: 24px;")
            self.worker.stop()

            if hasattr(self, 'worker'):
                self.worker.stop()
                self.worker.wait()

            #if self.csv_file:
            #    self.csv_file.close()
            #    self.csv_file = None
            #    print("DEBUG: File closed safely.")

    def update_display(self, data_dict):
        """
        Handles data from PySensorFlow Engine
        Received data_dict: {'ldr': 500, 'pot': 200}
        """
        #get data
        ldr_val = data_dict.get('ldr_sensor', 0.0)
        pot_val = data_dict.get('threshold', 500.0)

        #threshold control: manual or synced to hardware
        if self.chk_hw_sync.isChecked():
            #hardware mode: knob overrides GUI
            current_threshold = int(pot_val)
            #update the visual slider to match the knob
            self.threshold_slider.blockSignals(True) # prevent feedback loop
            self.threshold_slider.setValue(current_threshold)
            self.threshold_slider.blockSignals(False)
            self.slider_label.setText(f"Trigger Threshold (HW): {current_threshold}")
        else:
            #manual mode: GUI slider controls threshold
            current_threshold = self.threshold_slider.value()

        #apply smoothing
        if self.chk_smooth.isChecked():
            self.smoothing_buffer.append(ldr_val)
            val_to_plot = sum(self.smoothing_buffer) / len(self.smoothing_buffer)
        else:
            val_to_plot = ldr_val
            self.smoothing_buffer.clear()

        # convert raw adc to voltage
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

        if self.csv_write:
            current_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            self.csv_write.writerow([current_time, display_val])

        #control logic
        #compare vs software slider or hardware potentiometer
        #visualize hardware potentiometer on slider

        if hasattr(self, 'worker') and self.worker.isRunning():

            if val_to_plot < current_threshold and not self.led_is_on:
                self.worker.send_command('H')
                self.led_is_on = True
                self.label.setText(f">>> ALERT: {val_to_plot:.0f}  < {current_threshold}")
                self.label.setStyleSheet("color: #e74c3c; font-size: 24px; font-weight: bold;")

            elif val_to_plot >= current_threshold and self.led_is_on:
                self.worker.send_command('L')
                self.led_is_on = False
                self.label.setText(">>> MONITORING <<<")
                self.label.setStyleSheet("color: #00e5ff; font-size: 24px; font-weight: bold;")


    def update_slider_label(self, value):
        #only update in manual mode
        if not self.chk_hw_sync.isChecked():
            self.slider_label.setText(f"Trigger Threshold: {value}")

    def save_screenshot(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshots/screenshot_{timestamp}.png"
        exporter = pg.exporters.ImageExporter(self.graph_widget.plotItem)

        exporter.parameters()['width'] = 1000
        exporter.export(filename)

        self.label.setText(f"SAVED: {filename}")


