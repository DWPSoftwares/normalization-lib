import pandas as pd
import numpy as np
import logging

from dw_normalization_lib import Db_client, Tag, Measurement

from dw_normalization_lib.normalization_calculation.normalization_calculations import Normalized_calculations
from dw_normalization_lib.constants import LibConstants
from dw_normalization_lib.constants import Supported_Normalized_calcs
from dw_normalization_lib.objects.normalization_config import Normalization_config
from dw_normalization_lib.objects.filters import Filters
from errors import Empty_timeseries_result

log = logging.getLogger(__name__)

class Normalization_client:
    def __init__(self, timeseries_client: Db_client, normalization_config: Normalization_config, basline, filters: Filters) -> None:
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
        self.connector = timeseries_client
        self.config = normalization_config
        self.baseline = basline
        self.filters = filters

    def get_normalization(self):
        df = self.__normalization_mapping_df_from_influx()
        df = self.__add_baseline()
        df = self.__apply_filters(df)
        if df.shape[0] == 0:
            log.warning(f'widget: {self.config.__repr__}')
            return None
        df = self.__calculate_normalization_df(df)
        df = self.__remove_baseline(df)
        return df
    
    def __normalization_mapping_df_from_influx(self):
        measurments = list()
        for tag in self.baseline.tags:
            tags = {}
            tags[tag] = Tag(tag, tag, LibConstants.DEFAULT_FUNCTION)
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
        df = self.timeseries_client.get_data(measurments)
        
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
        df = df.append(self.baseline.data, ignore_index=True)
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

        for filter_ in LibConstants.FILTERS:
            if float(self.filters[filter_]["Low"]) < 0:
                self.filters[filter_]["Low"] = 0
                log.warning(
                    f'{filter_} filter has negative value for widgetId: {self.config.id}')

        log.debug(
            f'Filter Recovery, Low: {self.filters.recovery_low}, High :{self.filters.recovery_high}')
        log.debug(
            f'Filter Feed Flow, Low: {self.filters.feed_flow_low}, High :{self.filters.feed_flow_high}')
        log.debug(
            f'Filter Reject Conductivity, Low: {self.filters.reject_conductivity_low}, High :{self.filters.reject_conductivity_high}')
        initial_row_count = df.shape[0]
        df.loc[
            (df["Last_CCD_VR"] < float(self.filters.recovery.low))
            | (df["Last_CCD_VR"] > float(self.filters.recovery.high))
            | (df["FIT1"] < float(self.filters.feed_flow_low))
            | (df["FIT1"] > float(self.filters.feed_flow_high))
            | (df["CIT2"] < float(self.filters.reject_conductivity_low))
            | (df["CIT2"] > float(self.filters.reject_conductivity_high))
        ] = np.nan

        df.dropna(subset=["FIT1", "CIT2", "Last_CCD_VR"], inplace=True)
        filter_row_count = df.shape[0]
        if filter_row_count > 0:
            log.info(f'Filtered rows : {initial_row_count - filter_row_count}')

    def __calculate_normalization_df(self, df):
        all_tags = ["Time"]
        normalization_tags = []
        for i, tag in enumerate(self.config.tags):
            df_tag_label = f'Tag{str(i + 1)}'
            all_tags.append(df_tag_label)
            if tag["Tag"] in Normalized_calculations.normalization_function_map:
                if df_tag_label in pd_reg:
                    pd_reg = pd_reg.drop(df_tag_label, 1)
                log.debug(
                    f'Calling normalized Function :{Normalized_calculations.normalization_function_map[tag["Tag"]]}, Tag :{tag["Tag"]}'
                )
                df = Normalized_calculations.normalization_function_map[tag["Tag"]](df, i)
                tag["TagName"] = LibConstants.LABELS[tag["Tag"]]
                tag["Units"] = LibConstants.UNITS[tag["Tag"]]
                normalization_tags.append(df_tag_label)