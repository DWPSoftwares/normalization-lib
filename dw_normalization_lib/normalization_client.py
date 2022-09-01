import pandas as pd
import numpy as np
import logging
from typing import Dict

from dw_timeseries_lib import Db_client, Tag, Measurement

from dw_normalization_lib.normalization_calculation.normalization_calculations import Normalized_calculations
from dw_normalization_lib.constants import LibConstants
from dw_normalization_lib.constants import Supported_Normalized_calcs
from dw_normalization_lib.objects.normalization_config import Normalization_config
from dw_normalization_lib.objects.filters import Filters
from dw_normalization_lib.errors import Empty_timeseries_result, Missing_baseline_tag, Invalid_baseline_values

log = logging.getLogger(__name__)

class Normalization_client:
    def __init__(self, timeseries_client: Db_client, normalization_config: Normalization_config, filters: Filters) -> None:
        """
            Initializes parameters
            Parameters:
                connector: Db_client
                    user for making calls to influx 
                normalization_config: str
                    contains data on which normalization functions are required, time window and bucket size
                basline: str,
                     object containing data on the baseline
                filters: str
                    object containing data on the fikters

        """
        self.timeseries_client = timeseries_client
        self.config = normalization_config
        if not filters:
            filters = Filters()
        self.filters = filters

    def add_baseline(self, baseline: Dict[str, float]):
        def validate_baseline():
            missing_tags = []
            invalid_baseline_tags = []
            for tag in LibConstants.BASELINE_TAGS:
                if tag not in baseline:
                    missing_tags.append(tag)
                elif type(baseline[tag]) is not float:
                    invalid_baseline_tags.append(tag)
            
            if missing_tags:
                msg = f'mapping is missing required tags for normalization. The following tags are missing: {", ".join(missing_tags)}'
                log.error(msg)
                raise Missing_baseline_tag(msg)
            
            if invalid_baseline_tags:
                msg = f'invalid values for some baseline tags: {", ".join(invalid_baseline_tags)}'
                log.error(msg)
                raise Invalid_baseline_values(msg)

        def baseline_to_df():
            df_dict = {key: [baseline[key]] for key in baseline}
            df = pd.DataFrame.from_dict(df_dict)
            return df
        
        validate_baseline()
        # continue if no error

        baseline_df = baseline_to_df()
        self.baseline = baseline_df
        

    def get_normalization(self):
        df = self.__normalization_mapping_df_from_influx()
        df = self.__add_baseline(df)
        df = self.__apply_filters(df)
        if df.shape[0] == 0:
            log.warning(f'widget: {self.config.__repr__}')
            return None
        df = self.__calculate_normalization_df(df)
        # df = self.__remove_baseline(df)
        return df
    
    def __normalization_mapping_df_from_influx(self):
        measurments = list()
        tags = {}
        for tag in self.baseline:
            tags[tag] = Tag(tag, self.config.mapping[tag], LibConstants.DEFAULT_FUNCTION)
        new_measurment = Measurement(
            "normalization",
            self.config.systemId,
            tags,
            self.config.group,
            self.config.start_datetime,
            self.config.end_datetime,
            db=LibConstants.DEFAULT_DB
        )
        measurments.append(new_measurment)
        res_measurment = self.timeseries_client.get_data(measurments)
        df = res_measurment[0].data
        
        if df.empty:
            error = "Error in fetching data for baseline tags - no data"
            raise Empty_timeseries_result(error, code=1)
        
        series_null_columns = df.isna().all()
        if series_null_columns.any():
            # array
            null_columns = series_null_columns[series_null_columns].index.values
            warning = f'Error the following tags contain no data {" ".join(null_columns)} - please check baseline tag mapping and time range'
            log.warning(warning)

        return df

    def __add_baseline(self, df):
        df = df.append(self.baseline, ignore_index=True)
        return df

    def __remove_baseline(self, df):
        df.drop(df.tail(1).index, inplace=True)
        return df

    def __apply_filters(self,df):
        def store_max_min_values(df, widget):
            widget[LibConstants.DATA_MIN_MAX_VALUES] = {
                "Recovery": {"Max": round(df["Last_CCD_VR"].max(), 2), "Min": round(df["Last_CCD_VR"].min(), 2)},
                "FeedFlow": {"Max": round(df["FIT1"].max(), 2), "Min": round(df["FIT1"].min(), 2)},
                "RejectConductivity": {"Max": round(df["CIT2"].max(), 2), "Min": round(df["CIT2"].min(), 2)}
            }
            log.debug(
                f'Normalization data, Min and Max values : {widget[LibConstants.DATA_MIN_MAX_VALUES]}')

        # for filter_ in LibConstants.FILTERS:
        #     if float(self.filters[filter_]["Low"]) < 0:
        #         self.filters[filter_]["Low"] = 0
        #         log.warning(
        #             f'{filter_} filter has negative value for widgetId: {self.config.id}')

        log.debug(
            f'Filter Recovery, Low: {self.filters.recovery_low}, High :{self.filters.recovery_high}')
        log.debug(
            f'Filter Feed Flow, Low: {self.filters.feed_flow_low}, High :{self.filters.feed_flow_high}')
        log.debug(
            f'Filter Reject Conductivity, Low: {self.filters.reject_conductivity_low}, High :{self.filters.reject_conductivity_high}')
        initial_row_count = df.shape[0]
        df.loc[
            (df["Last_CCD_VR"] < float(self.filters.recovery_low))
            | (df["Last_CCD_VR"] > float(self.filters.recovery_high))
            | (df["FIT1"] < float(self.filters.feed_flow_low))
            | (df["FIT1"] > float(self.filters.feed_flow_high))
            | (df["CIT2"] < float(self.filters.reject_conductivity_low))
            | (df["CIT2"] > float(self.filters.reject_conductivity_high))
        ] = np.nan

        # df.dropna(subset=["FIT1", "CIT2", "Last_CCD_VR"], inplace=True)
        filter_row_count = df.shape[0]
        if filter_row_count > 0:
            log.info(f'Filtered rows : {initial_row_count - filter_row_count}')
        return df

    def __calculate_normalization_df(self, df):
        for i, tag in enumerate(self.config.tags):
            if tag in Supported_Normalized_calcs:
                calculation_client = Normalized_calculations()
                print(tag)
                print(tag.value)
                log.debug(
                    f'Calling normalized Function :{calculation_client.normalization_function_map[tag.value]}, Tag :{tag.value}'
                )
                df = calculation_client.normalization_function_map[tag.value](df, i)

        result_columns = ["Time"]
        result_columns.extend([tag.value for tag in self.config.tags if tag in Supported_Normalized_calcs])
        res_df = df[result_columns]
        return res_df
