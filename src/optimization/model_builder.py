from ortools.sat.python import cp_model
import pandas as pd
from src.utils.helpers import build_schedule_results
import warnings


def preprocess_jobshop_df(df, time_scale, use_setup_times):
    df = df.copy()
    df["processing_time_scaled"] = (
        (df["processing_time"] * time_scale).round().astype(int).fillna(0)
    )
    if use_setup_times:
        if "setup_time" in df.columns:
            df["setup_time_scaled"] = (
                (df["setup_time"] * time_scale).round().astype(int).fillna(0)
            )
        else:
            warnings.warn(
                "La columna 'setup_time' no está presente. Se ignorarán los tiempos de setup."
            )
            use_setup_times = False
    return df, use_setup_times


def build_jobs_data(df, use_setup_times):
    jobs_data = {}
    for job_id, job_df in df.groupby("job_id"):
        job_df = job_df.sort_values("operation_index")
        if use_setup_times:
            jobs_data[job_id] = [
                (
                    int(row["machine_id"]),
                    int(row["processing_time_scaled"]),
                    int(row["setup_time_scaled"] if not pd.isna(row["setup_time_scaled"]) else 0),
                )
                for _, row in job_df.iterrows()
            ]
        else:
            jobs_data[job_id] = [
                (int(row["machine_id"]), int(row["processing_time_scaled"]))
                for _, row in job_df.iterrows()
            ]
    return jobs_data


def create_cp_variables_and_constraints(
    model,
    jobs_data,
    horizon,
    enforce_daily_limit,
    H_daily_hours,
    time_scale,
    use_setup_times,
    start_time_fixed_map=None,
):
    all_tasks = {}
    job_ends = {}
    for job_id, operations in jobs_data.items():
        previous_end = None
        for task_id, op in enumerate(operations):
            if use_setup_times:
                machine, duration, setup = op
                total_duration = duration + setup
            else:
                machine, duration = op
                total_duration = duration
            suffix = f"_{job_id}_{task_id}"
            start_var = model.NewIntVar(0, horizon, "start" + suffix)
            end_var = model.NewIntVar(0, horizon, "end" + suffix)
            interval = model.NewIntervalVar(
                start_var, total_duration, end_var, "interval" + suffix
            )
            all_tasks[(job_id, task_id)] = (start_var, end_var, interval, machine)
            # Restricción de inicio fijo si corresponde
            if start_time_fixed_map is not None:
                key = (job_id, task_id)
                if key in start_time_fixed_map and start_time_fixed_map[key] is not None:
                    model.Add(start_var == int(start_time_fixed_map[key] * time_scale))
            if previous_end is not None:
                model.Add(start_var >= previous_end)
            previous_end = end_var
        job_ends[job_id] = previous_end
    # No solapamiento por máquina
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
    return all_tasks, job_ends


def build_jobshop_results(jobs_data, all_tasks, solver, time_scale, use_setup_times):
    results = []
    for job_id, operations in jobs_data.items():
        for task_id, op in enumerate(operations):
            start_var, end_var, _, machine = all_tasks[(job_id, task_id)]
            start_h = solver.Value(start_var) / time_scale
            end_h = solver.Value(end_var) / time_scale
            duration_h = end_h - start_h
            if use_setup_times:
                _, duration, setup = op
                setup_h = setup / time_scale
                process_h = duration / time_scale
                results.append(
                    {
                        "job_id": job_id,
                        "operation_index": task_id,
                        "machine_id": machine,
                        "start_time_hours": round(start_h, 2),
                        "end_time_hours": round(end_h, 2),
                        "duration_hours": round(duration_h, 2),
                        "setup_time_hours": round(setup_h, 2),
                        "processing_time_hours": round(process_h, 2),
                    }
                )
            else:
                _, duration = op
                process_h = duration / time_scale
                results.append(
                    {
                        "job_id": job_id,
                        "operation_index": task_id,
                        "machine_id": machine,
                        "start_time_hours": round(start_h, 2),
                        "end_time_hours": round(end_h, 2),
                        "duration_hours": round(duration_h, 2),
                        "processing_time_hours": round(process_h, 2),
                    }
                )
    return results


def build_start_time_fixed_map(fixed_starts):
    if not fixed_starts:
        return None
    start_time_fixed_map = {}
    for job_id, lst in fixed_starts.items():
        for item in lst:
            key = (int(job_id), int(item['operation_index']) if isinstance(item, dict) else item.operation_index)
            val = item['start_time_fixed'] if isinstance(item, dict) else item.start_time_fixed
            start_time_fixed_map[key] = val
    return start_time_fixed_map


def solve_jobshop(
    df: pd.DataFrame,
    time_scale: int = 60,
    H_daily_hours: int = 10,
    enforce_daily_limit: bool = True,
    use_setup_times: bool = False,
    max_time: int = 100,
    fixed_starts: dict = None,
):
    """
    Resuelve un Job Shop Scheduling, con opción de considerar tiempos de setup.
    """
    df, use_setup_times = preprocess_jobshop_df(df, time_scale, use_setup_times)
    jobs_data = build_jobs_data(df, use_setup_times)
    start_time_fixed_map = build_start_time_fixed_map(fixed_starts)
    if use_setup_times:
        horizon = int(
            (df["processing_time_scaled"] + df["setup_time_scaled"]).sum() * 2
        )
    else:
        horizon = int(df["processing_time_scaled"].sum() * 2)
    model = cp_model.CpModel()
    all_tasks, job_ends = create_cp_variables_and_constraints(
        model,
        jobs_data,
        horizon,
        enforce_daily_limit,
        H_daily_hours,
        time_scale,
        use_setup_times,
        start_time_fixed_map,
    )
    makespan = model.NewIntVar(0, horizon, "makespan")
    model.AddMaxEquality(makespan, list(job_ends.values()))
    model.Minimize(makespan)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = max_time
    status = solver.Solve(model)
    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        results = build_jobshop_results(jobs_data, all_tasks, solver, time_scale, use_setup_times)
    else:
        print("❌ No se encontró solución factible.")
        return pd.DataFrame()
    return pd.DataFrame(results)


def solve_jobshop_two_stage(
    df: pd.DataFrame,
    time_scale: int = 60,
    H_daily_hours: int = 10,
    enforce_daily_limit: bool = True,
    use_setup_times: bool = False,
    max_time_stage1: int = 60,
    max_time_stage2: int = 60,
    fixed_starts: dict = None,
):
    df, use_setup_times = preprocess_jobshop_df(df, time_scale, use_setup_times)
    jobs_data = build_jobs_data(df, use_setup_times)
    start_time_fixed_map = build_start_time_fixed_map(fixed_starts)
    if use_setup_times:
        horizon = int(
            (df["processing_time_scaled"] + df["setup_time_scaled"]).sum() * 2
        )
    else:
        horizon = int(df["processing_time_scaled"].sum() * 2)
    def build_model():
        model = cp_model.CpModel()
        all_tasks, job_ends = create_cp_variables_and_constraints(
            model,
            jobs_data,
            horizon,
            enforce_daily_limit,
            H_daily_hours,
            time_scale,
            use_setup_times,
            start_time_fixed_map,
        )
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
    if status2 in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        results = build_jobshop_results(jobs_data, all_tasks2, solver2, time_scale, use_setup_times)
        return pd.DataFrame(results)
    else:
        print("❌ No se encontró solución factible en la etapa 2. Se devuelven resultados de la etapa 1.")
        results = build_jobshop_results(jobs_data, all_tasks1, solver1, time_scale, use_setup_times)
        return pd.DataFrame(results)