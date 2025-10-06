### Job Shop Scheduling API

Proyecto para resolver Job Shop Scheduling (JSP) con FastAPI y OR-Tools (CP-SAT), incluyendo:

- Uso opcional de tiempos de setup por operación
- Restricción de jornada diaria
- Variante en dos etapas (minimiza makespan y luego suma de inicios)
- Fijación de inicios de operaciones vía `fixed_starts`

### Tecnologías

- Python 3.10+
- FastAPI
- OR-Tools (CP-SAT)
- Pandas

### Estructura relevante

- `api/routers/schedule_router.py`: endpoints de la API
- `api/schemas/schedule_schema.py`: esquemas de request/response
- `src/optimization/model_builder.py`: modelos de optimización
- `src/utils/helpers.py`: utilidades (por ejemplo, columnas legibles de día/hora)
- `docs/`: documentación adicional (formulación matemática)

### Ejecutar localmente

1. Crear y activar entorno, luego instalar dependencias:

```bash
pip install -r requirements.txt
```

2. Ejecutar API:

```bash
uvicorn api.main:app --reload
```

La API quedará disponible en `http://localhost:8000` y la documentación interactiva en `http://localhost:8000/docs`.

### Endpoints

- POST `/solve`: resuelve JSP en una etapa (minimiza makespan)
- POST `/solve_two_stage`: resuelve en dos etapas (1) makespan, (2) suma de inicios manteniendo makespan

Ambos endpoints comparten el mismo esquema de entrada y salida.

### Request (entrada)

- `operations` (lista de operaciones):
  - `job_id` (int)
  - `operation_index` (int)
  - `machine_id` (int)
  - `processing_time` (float, horas)
  - `setup_time` (float, horas, opcional)
- `H_daily_hours` (int): horas por jornada
- `enforce_daily_limit` (bool): habilita la restricción diaria
- `time_scale` (int): factor de escala (típicamente 60)
- `max_time` (int): tiempo máx. de cómputo en segundos
- `max_time_stage1` (int, opcional): si se incluye en `/solve`, se usa en vez de `max_time`; en `/solve_two_stage`, si no se provee, se toma `max_time`
- `max_time_stage2` (int, opcional): solo para `/solve_two_stage`
- `use_setup_times` (bool): activa uso de setups; si falta la columna, se ignoran con warning
- `fixed_starts` (opcional): diccionario `{ "jobId": [{ "operation_index": int, "start_time_fixed": float }] }`
  - Notas:
    - Las claves de `fixed_starts` deben ser strings en JSON
    - Los `start_time_fixed` están en horas y se respetan como restricciones duras

Ejemplo mínimo:

````json
{
  "operations": [
    { "job_id": 1, "operation_index": 0, "machine_id": 1, "processing_time": 2.5 },
    { "job_id": 1, "operation_index": 1, "machine_id": 2, "processing_time": 1.5 }
  ],
  "H_daily_hours": 8,
  "enforce_daily_limit": true,
  "time_scale": 60,
  "max_time": 100,
  "use_setup_times": false
}
``;

Ejemplo con setups y `fixed_starts`:

```json
{
  "operations": [
    { "job_id": 1, "operation_index": 0, "machine_id": 1, "processing_time": 2.5, "setup_time": 0.5 },
    { "job_id": 2, "operation_index": 0, "machine_id": 2, "processing_time": 3.0, "setup_time": 0.75 }
  ],
  "H_daily_hours": 8,
  "enforce_daily_limit": true,
  "time_scale": 60,
  "max_time": 120,
  "max_time_stage1": 90,
  "max_time_stage2": 30,
  "use_setup_times": true,
  "fixed_starts": {
    "1": [{ "operation_index": 0, "start_time_fixed": 0.0 }]
  }
}
````

### Response (salida)

```json
{
  "status": "optimal",
  "makespan": 5.0,
  "schedule": [
    {
      "job_id": 1,
      "operation_index": 0,
      "machine_id": 1,
      "start_time_hours": 0.0,
      "end_time_hours": 2.5,
      "duration_hours": 2.5,
      "processing_time_hours": 2.5,
      "setup_time_hours": 0.5,
      "start_day": 0,
      "start_hour_of_day": 0.0,
      "end_day": 0,
      "end_hour_of_day": 2.5
    }
  ]
}
```

Valores de `status` posibles: `optimal`, `infeasible`.

### Notas de diseño

- El cálculo usa CP-SAT con intervalos y `NoOverlap` por máquina
- Si `use_setup_times=true` y falta `setup_time`, se emite warning y se ignoran setups
- En `/solve_two_stage`, si la etapa 2 es infactible, se devuelve la solución de la etapa 1

### Documentación matemática

Consulta `docs/modelos_jsp.md` para ver la formulación del modelo en detalle (con asignación a subconjuntos de máquinas, restricción diaria y función objetivo).
