import pandas as pd


def add_day_hour_columns(schedule_df: pd.DataFrame, H_daily_hours: int = 8):
    df_human = schedule_df.copy()
    df_human["start_day"] = (df_human["start_time_hours"] // H_daily_hours).astype(int)
    df_human["start_hour_of_day"] = (
        df_human["start_time_hours"] % H_daily_hours
    ).round(2)
    df_human["end_day"] = (df_human["end_time_hours"] // H_daily_hours).astype(int)
    df_human["end_hour_of_day"] = (df_human["end_time_hours"] % H_daily_hours).round(2)
    return df_human
