from hx711 import HX711

class Tank:

    def __init__(self,fullWeight=0,dryWeight=0,s=None) -> None:
        self.weight = 0
        self.level = 0
        self.value = 0
        self.dry_weight = dryWeight
        self.full_weight = fullWeight
        self.sensor = s
        if self.sensor is None:
            raise ValueError("No sensor provided")
        self.sensor.set_reading_format("MSB", "MSB")
        self.sensor.set_reference_unit(57)
        self.sensor.reset()
        #self.tare()

    def tare(self):
#        self.full_weight = self.sensor.tare()
        self.sensor.tare()

    def set_full_weight(self, fw=0):
        if fw is not None:
            self.full_weight = fw

    def get_weight(self):
        self.weight = self.sensor.get_weight()
        # level = (weight - dry_weight) / (full_weight - dry_weight) %
        self.level = ((100.0/self.dry_weight) * self.weight) + 100
        return self.weight

    def get_value(self):
        self.value = self.sensor.get_value()
        return self.value
