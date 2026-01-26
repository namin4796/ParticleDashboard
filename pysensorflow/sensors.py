from abc import ABC, abstractmethod

class BaseSensor(ABC):
    """
    Abstract Base Class that all sensors must inherit from.
    """
    def __init__(self, config):
        self.id = config['id']
        self.name = config['name']
        self.index = config['index']
        self.value = 0.0

    @abstractmethod
    def process(self, raw_data_list):
        pass

class AnalogSensor(BaseSensor):
    """Standard 0-1023 ADC sensor"""
    def process(self, raw_data_list):
        # safety check: ensure data exists at this index
        if self.index < len(raw_data_list):
            try:
                self.value = float(raw_data_list[self.index])
            except ValueError:
                pass
        return self.value
