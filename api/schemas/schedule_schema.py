from pydantic import BaseModel
from typing import List

class TaskInput(BaseModel):
    job_id: int
    operation_id: int
    machine_id: int
    processing_time: float  # en horas

class SolveRequest(BaseModel):
    tasks: List[TaskInput]
    H_daily_hours: int = 8
    enforce_daily_limit: bool = True

class TaskOutput(BaseModel):
    job_id: int
    operation_id: int
    machine_id: int
    start_time_hours: float
    end_time_hours: float
    duration_hours: float
    start_day: int
    start_hour_of_day: float
    end_day: int
    end_hour_of_day: float

class SolveResponse(BaseModel):
    makespan: float
    schedule: List[TaskOutput]
