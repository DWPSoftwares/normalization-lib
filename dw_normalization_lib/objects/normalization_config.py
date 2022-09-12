import datetime
from typing import List, Dict, Optional

from dw_normalization_lib.constants import LibConstants, Supported_Normalized_calcs
from dw_normalization_lib.errors import Missing_mapping_tag
from dw_normalization_lib.objects.filters import Filters


class Normalization_config():
    def __init__(
        self,
        id: str,
        systemId: str,
        group: int, 
        start_datetime: datetime.datetime,
        end_datetime: datetime.datetime, 
        tags: List[Supported_Normalized_calcs],
        mapping: Optional[Dict[str, str]] = None,
        filters: Optional[Filters] = None
    ) -> None:
        '''
            Used for initializing the normalization client with reqired data for the execution of the calculation.
            Parameters:
                id: str
                systemId: str
                    a valid systemId, normalization calculation is performed for this system
                group: int
                    time in seconds between result values
                start_datetime: datetime.datetime
                    data start time
                end_datetime: datetime.datetime
                    data end time
                tags: List[Supported_Normalized_calcs]
                    A list of normalization calculation to be performed, must be selected from the supported normalization calculations
                mapping: Optional[Dict[str, str]] = None
                    A dictionary where keys are the required tag functions to perform the normalization calculations 
                    the value is the tagId for that function per that system. 
                    
                    The parameter is optional, if not passed, stored default values are used instead.
                    default values can be examined by importing BASELINE_DEFAULT_TAG_MAP

                    The purpose is the mapping is to ensure the calculations are performed on the correct tagsId's.
                    For example:
                    AIT1 default value is 'Tag002'
                    case 1: AIT1 is represented by tagId 'Tag001' on systemId 'System1'
                    case 2: AIT1 is represented by tagId 'Tag002' on systemId 'System2'

                    in case 1: 
                        mapping will be pased so that mapping = {...,"AIT1": "Tag001"  , ...}
                    in case 2:
                        mapping will be pased so that mapping = {...,"AIT1": "Tag002"  , ...}
                        OR
                        mapping will not be passed/passed as None and default value will be used.
        '''
        self.id = id
        self.systemId = systemId
        self.group = group
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.tags = tags
        if mapping:
            self.mapping = mapping
        else:
            self.mapping = LibConstants.BASELINE_DEFAULT_TAG_MAP

        if filters:
            self.filters = filters
        else: 
            self.filters = Filters()

    def validate_mapping(self) -> bool:
        '''
            Validates that each tag required for normalization has it's mapping between value and tagId supplied by the client
            Returns:
                bool:
                    True if all mappings as described in LibConstants.BASELINE_TAGS are present
            Raises:
                Missing_mapping_tag
                    Iff at least one of the required tags is missing in mapping.
        '''
        if all([tag in self.mapping for tag in LibConstants.BASELINE_TAGS]):
            return True
        else:
            missing_tags = []
            for tag in LibConstants.BASELINE_TAGS:
                if tag not in self.mapping:
                    missing_tags.append(tag)
            raise Missing_mapping_tag(f'mapping is missing required tags for normalization. The following tags are missing: {", ".join(missing_tags)}')
