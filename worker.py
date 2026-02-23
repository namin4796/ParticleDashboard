#import serial
#import serial.tools.list_ports
import time
from PyQt6.QtCore import QThread, pyqtSignal
from pysensorflow.core import SensorEngine
import paho.mqtt.client as mqtt

class SensorWorker(QThread):
    #emits a dictionary
    data_signal = pyqtSignal(dict)

    def __init__(self, port_name, config_path="config/setup.json"):
        super().__init__()
        self.is_running = True
        #self.port_name = port_name

        # initialize engine
        self.engine = SensorEngine(config_path)
        #self.serial_conn = None

        # MQTT config
        self.broker = "broker.emqx.io"
        self.port = 1883
        self.telemetry_topic = "pysensorflow/telemetry/raw"
        self.command_topic = "pysensorflow/command"

        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            print(f"GUI Worker connected to MQTT Broker at {self.broker}")
            self.client.subscribe(self.telemetry_topic)
        else:
            print(f"Worker connection failed with code {reason_code}")

    def on_message(self, client, userdata, msg):
        """Triggered automatically every time a new MQTT message arrives."""
        if not self.is_running:
            return

        try:
            #decode the data payload
            payload = msg.payload.decode('utf-8')
            sensor_data = self.engine.parse(payload)

            if sensor_data:
                self.data_signal.emit(sensor_data)
        except Exception as e:
            print(f"Error parsing MQTT message: {e}")

    def send_command(self, command_char):
        self.client.publish(self.command_topic, command_char)
        print(f"DEBUG: Sent command {command_char} to MQTT topic {self.command_topic}")

    def run(self):
        print("MQTT UI Worker started... Listening for Cloud telemetry.\n")
        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
        
            #keep the PyQt QThread alive while the GUI is running
            while self.is_running:
                time.sleep(0.1)

        except Exception as e:
            print(f"MQTT Worker Error: {e}")

        finally:
            self.client.loop_stop()
            self.client.disconnect()
            print("DEBUG: MQTT UI connection closed")

    #stop the worker
    def stop(self):
        self.is_running = False
