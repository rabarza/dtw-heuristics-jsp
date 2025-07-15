from ortools.sat.python import cp_model
import pandas as pd


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
    else:
        print("❌ No se encontró solución factible.")
        return pd.DataFrame()
    return pd.DataFrame(results)
