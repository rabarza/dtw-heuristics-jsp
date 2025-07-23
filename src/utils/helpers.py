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


def build_schedule_results(jobs_data, all_tasks, solver, time_scale):
    results = []
    for job_id, operations in jobs_data.items():
        for task_id in range(len(operations)):
            start_var, end_var, _, machine = all_tasks[(job_id, task_id)]
            start_h = solver.Value(start_var) / time_scale
            end_h = solver.Value(end_var) / time_scale
            results.append(
                {
                    "job_id": job_id,
                    "operation_index": task_id,
                    "machine_id": machine,
                    "start_time_hours": round(start_h, 2),
                    "end_time_hours": round(end_h, 2),
                    "duration_hours": round(end_h - start_h, 2),
                }
            )
    return results
