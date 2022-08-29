import pandas as pd
import numpy as np
import logging

from dw_timeseries_lib import Db_client, Tag, Measurement

from normalization_calculation import Normalized_calculations
from constants import LibConstants
from errors import Empty_timeseries_result

log = logging.getLogger(__name__)

class Normalization_client:
    def __init__(self, timeseries_client: Db_client, normalization_config, basline, filters) -> None:
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
            log.warning(f'widget: {self.normalization_config.__repr__}')
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
            self.normalization_config.systemId,
            tags,
            self.normalization_config.group,
            self.normalization_config.start_datetime,
            self.normalization_config.end_datetime,
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
            if float(self.normalization_config[filter_]["Low"]) < 0:
                self.normalization_config[filter_]["Low"] = 0
                log.warning(
                    f'{filter_} filter has negative value for widgetId: {self.normalization_config.id}')

        log.debug(
            f'Filter Recovery, Low: {self.normalization_config.recovery.low}, High :{self.normalization_config.recovery.high}')
        log.debug(
            f'Filter Feed Flow, Low: {self.normalization_config.feedflow.low}, High :{self.normalization_config.feedflow.high}')
        log.debug(
            f'Filter Reject Conductivity, Low: {self.normalization_config.rejectConductivity.low}, High :{self.normalization_config.rejectConductivity.high}')
        initial_row_count = df.shape[0]
        df.loc[
            (df["Last_CCD_VR"] < float(self.normalization_config.recovery.low))
            | (df["Last_CCD_VR"] > float(self.normalization_config.recovery.high))
            | (df["FIT1"] < float(self.normalization_config.feedflow.low))
            | (df["FIT1"] > float(self.normalization_config.feedflow.high))
            | (df["CIT2"] < float(self.normalization_config.rejectConductivity.low))
            | (df["CIT2"] > float(self.normalization_config.rejectConductivity.high))
        ] = np.nan

        df.dropna(subset=["FIT1", "CIT2", "Last_CCD_VR"], inplace=True)
        filter_row_count = df.shape[0]
        if filter_row_count > 0:
            log.info(f'Filtered rows : {initial_row_count - filter_row_count}')

    def __calculate_normalization_df(self, df):
        all_tags = ["Time"]
        normalization_tags = []
        for i, tag in enumerate(self.normalization_config.tags):
            if not tag["Tag"]:  # empty tag
                continue
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