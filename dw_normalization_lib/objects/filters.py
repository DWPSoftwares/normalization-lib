from dataclasses import dataclass

@dataclass
class Filters:
    reject_conductivity_low: float
    reject_conductivity_high: float
    feed_flow_low: float
    feed_flow_hight: float
    recovery_low: float
    recovery_high: float
