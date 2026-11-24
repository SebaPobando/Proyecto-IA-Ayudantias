# Estado de ProyectoIA hasta el bloque 32

La implementacion local cubre las piezas vistas hasta el bloque 32. La evidencia
automatizada no sustituye la revision de respuestas reales ni demuestra que una
actividad que pide API real este cerrada.

| Pieza | Evidencia disponible | Pendiente |
|---|---|---|
| Bloques 18 a 20 | Suite original de cadena, enrutamiento y fallback | Mantener evidencia real previa; no se genero una nueva corrida pagada |
| Bloques 21 a 23 | Agentes anteriores conservados, trazas futuras minimizadas | Asignar revisores y revisar las trazas historicas antes de compartir |
| Bloques 24 a 26 | Chroma persistente, reindexacion, fuentes, citas y demostracion local | Indexacion y respuesta del proveedor bajo configuracion de la cuenta |
| Bloque 27 | Evaluacion de 10 casos con k=1,3,6 y metricas sobre recuperacion local | Repetir con embeddings reales y corpus menos trivial |
| Bloque 28 | Instrumentacion preparada, registros de demostracion etiquetados | 3 consultas reales y comparacion k=3/k=6; tarifas vigentes y costo de embeddings |
| Bloque 29 | 12 ejemplos ficticios balanceados y validador que detecta errores | Dataset real, separacion de evaluacion y entrenamiento solo si se decide usarlo |
| Bloque 30 | Decision fundamentada y sensibilidad del metodo | Confirmar supuestos de cambio de informacion y calidad de formato con evidencia |
| Bloque 31 | Filtro, roles, delimitadores y bloqueo antes de generar; logs sin consulta cruda | Pruebas de ataques contra modelo real y permisos de acceso |
| Bloque 32 | Historial y diff, pausa real de LangGraph, aprobacion/rechazo y 6 riesgos | Decision humana sobre prompt activo y asignacion de personas a los roles |

Los resultados en `docs/evidencias_simuladas` usan vectores lexicos locales y una
respuesta extractiva, sin consultar un LLM. Los tiempos son de ejecucion local;
tokens y costos se dejan desconocidos. Los resultados de recuperacion son
especialmente faciles con diez textos cortos y preguntas cercanas a su vocabulario.
No deben presentarse como calidad semantica o de generalizacion del proveedor.

Las trazas nuevas del agente se escriben minimizadas en `.local`. El archivo
historico `docs/trazas_agente.jsonl` se conserva como estaba; antes de publicarlo,
el custodio debe comprobar si contiene informacion personal o texto de usuarios.

No se hizo entrenamiento, despliegue, commit ni push. Los comandos de modo real
quedan documentados para que se ejecuten con la cuenta y los modelos elegidos.
