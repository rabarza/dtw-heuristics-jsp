from pydantic import BaseModel
from typing import List, Optional


class TaskInput(BaseModel):
    job_id: int
    operation_index: int
    machine_id: int
    processing_time: float  # en horas
    setup_time: Optional[float] = None  # en horas, opcional


class SolveRequest(BaseModel):
    tasks: List[TaskInput]
    H_daily_hours: int = 8
    enforce_daily_limit: bool = True
    time_scale: int = 60
    max_time: int = 100
    use_setup_times: bool = False
    max_time_stage1: Optional[int] = None
    max_time_stage2: Optional[int] = None


class TaskOutput(BaseModel):
    job_id: int
    operation_index: int
    machine_id: int
    start_time_hours: float
    end_time_hours: float
    duration_hours: float
    processing_time_hours: Optional[float] = None
    setup_time_hours: Optional[float] = None
    start_day: int
    start_hour_of_day: float
    end_day: int
    end_hour_of_day: float


class SolveResponse(BaseModel):
    status: str
    makespan: float
    schedule: List[TaskOutput]
