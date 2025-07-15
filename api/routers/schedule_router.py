from fastapi import APIRouter, HTTPException
from api.schemas.schedule_schema import SolveRequest, SolveResponse, TaskOutput
import pandas as pd
from src.optimization.model_builder import solve_jobshop
from src.utils.helpers import add_day_hour_columns

router = APIRouter()


@router.post("/solve", response_model=SolveResponse)
def solve_schedule(req: SolveRequest):
    # Convertir lista de tareas a DataFrame
    data = [t.model_dump() for t in req.tasks]
    df = pd.DataFrame(data)

    # Ejecutar optimización
    schedule_df = solve_jobshop(
        df,
        time_scale=60,
        H_daily_hours=req.H_daily_hours,
        enforce_daily_limit=req.enforce_daily_limit,
        max_time=100,
    )
    # Si no se encontró solución
    if schedule_df.empty:
        return SolveResponse(status="infeasible", makespan=0.0, schedule=[])

    # Agregar columnas legibles
    schedule_df_human = add_day_hour_columns(
        schedule_df, H_daily_hours=req.H_daily_hours
    )

    # Calcular makespan
    makespan = (
        schedule_df_human["end_time_hours"].max()
        if not schedule_df_human.empty
        else 0.0
    )

    # Convertir a salida
    output = [
        TaskOutput(
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
        for _, row in schedule_df_human.iterrows()
    ]

    return SolveResponse(status="optimal", makespan=makespan, schedule=output)
