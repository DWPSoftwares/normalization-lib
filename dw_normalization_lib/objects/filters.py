from dataclasses import dataclass

@dataclass
class Filters:
    '''
        valid values for reject conductivity, feed flow and recovery are non negative
        therefor default low values are set to zero
    '''
    reject_conductivity_low: float = 0
    reject_conductivity_high: float = float('inf')
    feed_flow_low: float = 0
    feed_flow_high: float = float('inf')
    recovery_low: float = 0
    recovery_high: float = float('inf')
