import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Union, Optional
import datetime

from dw_timeseries_lib import Db_client, Tag, Measurement

from dw_normalization_lib.normalization_calculation.normalization_calculations import Normalized_calculations
from dw_normalization_lib.constants import LibConstants
from dw_normalization_lib.constants import Supported_Normalized_calcs
from dw_normalization_lib.objects.normalization_config import Normalization_config
from dw_normalization_lib.objects.filters import Filters
from dw_normalization_lib.errors import (
    Empty_timeseries_result,
    Missing_baseline_tag,
    Invalid_baseline_values,
    SystemId_not_configured,
    No_timeseries_data_found
)

log = logging.getLogger(__name__)

class Normalization_client:
    id: int
    systemId: Union[str, None] = None
    mapping: Dict[str, str]
    group: int
    start_datetime: Union[datetime.datetime, None] = None
    end_datetime: Union[datetime.datetime, None] = None
    normalization_tags: Union[List[Supported_Normalized_calcs], None] = None
    baseline: Union[pd.DataFrame, None] = None
    filters: Filters
    tags: Union[List[str], None] = None

    def __init__(
        self,
        timeseries_client: Db_client,
        normalization_config: Optional[Union[None, Normalization_config]],
    ) -> None:
        """
            Initializes parameters
            Parameters:
                connector: Db_client
                    user for making calls to influx 
                normalization_config: str
                    contains data on which normalization functions are required, time window and bucket size
        """
        if normalization_config:
            self.id = normalization_config.id
            self.systemId = normalization_config.systemId
            self.mapping = normalization_config.mapping
            self.group = normalization_config.group
            self.start_datetime = normalization_config.start_datetime
            self.end_datetime = normalization_config.end_datetime
            self.normalization_tags = normalization_config.tags
            self.filters = normalization_config.filters
        else:  # setting defaults
            self.id = LibConstants.DEFAULT_NORMALIZATION_CLIENT_ID
            self.mapping = LibConstants.BASELINE_DEFAULT_TAG_MAP
            self.group = LibConstants.DEFAULT_GROUP
            self.filters = Filters()

        self.timeseries_client = timeseries_client

    def add_baseline(self, baseline: Dict[str, float]):
        def validate_baseline():
            missing_tags = []
            invalid_baseline_tags = []
            for tag in LibConstants.BASELINE_TAGS:
                if tag not in baseline:
                    missing_tags.append(tag)
                # elif type(baseline[tag]) is not float:
                #     invalid_baseline_tags.append(tag)
            
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

    def baseline_from_timestamp(self, timestamp:datetime.datetime):
        def extract_closest_df_value(df, column, timestamp):
            df = df[[column]]
            df = df.dropna()
            if len(df):
                loc = df.index.get_loc(timestamp, method="nearest")
                val = df[column][loc]
                if np.isnan(val):
                    val = None
                return val
            else:
                return None

        if not self.systemId:
            raise SystemId_not_configured()

        tz = timestamp.tzinfo
        if tz:
            tz = str(tz)
        else:
            tz = 'UTC'

        dt = timestamp.replace(tzinfo=None)
        start_dt = dt - datetime.timedelta(minutes=30)
        end_dt = dt + datetime.timedelta(minutes=30)
        
        measurments = list()
        tags = {}
        for tag in LibConstants.BASELINE_TAGS:
            tags[tag] = Tag(tag, self.mapping[tag], LibConstants.DEFAULT_FUNCTION)
        baseline_measurment = Measurement(
            "baseline",
            self.systemId,
            tags,
            LibConstants.DEFAULT_GROUP,
            start_dt,
            end_dt,
            timezone=tz,
            db=LibConstants.DEFAULT_DB
        )
        measurments.append(baseline_measurment)
        res_measurment = self.timeseries_client.get_data(measurments)
        df = res_measurment[0].data

        baseline = {}
        if df is not None and not df.empty:
            df_dt = pd.to_datetime(dt)
            df["Time"] = pd.to_datetime(df["Time"]).dt.tz_localize(None)  # convert from ISO to df TimeStamp
            df = df.set_index("Time")
            for i, column in enumerate(df.columns.values.tolist()):
                if column == "Time":
                    continue
                val = extract_closest_df_value(df.copy(), column, df_dt)
                baseline[column] = val
        else:
            mapping_tags_string = ' '.join([self.mapping[tag] for tag in tag in LibConstants.BASELINE_TAGS])
            log.warn('No data in timeseries db for all tags in selected mapping: {mapping_tags_string}, \
                for system {self.systemId} in the time window from {start_dt} to {end_dt}')
            baseline = {elem: None for elem in self.mapping}
        
        return baseline

    def get_normalization(self):
        df = self.__normalization_mapping_df_from_timeseries_db()
        df = self.__add_baseline(df)
        df = self.__apply_filters(df)
        if df.shape[0] == 0:
            log.warning(f'widget: {self.__repr__}')
            return None
        df = self.__calculate_normalization_df(df)
        df = self.__remove_baseline(df)
        return df
    
    def __normalization_mapping_df_from_timeseries_db(self):
        measurments = list()
        tags = {}
        for tag in self.baseline:
            tags[tag] = Tag(tag, self.mapping[tag], LibConstants.DEFAULT_FUNCTION)
        # case client requested additional system tags
        if self.tags:
            for tag in self.tags:
                tags[tag] = Tag(tag, tag, LibConstants.DEFAULT_FUNCTION)
        # resume normal flow
        new_measurment = Measurement(
            "normalization",
            self.systemId,
            tags,
            self.group,
            self.start_datetime,
            self.end_datetime,
            bucket=LibConstants.DEFAULT_BUCKET,
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
        df_filters = df[["Last_CCD_VR", "FIT1", "CIT2"]]
        df_filters.loc[
            (df["Last_CCD_VR"] < float(self.filters.recovery_low))
            | (df["Last_CCD_VR"] > float(self.filters.recovery_high))
            | (df["FIT1"] < float(self.filters.feed_flow_low))
            | (df["FIT1"] > float(self.filters.feed_flow_high))
            | (df["CIT2"] < float(self.filters.reject_conductivity_low))
            | (df["CIT2"] > float(self.filters.reject_conductivity_high))
        ] = np.nan

        df = df.where(pd.notnull(df), None)

        # df.dropna(subset=["FIT1", "CIT2", "Last_CCD_VR"], inplace=True)
        filter_row_count = df.shape[0]
        if filter_row_count > 0:
            log.info(f'Filtered rows : {initial_row_count - filter_row_count}')
        return df

    def __calculate_normalization_df(self, df):
        for i, tag in enumerate(self.normalization_tags):
            if tag in Supported_Normalized_calcs:
                calculation_client = Normalized_calculations()
                log.debug(
                    f'Calling normalized Function :{calculation_client.normalization_function_map[tag.value]}, Tag :{tag.value}'
                )
                df = calculation_client.normalization_function_map[tag.value](df)

        result_columns = ["Time"]
        result_columns.extend([tag.value for tag in self.normalization_tags if tag in Supported_Normalized_calcs])
        # case client requested additional system tags
        if self.tags:
            result_columns.extend([tag for tag in self.tags])
        res_df = df[result_columns]
        return res_df
