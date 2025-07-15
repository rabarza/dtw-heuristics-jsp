import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd


def plot_schedule(schedule_df: pd.DataFrame, H_daily_hours: int = 8, figsize=(20, 8)):
    """
    Dibuja un diagrama de Gantt del schedule y marca límites de jornadas diarias.

    Parameters
    ----------
    schedule_df : pd.DataFrame
        Debe contener columnas: job_id, operation_index, machine_id, start_time_hours, end_time_hours, duration_hours
    H_daily_hours : int
        Número de horas por jornada laboral.
    figsize : tuple
        Tamaño de la figura.
    """
    # Ordenar por tiempo de inicio
    schedule_df_sorted = schedule_df.sort_values(by="start_time_hours").copy()

    # Crear figura
    fig, ax = plt.subplots(figsize=figsize)

    # Color distinto por máquina
    machines = schedule_df_sorted["machine_id"].unique()
    color_map = {m: plt.cm.tab20(i % 20) for i, m in enumerate(machines)}

    yticks, ylabels = [], []
    y = 0

    # Verificación opcional: ¿alguna operación cruza días?
    for _, row in schedule_df_sorted.iterrows():
        start_day = int(row["start_time_hours"] // H_daily_hours)
        end_day = int(row["end_time_hours"] // H_daily_hours)
        if start_day != end_day:
            print(
                f"⚠️ Advertencia: Job {row['job_id']} operación {row['operation_index']} cruza días ({row['start_time_hours']}h → {row['end_time_hours']}h)."
            )

    # Graficar cada job
    for job_id, job_df in schedule_df_sorted.groupby("job_id"):
        for _, row in job_df.iterrows():
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
    ax.legend(handles=patches, bbox_to_anchor=(1, 1), loc="upper right")
    plt.tight_layout()
    plt.show()
