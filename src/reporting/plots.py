import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd


def plot_schedule(schedule_df: pd.DataFrame, H_daily_hours: int = 8, figsize=(20, 8)):
    """
    Dibuja un diagrama de Gantt del schedule y marca límites de jornadas diarias.
    Si existen columnas de setup, grafica el setup en gris y el procesamiento en color de máquina.
    """
    schedule_df_sorted = schedule_df.sort_values(by="start_time_hours").copy()
    fig, ax = plt.subplots(figsize=figsize)
    machines = schedule_df_sorted["machine_id"].unique()
    color_map = {m: plt.cm.tab20(i % 20) for i, m in enumerate(machines)}
    yticks, ylabels = [], []
    y = 0
    has_setup = "setup_time_hours" in schedule_df_sorted.columns and "processing_time_hours" in schedule_df_sorted.columns
    for _, row in schedule_df_sorted.iterrows():
        start_day = int(row["start_time_hours"] // H_daily_hours)
        end_day = int(row["end_time_hours"] // H_daily_hours)
        if start_day != end_day:
            print(
                f"⚠️ Advertencia: Job {row['job_id']} operación {row['operation_index']} cruza días ({row['start_time_hours']}h → {row['end_time_hours']}h)."
            )
    for job_id, job_df in schedule_df_sorted.groupby("job_id"):
        for _, row in job_df.iterrows():
            if has_setup:
                # Graficar setup (gris)
                if row["setup_time_hours"] > 0:
                    ax.barh(
                        y,
                        row["setup_time_hours"],
                        left=row["start_time_hours"],
                        color="#888888",
                        edgecolor="black",
                        hatch="//",
                        label="Setup" if y == 0 else None,
                    )
                # Graficar procesamiento (color máquina)
                ax.barh(
                    y,
                    row["processing_time_hours"],
                    left=row["start_time_hours"] + row["setup_time_hours"],
                    color=color_map[row["machine_id"]],
                    edgecolor="black",
                )
                ax.text(
                    row["start_time_hours"] + row["setup_time_hours"] + row["processing_time_hours"] / 2,
                    y,
                    int(row["operation_index"]),
                    va="center",
                    ha="center",
                    fontsize=8,
                    color="white",
                )
            else:
                ax.barh(
                    y,
                    row["duration_hours"],
                    left=row["start_time_hours"],
                    color=color_map[row["machine_id"]],
                    edgecolor="black",
                )
                ax.text(
                    row["start_time_hours"] + row["duration_hours"] / 2,
                    y,
                    int(row["operation_index"]),
                    va="center",
                    ha="center",
                    fontsize=8,
                    color="white",
                )
        yticks.append(y)
        ylabels.append(f"Job {job_id}")
        y += 1
    max_time = schedule_df_sorted["end_time_hours"].max()
    for t in range(H_daily_hours, int(max_time) + H_daily_hours, H_daily_hours):
        ax.axvline(x=t, color="red", linestyle="--", linewidth=1)
    ax.set_yticks(yticks)
    ax.set_yticklabels(ylabels)
    ax.set_xlabel("Tiempo (horas)")
    ax.set_title("Diagrama de Gantt del Job Shop")
    patches = [
        mpatches.Patch(color=color_map[m], label=f"Máquina {m}") for m in machines
    ]
    if has_setup:
        patches.append(mpatches.Patch(facecolor="#888888", hatch="//", label="Setup"))
    ax.legend(handles=patches, bbox_to_anchor=(1, 1), loc="upper right")
    plt.tight_layout()
    plt.show()
