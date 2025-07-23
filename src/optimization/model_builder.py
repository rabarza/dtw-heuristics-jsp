from ortools.sat.python import cp_model
import pandas as pd
from src.utils.helpers import build_schedule_results


def solve_jobshop(
    df: pd.DataFrame,
    time_scale: int = 60,
    H_daily_hours: int = 10,
    enforce_daily_limit: bool = True,
    max_time: int = 100,
):
    # Preprocesar
    df = df.copy()
    df["processing_time_scaled"] = (
        (df["processing_time"] * time_scale).round().astype(int)
    )

    # Crear estructura de datos para el modelo
    jobs_data = {}
    for job_id, job_df in df.groupby("job_id"):
        job_df = job_df.sort_values("operation_index")
        jobs_data[job_id] = [
            (int(row["machine_id"]), int(row["processing_time_scaled"]))
            for _, row in job_df.iterrows()
        ]

    # Crear modelo
    model = cp_model.CpModel()
    horizon = int(df["processing_time_scaled"].sum() * 2)
    all_tasks = {}
    job_ends = {}

    for job_id, operations in jobs_data.items():
        previous_end = None
        for task_id, (machine, duration) in enumerate(operations):
            suffix = f"_{job_id}_{task_id}"
            start_var = model.NewIntVar(0, horizon, "start" + suffix)
            end_var = model.NewIntVar(0, horizon, "end" + suffix)
            interval = model.NewIntervalVar(
                start_var, duration, end_var, "interval" + suffix
            )
            all_tasks[(job_id, task_id)] = (start_var, end_var, interval, machine)

            if previous_end is not None:
                model.Add(start_var >= previous_end)
            previous_end = end_var
        job_ends[job_id] = previous_end

    # Restricciones de máquina
    machine_to_intervals = {}
    for (job_id, task_id), (_, _, interval, machine) in all_tasks.items():
        machine_to_intervals.setdefault(machine, []).append(interval)
    for machine, intervals in machine_to_intervals.items():
        model.AddNoOverlap(intervals)

    # Restricción diaria opcional
    if enforce_daily_limit:
        H_daily = int(H_daily_hours * time_scale)
        for (job_id, task_id), (start_var, end_var, _, _) in all_tasks.items():
            day_start = model.NewIntVar(0, 1000, f"day_start_{job_id}_{task_id}")
            day_end = model.NewIntVar(0, 1000, f"day_end_{job_id}_{task_id}")
            model.AddDivisionEquality(day_start, start_var, H_daily)
            model.AddDivisionEquality(day_end, end_var, H_daily)
            model.Add(day_start == day_end)

    # Objetivo
    makespan = model.NewIntVar(0, horizon, "makespan")
    model.AddMaxEquality(makespan, list(job_ends.values()))
    model.Minimize(makespan)

    # Resolver
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = max_time
    status = solver.Solve(model)

    # Construir schedule_df
    results = []
    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        results = build_schedule_results(jobs_data, all_tasks, solver, time_scale)
    else:
        print("❌ No se encontró solución factible.")
        return pd.DataFrame()
    return pd.DataFrame(results)


def solve_jobshop_two_stage(
    df: pd.DataFrame,
    time_scale: int = 60,
    H_daily_hours: int = 10,
    enforce_daily_limit: bool = True,
    max_time_stage1: int = 60,
    max_time_stage2: int = 60,
):
    from src.utils.helpers import build_schedule_results
    df = df.copy()
    df["processing_time_scaled"] = (
        (df["processing_time"] * time_scale).round().astype(int)
    )

    def get_jobs_data(df):
        jobs_data = {}
        for job_id, job_df in df.groupby("job_id"):
            job_df = job_df.sort_values("operation_index")
            jobs_data[job_id] = [
                (int(row["machine_id"]), int(row["processing_time_scaled"]))
                for _, row in job_df.iterrows()
            ]
        return jobs_data

    jobs_data = get_jobs_data(df)
    horizon = int(df["processing_time_scaled"].sum() * 2)

    def build_model():
        model = cp_model.CpModel()
        all_tasks = {}
        job_ends = {}
        for job_id, operations in jobs_data.items():
            previous_end = None
            for task_id, (machine, duration) in enumerate(operations):
                suffix = f"_{job_id}_{task_id}"
                start_var = model.NewIntVar(0, horizon, "start" + suffix)
                end_var = model.NewIntVar(0, horizon, "end" + suffix)
                interval = model.NewIntervalVar(start_var, duration, end_var, "interval" + suffix)
                all_tasks[(job_id, task_id)] = (start_var, end_var, interval, machine)

                # Precedencia
                if previous_end is not None:
                    model.Add(start_var >= previous_end)
                previous_end = end_var
            job_ends[job_id] = previous_end

        # No solapamiento en máquinas
        machine_to_intervals = {}
        for (job_id, task_id), (_, _, interval, machine) in all_tasks.items():
            machine_to_intervals.setdefault(machine, []).append(interval)
        for machine, intervals in machine_to_intervals.items():
            model.AddNoOverlap(intervals)

        # Restricción diaria opcional
        if enforce_daily_limit:
            H_daily = int(H_daily_hours * time_scale)
            for (job_id, task_id), (start_var, end_var, _, _) in all_tasks.items():
                day_start = model.NewIntVar(0, 1000, f"day_start_{job_id}_{task_id}")
                day_end = model.NewIntVar(0, 1000, f"day_end_{job_id}_{task_id}")
                model.AddDivisionEquality(day_start, start_var, H_daily)
                model.AddDivisionEquality(day_end, end_var, H_daily)
                model.Add(day_start == day_end)
        makespan = model.NewIntVar(0, horizon, "makespan")
        model.AddMaxEquality(makespan, list(job_ends.values()))
        return model, all_tasks, job_ends, makespan

    # Etapa 1: Minimizar makespan
    model1, all_tasks1, job_ends1, makespan1 = build_model()
    model1.Minimize(makespan1)
    solver1 = cp_model.CpSolver()
    solver1.parameters.max_time_in_seconds = max_time_stage1
    status1 = solver1.Solve(model1)
    if status1 not in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        print("❌ No se encontró solución factible en la etapa 1.")
        return pd.DataFrame()
    best_makespan = solver1.Value(makespan1)
    print(f"✅ Makespan mínimo encontrado: {best_makespan/time_scale} horas")

    # Etapa 2: Minimizar suma de tiempos de inicio
    model2, all_tasks2, job_ends2, makespan2 = build_model()
    model2.Add(makespan2 == best_makespan)
    total_start = sum(start_var for (start_var, _, _, _) in all_tasks2.values())
    model2.Minimize(total_start)
    solver2 = cp_model.CpSolver()
    solver2.parameters.max_time_in_seconds = max_time_stage2
    status2 = solver2.Solve(model2)
    if status2 not in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        print("❌ No se encontró solución factible en la etapa 2.")
        return
    results = build_schedule_results(jobs_data, all_tasks2, solver2, time_scale)
    return pd.DataFrame(results)
