from fastapi import APIRouter, HTTPException
from api.schemas.schedule_schema import (
    SolveRequest,
    SolveResponse,
    TaskOutput,
)
import pandas as pd
from src.optimization.model_builder import (
    solve_jobshop,
    solve_jobshop_two_stage,
)
from src.utils.helpers import add_day_hour_columns

router = APIRouter()


def _build_output(schedule_df_human):
    output = []
    for _, row in schedule_df_human.iterrows():
        output_kwargs = dict(
            job_id=int(row["job_id"]),
            operation_index=int(row["operation_index"]),
            machine_id=int(row["machine_id"]),
            start_time_hours=row["start_time_hours"],
            end_time_hours=row["end_time_hours"],
            duration_hours=row["duration_hours"],
            start_day=int(row["start_day"]),
            start_hour_of_day=row["start_hour_of_day"],
            end_day=int(row["end_day"]),
            end_hour_of_day=row["end_hour_of_day"],
        )
        if "processing_time_hours" in row:
            output_kwargs["processing_time_hours"] = row["processing_time_hours"]
        if "setup_time_hours" in row:
            output_kwargs["setup_time_hours"] = row["setup_time_hours"]
        output.append(TaskOutput(**output_kwargs))
    return output

@router.post("/solve", response_model=SolveResponse)
def solve_schedule(req: SolveRequest):
    data = [t.model_dump() for t in req.tasks]
    df = pd.DataFrame(data)
    # Determinar el tiempo máximo a usar
    max_time = req.max_time_stage1 if req.max_time_stage1 is not None else req.max_time
    schedule_df = solve_jobshop(
        df,
        time_scale=req.time_scale,
        H_daily_hours=req.H_daily_hours,
        enforce_daily_limit=req.enforce_daily_limit,
        use_setup_times=req.use_setup_times,
        max_time=max_time,
        fixed_starts=req.fixed_starts,
    )
    if schedule_df.empty:
        return SolveResponse(status="infeasible", makespan=0.0, schedule=[])
    schedule_df_human = add_day_hour_columns(
        schedule_df, H_daily_hours=req.H_daily_hours
    )
    makespan = (
        schedule_df_human["end_time_hours"].max()
        if not schedule_df_human.empty
        else 0.0
    )
    output = _build_output(schedule_df_human)
    return SolveResponse(status="optimal", makespan=makespan, schedule=output)

@router.post("/solve_two_stage", response_model=SolveResponse)
def solve_schedule_two_stage(req: SolveRequest):
    data = [t.model_dump() for t in req.tasks]
    df = pd.DataFrame(data)
    schedule_df = solve_jobshop_two_stage(
        df,
        time_scale=req.time_scale,
        H_daily_hours=req.H_daily_hours,
        enforce_daily_limit=req.enforce_daily_limit,
        use_setup_times=req.use_setup_times,
        max_time_stage1=req.max_time_stage1 or req.max_time,
        max_time_stage2=req.max_time_stage2 or 60,
        fixed_starts=req.fixed_starts,
    )
    if schedule_df is None or schedule_df.empty:
        return SolveResponse(status="infeasible", makespan=0.0, schedule=[])
    schedule_df_human = add_day_hour_columns(
        schedule_df, H_daily_hours=req.H_daily_hours
    )
    makespan = (
        schedule_df_human["end_time_hours"].max()
        if not schedule_df_human.empty
        else 0.0
    )
    output = _build_output(schedule_df_human)
    return SolveResponse(status="optimal", makespan=makespan, schedule=output)

