import json
import time
import serial
import paho.mqtt.client as mqtt

try:
    with open("config/setup.json", "r") as f:
        config = json.load(f)
    PORT = config.get("port", "/dev/cu.usbmodem14201")
    BAUD = config.get("baud_rate", 9600)

except Exception as e:
    print(f"Failed to load config: {e}")
    exit(1)

# MQTT config
BROKER = "broker.emqx.io"
PORT_MQTT = 1883 # public testing broker
TOPIC = "pysensorflow/telemetry/raw"

# create a MQTT client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

def on_connect(client, usedata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"SUCCESS: Connected to MQTT Broker at {BROKER}")
    else:
        print(f"FAILED: Connection error code {reason_code}")

client.on_connect = on_connect
client.connect(BROKER, PORT_MQTT, 60)

#start network loop in the background
client.loop_start()

#main loop
print(f"Opening Serial Port {PORT} at {BAUD} baud ... ")
try:
    ser = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2) # wait for Arduino to reset
    ser.reset_input_buffer()

    print("Bridge active. Reading hardware and publishing to MQTT... (Press Ctrl+C to quit)")

    while True:
        if ser.in_waiting > 0:
            try:
                line = ser.readline().decode('utf-8').strip()
                if line:
                    client.publish(TOPIC, line)
                    print(f"Published to {TOPIC}: {line}")
            except UnicodeDecodeError:
                pass # ignore junk data
        time.sleep(0.01)

except serial.SerialException as e:
    print(f"\nSerial Error: {e}\n(Is the Arduino plugged in or is the dashboard currently locking the port?)")
except KeyboardInterrupt:
    print("\nShutting down bridge...")
finally:
    client.loop_stop()
    if 'ser' in locals() and ser.is_open:
        ser.close()
