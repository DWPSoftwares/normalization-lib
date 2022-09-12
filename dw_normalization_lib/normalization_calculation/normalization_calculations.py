import numpy as np
import logging
import math

log = logging.getLogger(__name__)

class Normalized_calculations():
    def __init__(self):
        self.normalization_function_map = {
            "normalized_permeate_flow": self.normalized_permeate_flow,
            "normalized_differential_pressure": self.normalized_differential_pressure,
            "normalized_permeate_TDS": self.normalized_permeate_TDS,
            "net_driving_pressure": self.net_driving_pressure,
            "normalized_flux": self.normalized_flux,
            "normalized_salt_passage": self.normalized_salt_passage,
            "normalized_specific_flux": self.normalized_specific_flux,
        }

    def calulate_coefficient(self, df):
        if df["TT_1_C"] > 25:
            return 2640
        else:
            return 3020


    def calculate_TT_1_C(self, df):
        if np.isnan(df["TT1"]) or df["TT1"] is None:
            return 0
        return (df["TT1"] - 32) / 1.8


    # IFERROR(IF(T9-V9<2,U9+T9,T9),0)
    def calculate_lead_element_flow(self, df):
        try:
            if np.isnan(df["FIT1"]) or np.isnan(df["FIT3"]):
                return 0
            if (df["FIT1"] - df["FIT3"]) < 2:
                if np.isnan(df["FIT2"]):
                    return 0
                return df["FIT1"] + df["FIT2"]
            else:
                return df["FIT1"]
        except TypeError:
            return 0


    # IFERROR(IF(Z8=0,0,V8/Z8),0)
    def calculate_module_recovery(self, df):
        try:
            if np.isnan(df["lead_element_flow"]):
                return 0
            if df["lead_element_flow"] == 0:
                return 0
            else:
                if np.isnan(df["FIT3"]):
                    return 0
                return df["FIT3"] / df["lead_element_flow"]
        except (TypeError, ValueError, ZeroDivisionError):
            return 0


    # IFERROR(((L7*AC7)+((M7*1000)*(1-AC7)))*0.67,0)
    def calculate_feed_cond_C(self, df):
        try:
            if (
                np.isnan(df["CIT1"])
                or np.isnan(df["module_recovery"])
                or np.isnan(df["CIT2"])
            ):
                return 0
            return (df["CIT1"] * df["module_recovery"]) + (
                (df["CIT2"] * 1_000) * (1 - df["module_recovery"]) * 0.67
            )
        except TypeError:
            return 0


    # IFERROR(IF(AC6=0,0,AH6*((LN(1/(1-AC6)))/AC6)),0)
    def calculate_feed_reject_cond_C(self, df):
        try:
            if (
                df["module_recovery"] == 0
                or np.isnan(df["module_recovery"])
                or np.isnan(df["feed_cond_C"])
            ):
                return 0
            else:
                return df["feed_cond_C"] * (
                    math.log(1 / (1 - df["module_recovery"])
                            ) / df["module_recovery"]
                )
        except (TypeError, ValueError, ZeroDivisionError):
            return 0


    # IFERROR(IF(AG6<20000,(AG6*(C6+320))/491000,((0.0117*AG6-34/14.23)*((C6+320)/345))),0)
    def calculate_osmotic_pressure(self, df):
        try:
            if np.isnan(df["feed_reject_cond_C"]) or np.isnan(df["TT_1_C"]):
                return 0
            if df["feed_reject_cond_C"] < 20_000:
                return df["feed_reject_cond_C"] * (df["TT_1_C"] + 320) / 491_000
            else:
                return ((0.0117 * df["feed_reject_cond_C"]) - (34 / 14.23)) * (
                    (df["TT_1_C"] + 320) / 345
                )
        except TypeError:
            return 0


    # IFERROR((((E5+F5)/2)/14.23)-(12/14.23)-AF5,0)
    def calculate_trans_membrane_pressure(self, df):
        try:
            if np.isnan(df["PT2"]) or np.isnan(df["osmotic_pressure"]):
                return 0
            return (
                (((df["PT2"] + df["PT3"]) / 2) / 14.23)
                - (df["PT7"] / 14.23)
                - df["osmotic_pressure"]
            )
        except TypeError:
            return 0


    # V184*($AJ$5/AJ184)*($AE$5/AE184)
    def calculate_normalized_permeate_flow(
        self, df, bl_trans_membrane_pressure, bl_temperature_correction_factor
    ):
        try:
            if (
                np.isnan(df["FIT3"])
                or np.isnan(df["trans_membrane_pressure"])
                or np.isnan(df["temperature_correction_factor"])
                or df["trans_membrane_pressure"] == 0
                or df["temperature_correction_factor"] == 0
            ):
                return 0
            val = float(
                df["FIT3"]
                * (bl_trans_membrane_pressure / df["trans_membrane_pressure"])
                * (bl_temperature_correction_factor / df["temperature_correction_factor"])
            )
            return val
        except BaseException as err:
            print(
                f'Base Exception : {str (err)} ')
            return 0


    # (IF(C5>25,EXP(2640*((1/298)-(1/(273+C5)))),EXP(3020*((1/298)-(1/(273+C5)))))
    def calculate_temperature_correction_factor(self, df):
        return np.exp(df["coefficient"] * ((1 / 298) - (1 / (273 + df["TT_1_C"]))))


    # I8*($AE$5/AE8)
    def calculate_normalized_differential_pressure(self, df, bl_temperature_correction_factor):
        try:
            val = (df["PT2"] - df["PT3"]) * (
                bl_temperature_correction_factor /
                df["temperature_correction_factor"]
            )
            return val
        except BaseException:
            return 0


    # IFERROR((N5*(C5+320))/491000,0)
    def calculate_osmotic_pressure_Posmo_p(self, df):
        if np.isnan(df["CIT3"]) or np.isnan(df["TT_1_C"]):
            return 0
        else:
            return df["CIT3"] * (df["TT_1_C"] + 320) / 491_000


    def calculate_normalized_permeate_TDS(
        self, df, bl_trans_membrane_pressure, bl_feed_reject_cond_C, bl_osmotic_pressure_Posmo_p
    ):
        try:
            if np.isnan(df["CIT3"]):
                return 0
            return (
                (df["CIT3"] * 0.67)
                * (
                    (df["trans_membrane_pressure"] + df["osmotic_pressure_Posmo_p"])
                    / (bl_trans_membrane_pressure + bl_osmotic_pressure_Posmo_p)
                )
                * (bl_feed_reject_cond_C / df["feed_reject_cond_C"])
            )
        except (TypeError, ZeroDivisionError):
            return 0


    # IFERROR((L5*LN((M5*1000)/L5))/(1-(L5/(M5*1000))),0)
    def calculate_avg_feed(self, df):
        if np.isnan(df["CIT1"]) or np.isnan(df["CIT2"]) or df["CIT1"] == 0 or df['CIT2'] == 0:
            return 0
        return (df["CIT1"] * np.log(df["CIT2"] * 1_000 / df["CIT1"])) / (
            1 - (df["CIT1"] / (df["CIT2"] * 1_000))
        )


    # (CALC) Q = IFERROR((O7-N7)/O7,0)
    def calculate_avg_membrane_rejection(self, df):
        if np.isnan(df["CIT3"]):
            return 0
        try:
            return (df["avg_feed"] - df["CIT3"]) / df["avg_feed"]
        except (TypeError, ZeroDivisionError):
            return 0


    # 100*(1-Q33)*($AE$5/AE33)
    def calculate_normalized_salt_passage(self, df, bl_temperature_correction_factor):
        return (
            100
            * (1 - df["avg_membrane_rejection"])
            / (bl_temperature_correction_factor / df["temperature_correction_factor"])
        )


    # ((I5/2)-12-(AF5*14.23)+(AM5*14.23))*-1
    def calculate_net_driving_pressure(self, df):
        if np.isnan(df["PT2"]) or np.isnan(df["PT3"]):
            return 0
        return (
            (((df["PT2"] - df["PT3"]) / 2)
                - df["PT7"]
                - (df["osmotic_pressure"] * 14.23)
                + (df["osmotic_pressure_Posmo_p"] * 14.23)) * (-1)
        )


    # IFERROR((V5*1440)/1200,0)
    def calculate_operating_flux(self, df):
        if np.isnan(df["FIT3"]):
            return 0
        return df["FIT3"] * 1440 / 1200


    # IFERROR(AX5*($AJ$5/AJ5)*($AE$5/AE5),0)
    def calculate_normalized_flux(
        self, df, bl_trans_membrane_pressure, bl_temperature_correction_factor
    ):
        return (
            df["operating_flux"]
            * (bl_trans_membrane_pressure / df["trans_membrane_pressure"])
            * (bl_temperature_correction_factor / df["temperature_correction_factor"])
        )


    # IFERROR(AX5/AV5,0)
    def calculate_specific_flux(self, df):
        try:
            return df["operating_flux"] / df["net_driving_pressure"]
        except ZeroDivisionError:
            return 0


    # IFERROR(AY6*((AJ6+AM6)/($AJ$5+$AM$5))*($AE$5/AE6),0)
    def calculate_normalized_specific_flux(self, df):
        try:
            return df["normalized_flux"] / df["net_driving_pressure"]
        except ZeroDivisionError:
            return 0


    def normalized_permeate_flow(self, df, i):
        if "TT_1_C" not in df:
            df["TT_1_C"] = df.apply(self.calculate_TT_1_C, axis=1)
        if "coefficient" not in df:
            df["coefficient"] = df.apply(self.calulate_coefficient, axis=1)
        if "temperature_correction_factor" not in df:
            df["temperature_correction_factor"] = df.apply(
                self.calculate_temperature_correction_factor, axis=1
            )
        if "lead_element_flow" not in df:
            df["lead_element_flow"] = df.apply(self.calculate_lead_element_flow, axis=1)
        if "module_recovery" not in df:
            df["module_recovery"] = df.apply(self.calculate_module_recovery, axis=1)
        if "feed_cond_C" not in df:
            df["feed_cond_C"] = df.apply(self.calculate_feed_cond_C, axis=1)
        if "feed_reject_cond_C" not in df:
            df["feed_reject_cond_C"] = df.apply(
                self.calculate_feed_reject_cond_C, axis=1)
        if "osmotic_pressure" not in df:
            df["osmotic_pressure"] = df.apply(self.calculate_osmotic_pressure, axis=1)
        if "trans_membrane_pressure" not in df:
            df["trans_membrane_pressure"] = df.apply(
                self.calculate_trans_membrane_pressure, axis=1
            )

        args = (
            df["trans_membrane_pressure"].values[-1],
            df["temperature_correction_factor"].values[-1],
        )
        df["normalized_permeate_flow"] = df.apply(
            self.calculate_normalized_permeate_flow, axis=1, args=args
        )
        return df


    def normalized_differential_pressure(self, df, i):
        if "TT_1_C" not in df:
            df["TT_1_C"] = df.apply(self.calculate_TT_1_C, axis=1)
        if "coefficient" not in df:
            df["coefficient"] = df.apply(self.calulate_coefficient, axis=1)
        if "temperature_correction_factor" not in df:
            df["temperature_correction_factor"] = df.apply(
                self.calculate_temperature_correction_factor, axis=1
            )

        args = (df["temperature_correction_factor"].values[-1],)
        df["normalized_differential_pressure"] = df.apply(
            self.calculate_normalized_differential_pressure, axis=1, args=args
        )
        return df


    def normalized_permeate_TDS(self, df, i):
        if "TT_1_C" not in df:
            df["TT_1_C"] = df.apply(self.calculate_TT_1_C, axis=1)
        if "osmotic_pressure_Posmo_p" not in df:
            df["osmotic_pressure_Posmo_p"] = df.apply(
                self.calculate_osmotic_pressure_Posmo_p, axis=1
            )
        if "lead_element_flow" not in df:
            df["lead_element_flow"] = df.apply(self.calculate_lead_element_flow, axis=1)
        if "module_recovery" not in df:
            df["module_recovery"] = df.apply(self.calculate_module_recovery, axis=1)
        if "feed_cond_C" not in df:
            df["feed_cond_C"] = df.apply(self.calculate_feed_cond_C, axis=1)
        if "feed_reject_cond_C" not in df:
            df["feed_reject_cond_C"] = df.apply(
                self.calculate_feed_reject_cond_C, axis=1)

        if "osmotic_pressure" not in df:
            df["osmotic_pressure"] = df.apply(self.calculate_osmotic_pressure, axis=1)
        if "trans_membrane_pressure" not in df:
            df["trans_membrane_pressure"] = df.apply(
                self.calculate_trans_membrane_pressure, axis=1
            )

        args = (
            df["trans_membrane_pressure"].values[-1],
            df["feed_reject_cond_C"].values[-1],
            df["osmotic_pressure_Posmo_p"].values[-1],
        )
        df["normalized_permeate_TDS"] = df.apply(
            self.calculate_normalized_permeate_TDS, axis=1, args=args
        )
        return df


    def net_driving_pressure(self, df, i):
        if "TT_1_C" not in df:
            log.debug('normalization - calculate_TT_1_C')
            df["TT_1_C"] = df.apply(self.calculate_TT_1_C, axis=1)
        if "lead_element_flow" not in df:
            log.debug('normalization - calculate_lead_element_flow')
            df["lead_element_flow"] = df.apply(self.calculate_lead_element_flow, axis=1)
        if "module_recovery" not in df:
            log.debug('normalization - calculate_module_recovery')
            df["module_recovery"] = df.apply(self.calculate_module_recovery, axis=1)
        if "feed_cond_C" not in df:
            log.debug('normalization - calculate_feed_cond_C')
            df["feed_cond_C"] = df.apply(self.calculate_feed_cond_C, axis=1)
        if "feed_reject_cond_C" not in df:
            log.debug('normalization - calculate_feed_reject_cond_C')
            df["feed_reject_cond_C"] = df.apply(
                self.calculate_feed_reject_cond_C, axis=1)
        if "osmotic_pressure" not in df:
            log.debug('normalization - calculate_osmotic_pressure')
            df["osmotic_pressure"] = df.apply(self.calculate_osmotic_pressure, axis=1)

        if "osmotic_pressure_Posmo_p" not in df:
            log.debug('normalization - calculate_osmotic_pressure_Posmo_p')
            df["osmotic_pressure_Posmo_p"] = df.apply(
                self.calculate_osmotic_pressure_Posmo_p, axis=1
            )
        log.debug('normalization - calculate_net_driving_pressure')
        df["net_driving_pressure"] = df.apply(self.calculate_net_driving_pressure, axis=1)
        return df


    def normalized_flux(self, df, i):
        if "TT_1_C" not in df:
            df["TT_1_C"] = df.apply(self.calculate_TT_1_C, axis=1)
        if "lead_element_flow" not in df:
            df["lead_element_flow"] = df.apply(self.calculate_lead_element_flow, axis=1)
        if "module_recovery" not in df:
            df["module_recovery"] = df.apply(self.calculate_module_recovery, axis=1)
        if "feed_cond_C" not in df:
            df["feed_cond_C"] = df.apply(self.calculate_feed_cond_C, axis=1)
        if "feed_reject_cond_C" not in df:
            df["feed_reject_cond_C"] = df.apply(
                self.calculate_feed_reject_cond_C, axis=1)
        if "osmotic_pressure" not in df:
            df["osmotic_pressure"] = df.apply(self.calculate_osmotic_pressure, axis=1)
        if "trans_membrane_pressure" not in df:
            df["trans_membrane_pressure"] = df.apply(
                self.calculate_trans_membrane_pressure, axis=1
            )

        if "coefficient" not in df:
            df["coefficient"] = df.apply(self.calulate_coefficient, axis=1)
        if "temperature_correction_factor" not in df:
            df["temperature_correction_factor"] = df.apply(
                self.calculate_temperature_correction_factor, axis=1
            )

        if "operating_flux" not in df:
            df["operating_flux"] = df.apply(self.calculate_operating_flux, axis=1)

        args = (
            df["trans_membrane_pressure"].values[-1],
            df["temperature_correction_factor"].values[-1],
        )
        df["normalized_flux"] = df.apply(self.calculate_normalized_flux,
                                        axis=1, args=args)
        return df


    def normalized_salt_passage(self, df, i):
        if "avg_feed" not in df:
            df["avg_feed"] = df.apply(self.calculate_avg_feed, axis=1)
        if "avg_membrane_rejection" not in df:
            df["avg_membrane_rejection"] = df.apply(
                self.calculate_avg_membrane_rejection, axis=1
            )

        if "TT_1_C" not in df:
            df["TT_1_C"] = df.apply(self.calculate_TT_1_C, axis=1)
        if "coefficient" not in df:
            df["coefficient"] = df.apply(self.calulate_coefficient, axis=1)
        if "temperature_correction_factor" not in df:
            df["temperature_correction_factor"] = df.apply(
                self.calculate_temperature_correction_factor, axis=1
            )

        args = (df["temperature_correction_factor"].values[-1],)
        df["normalized_salt_passage"] = df.apply(
            self.calculate_normalized_salt_passage, axis=1, args=args
        )
        return df


    def normalized_specific_flux(self, df, i):
        if "operating_flux" not in df:
            df["operating_flux"] = df.apply(self.calculate_operating_flux, axis=1)

        if "TT_1_C" not in df:
            df["TT_1_C"] = df.apply(self.calculate_TT_1_C, axis=1)
        if "lead_element_flow" not in df:
            df["lead_element_flow"] = df.apply(self.calculate_lead_element_flow, axis=1)
        if "module_recovery" not in df:
            df["module_recovery"] = df.apply(self.calculate_module_recovery, axis=1)
        if "feed_cond_C" not in df:
            df["feed_cond_C"] = df.apply(self.calculate_feed_cond_C, axis=1)
        if "feed_reject_cond_C" not in df:
            df["feed_reject_cond_C"] = df.apply(
                self.calculate_feed_reject_cond_C, axis=1)
        if "osmotic_pressure" not in df:
            df["osmotic_pressure"] = df.apply(self.calculate_osmotic_pressure, axis=1)

        if "osmotic_pressure_Posmo_p" not in df:
            df["osmotic_pressure_Posmo_p"] = df.apply(
                self.calculate_osmotic_pressure_Posmo_p, axis=1
            )

        if "trans_membrane_pressure" not in df:
            df["trans_membrane_pressure"] = df.apply(
                self.calculate_trans_membrane_pressure, axis=1
            )

        if "coefficient" not in df:
            df["coefficient"] = df.apply(self.calulate_coefficient, axis=1)
        if "temperature_correction_factor" not in df:
            df["temperature_correction_factor"] = df.apply(
                self.calculate_temperature_correction_factor, axis=1
            )

        if "net_driving_pressure" not in df:
            df["net_driving_pressure"] = df.apply(
                self.calculate_net_driving_pressure, axis=1)
        if "specific_flux" not in df:
            df["Tag" + str(i + 1)] = df.apply(self.calculate_specific_flux, axis=1)

        args = (
            df["trans_membrane_pressure"].values[-1],
            df["temperature_correction_factor"].values[-1],
        )
        df["normalized_flux"] = df.apply(self.calculate_normalized_flux,
                                        axis=1, args=args)

        df["normalized_specific_flux"] = df.apply(
            self.calculate_normalized_specific_flux, axis=1)
        return df