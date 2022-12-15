import logging
from logging import NullHandler

from .normalization_client import Normalization_client
from .constants import LibConstants, Supported_Normalized_calcs
BASELINE_DEFAULT_TAG_MAP = LibConstants.BASELINE_DEFAULT_TAG_MAP
from .objects import Filters, Normalization_config
from ._version import __version__

__author__ = "DuPont W&P IT Team"
__version__ = __version__

__all__ = (
    Normalization_client,
    BASELINE_DEFAULT_TAG_MAP,
    Supported_Normalized_calcs,
    Filters,
    Normalization_config
)

# Set default logging handler to avoid "No handler found" warnings.
logging.getLogger(__name__).addHandler(NullHandler())
