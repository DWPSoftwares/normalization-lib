import enum

class LibConstants:
    DEFAULT_NORMALIZATION_CLIENT_ID = 1
    DEFAULT_FUNCTION = "mean"
    DEFAULT_GROUP = 10  # 10 seconds
    DEFAULT_DB = 'test_DB'
    FILTERS = ('Recovery', 'FeedFlow', 'RejectConductivity')
    DATA_MIN_MAX_VALUES = "DATA_MIN_MAX_VALUES"
    LABELS = {
        'normalized_permeate_flow': 'Normalized Permeate Flow',
        'normalized_differential_pressure': 'Normalized Differential Pressure',
        'normalized_permeate_TDS': 'Normalized Permeate TDS',
        'net_driving_pressure': 'Net Driving Pressure',
        'normalized_flux': 'Normalized Flux',
        'normalized_salt_passage': 'Normalized Salt Passage',
        'normalized_specific_flux': 'Normalized Specific Flux',
    }
    UNITS = {
        'normalized_permeate_flow': 'gpm',
        'normalized_differential_pressure': 'psid',
        'normalized_permeate_TDS': 'mg/L',
        'net_driving_pressure': 'psig',
        'normalized_flux': 'gfd',
        'normalized_salt_passage': '%',
        'normalized_specific_flux': 'gfd/psig',
    }
    FILTER_RECOVERY = 'Volumetric_Recovery'
    FILTER_CONDUCTIVITY = 'Reject_Conductivity'
    FILTER_FEED_FLOW_LOW = 'Feed_flow_low'
    FILTER_FEED_FLOW_HIGH = 'Feed_flow_high'
    BASELINE_TAGS = (
        "AIT1",
        "CIT1",
        "CIT2",
        "CIT3",
        "FIT1",
        "FIT2",
        "FIT3",
        "Last_CCD_VR",
        "M_DP",
        "PT2",
        "PT3",
        "PT7",
        "TT1",
        FILTER_RECOVERY
    )
    FILTER_SPS = (
        FILTER_CONDUCTIVITY,  # Target CC to PF Brine conductivity
        FILTER_FEED_FLOW_LOW,  # Target Feed flow during CC
        FILTER_FEED_FLOW_HIGH,  # Target Feed flow during PF
        FILTER_RECOVERY  # Target CC to PF Volumetric Recovery
    )
    BASELINE_DEFAULT_TAG_MAP = {
        "AIT1": "TAG084",
        "CIT1": "TAG087",
        "CIT2": "TAG088",
        "CIT3": "TAG089",
        "FIT1": "TAG071",
        "FIT2": "TAG072",
        "FIT3": "TAG073",
        "Last_CCD_VR": "TAG044",
        "M_DP": "TAG038",
        "PT2": "TAG078",
        "PT3": "TAG079",
        "PT7": "TAG080",
        "TT1": "TAG092",
        FILTER_RECOVERY: "SP023",
        FILTER_CONDUCTIVITY: "SP024",
        FILTER_FEED_FLOW_LOW: "SP014",
        FILTER_FEED_FLOW_HIGH: "SP015"
    }


class Supported_Normalized_calcs(enum.Enum):
        PERMEATE_FLOW = 'normalized_permeate_flow'
        DIFFERENTIAL_PRESSURE = 'normalized_differential_pressure'
        PERMEATE_TDS = 'normalized_permeate_TDS'
        NET_DRIVING_PRESSURE = 'net_driving_pressure'
        FLUX = 'normalized_flux'
        SALT_PASSAGE = 'normalized_salt_passage'
        SPECIFIC_FLUX = 'normalized_specific_flux'
