import json
from .sensors import AnalogSensor

class SensorEngine:
    def __init__(self, config_path):
        self.sensors = {}
        self.load_config(config_path)

    def load_config(self, path):
        with open(path, 'r') as f:
            self.config = json.load(f)

        #factory pattern: create objects based on json
        for sensor_conf in self.config['sensors']:
            s_id = sensor_conf['id']
            if sensor_conf['type'] == 'analog':
                self.sensors[s_id] = AnalogSensor(sensor_conf)

    def parse(self, csv_line):
        """
        Takes raw string "500, 200" and returns dict {'ldr': 500, 'pot': 200}
        """
        if not csv_line or ',' not in csv_line:
            return None

        raw_values = csv_line.split(',')
        results = {}

        # ask each sensor object to find its own data
        for s_id, sensor_obj in self.sensors.items():
            val = sensor_obj.process(raw_values)
            results[s_id] = val

        return results
