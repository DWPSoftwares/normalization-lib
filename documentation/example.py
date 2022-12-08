import os
import sys
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import datetime
import pytz

from dw_normalization_lib import (
    Normalization_client,
    BASELINE_DEFAULT_TAG_MAP,
    Filters,
    Normalization_config,
    Supported_Normalized_calcs,
    Filters
)

from dw_timeseries_lib import (
    Timeseries_factory,
    SupportedDbs,
    Df_influx_convertor_v2,
    Influx_connection_data_v2,
    InfluxDbVersion
)

DEFAULT_SYSTEMID = 'WEST_MORGAN_1_1137C_RO1'
DEFAULT_GROUP = 300  # 5 mins

with open("./documentation/config.json", 'r') as fi:
    config = json.load(fi)

with open("./documentation/mapping.json", 'r') as fi:
    mapping = json.load(fi)

with open("./documentation/baseline.json", 'r') as fi:
    baseline = json.load(fi)

# creating and configuring influx client
# connection_data = Influx_connection_data(config["host"], config["port"], config["username"], config["password"])
# timeseries_factory = Timeseries_factory()
df_converter = Df_influx_convertor_v2()
# influx_client = timeseries_factory.get_instance(SupportedDbs(1), connection_data, df_converter)

connection_data = Influx_connection_data_v2(org_name=config["org_name"],token=config["token"],url=config["url"])

timeseries_factory = Timeseries_factory()
influx_client = timeseries_factory.get_instance(SupportedDbs(1), connection_data, df_converter, version=InfluxDbVersion.V2)

filters = Filters(0, 100, 0, 100, 0, 100)

#creating and configuring normalization config
normalization_config = Normalization_config(
    1,
    DEFAULT_SYSTEMID,
    DEFAULT_GROUP,
    datetime.datetime.utcnow() - datetime.timedelta(days=1),  # 1 day ago
    datetime.datetime.utcnow(),
    [Supported_Normalized_calcs('normalized_permeate_flow'), Supported_Normalized_calcs('net_driving_pressure')],
    mapping,
)

client = Normalization_client(influx_client, normalization_config)

ts = datetime.datetime(2022, 9, 1, 9, 18)

baseline = client.baseline_from_timestamp(ts)
print("--- baseline ---- \n")
print(baseline)

client.add_baseline(baseline)

client.tags = ["TAG037"]
result = client.get_normalization()

print('---result--- \n')
print(result)