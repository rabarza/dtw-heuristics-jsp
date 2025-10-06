## Formulación extendida JSP con asignación flexible de máquinas

### Conjuntos y parámetros

- $J = \{1, \dots, n\}$: conjunto de trabajos.
- Para cada trabajo $j \in J$: $O_j = \{1, \dots, o_j\}$: conjunto ordenado de operaciones.
- $M$: conjunto de máquinas.

Para cada operación $(j,k)$:

- $\mathcal{M}_{jk} \subseteq M$: máquinas aptas para procesar $(j,k)$.
- $p_{jk}^m > 0$: tiempo de procesamiento si $(j,k)$ se ejecuta en la máquina $m \in \mathcal{M}_{jk}$.

Parámetro de jornada:

- $H_{\text{daily}} > 0$: duración máxima de la jornada diaria.

Opcionalmente, tiempos de setup por operación (si aplica el caso simple con una única máquina por operación):

- $s_{jk} \ge 0$: tiempo de setup asociado a $(j,k)$.

### Variables de decisión

- $x_{jk}^m \in \{0,1\}$: vale 1 si $(j,k)$ se asigna a la máquina $m$.
- $S_{jk} \ge 0$: inicio de la operación $(j,k)$.
- $C_{jk} \ge 0$: término de la operación $(j,k)$.
- $C_{\max} \ge 0$: makespan.
- $Y_{jk,j'k'}^{m} \in \{0,1\}$: orden relativo entre $(j,k)$ y $(j',k')$ si ambas usan $m$.
- $d_{jk} \in \mathbb{Z}_{\ge 0}$: día asignado a la operación $(j,k)$.

Si se usan setups agregados a la duración (caso simple):

- $C_{jk} = S_{jk} + p_{jk} + s_{jk}$.

### Restricciones

1. Asignación a máquina (si hay flexibilidad):

$$\sum_{m \in \mathcal{M}_{jk}} x_{jk}^m = 1, \quad \forall j \in J,\; \forall k \in O_j.$$

2. Precedencia dentro del trabajo:

$$S_{j,k+1} \ge C_{jk}, \quad \forall j \in J, \; \forall k \in O_j \setminus \{o_j\}.$$

3. Definición de término con máquina elegida (flexible):

$$C_{jk} = S_{jk} + \sum_{m \in \mathcal{M}_{jk}} p_{jk}^m \, x_{jk}^m, \quad \forall j \in J,\; \forall k \in O_j.$$

4. No solapamiento por máquina:

Para toda $m \in M$ y todo par $(j,k) \neq (j',k')$:

$$S_{j'k'} \ge C_{jk} - M_{\text{big}} \cdot Y_{jk,j'k'}^m - M_{\text{big}} \cdot (2 - x_{jk}^m - x_{j'k'}^m),$$

$$S_{jk} \ge C_{j'k'} - M_{\text{big}} \cdot (1 - Y_{jk,j'k'}^m) - M_{\text{big}} \cdot (2 - x_{jk}^m - x_{j'k'}^m).$$

Con 

$$M_{\text{big}} = \sum_{j \in J}\sum_{k \in O_j}\max_{m \in \mathcal{M}_{jk}} p_{jk}^m$$

Estas restricciones se activan solo si ambas operaciones usan la misma máquina $m$.

5. Restricción de jornada diaria:

$$H_{\text{daily}} \cdot d_{jk} \le S_{jk}, \quad \forall j,k,$$

$$C_{jk} \le H_{\text{daily}} \cdot (d_{jk} + 1), \quad \forall j,k,\; d_{jk} \in \mathbb{Z}_{\ge 0}.$$

6. Makespan:

$$C_{\max} \ge C_{j,o_j}, \quad \forall j \in J.$$

### Función objetivo

$$\min \; C_{\max}.$$

### Comentarios

- La variante de dos etapas usa primero la función objetivo anterior; en la segunda etapa fija $C_{\max}$ al óptimo y minimiza la suma de inicios $\sum_{j,k} S_{jk}$.
- Si se emplean tiempos de setup como parte de la duración, se incorporan sumados a $p_{jk}$ en la duración efectiva de la operación.
