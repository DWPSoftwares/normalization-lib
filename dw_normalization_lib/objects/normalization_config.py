from dataclasses import dataclass
import datetime
from typing import List

from constants import Supported_Normalized_calcs

@dataclass
class Normalization_config():
    id: str
    systemId: str
    group: int
    start_datetime: datetime.datetime
    end_datetime: datetime.datetime
    tags: List[Supported_Normalized_calcs]
