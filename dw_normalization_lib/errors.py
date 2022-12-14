
class CustomCloudUtilError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self) -> str:
        if self.message:
            return f'{self.message}'
        else:
            return f'Timeseries db error occurred'


class Empty_timeseries_result(Exception):
    def __init__(self, *args: object) -> None:
        if args:
            self.message = args[0]
        else:
            self.message = 'empty data returned from timeseries db'
        super().__init__(*args)


class Missing_mapping_tag(Exception):
    def __init__(self, *args: object) -> None:
        if args:
            self.message = args[0]
        else:
            self.message = 'tag/s missing in mapping'
        super().__init__(*args)


class Missing_baseline_tag(Exception):
    def __init__(self, *args: object) -> None:
        if args:
            self.message = args[0]
        else:
            self.message = 'tag/s missing in baseline'
        super().__init__(*args)


class Invalid_baseline_values(Exception):
    def __init__(self, *args: object) -> None:
        if args:
            self.message = args[0]
        else:
            self.message = 'some tags have invalid value'
        super().__init__(*args)


class SystemId_not_configured(Exception):
    def __init__(self, *args: object) -> None:
        if args:
            self.message = args[0]
        else:
            self.message = 'No systemId configured for normalization cliend instance'
        super().__init__(*args)


class No_timeseries_data_found(Exception):
    def __init__(self, *args: object) -> None:
        if args:
            self.message = args[0]
        else:
            self.message = 'no time series data has been found for the selected system, tags and time window'
        super().__init__(*args)