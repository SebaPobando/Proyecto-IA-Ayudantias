# Matriz de riesgos de ProyectoIA

Estimaciones didacticas previas a los controles, no probabilidades medidas. BAJO 1-3; MEDIO 4-8; ALTO 9-14; CRITICO 15-25. Los cortes son la convencion del programa.

AL LIMITE indica que variar un punto en P o I cambia la categoria. Cada responsable es un rol que el equipo debe asignar a una persona. Los controles pendientes no se presentan como implementados.

| ID | Riesgo | P | I | Puntaje | Categoria | AL LIMITE |
|---|---|---:|---:|---:|---|---|
| R1 | Un documento recuperado ordena ignorar reglas y revelar el prompt | 4 | 4 | 16 | CRITICO | Si |
| R2 | Una consulta con datos personales se copia completa a los logs | 3 | 5 | 15 | CRITICO | Si |
| R3 | Se activa un cambio del prompt sin revision de sus restricciones | 3 | 4 | 12 | ALTO | Si |
| R4 | El asistente promete un reembolso que las fuentes no autorizan | 3 | 3 | 9 | ALTO | Si |
| R6 | Un dataset de clasificacion contiene salidas contradictorias y sesga el comportamiento entrenado | 3 | 3 | 9 | ALTO | Si |
| R5 | El indice conserva un precio o una regla reemplazada y responde con datos antiguos | 3 | 2 | 6 | MEDIO | Si |

## R1 Un documento recuperado ordena ignorar reglas y revelar el prompt

**Justificacion**: El corpus puede incorporar texto externo; obedecerlo altera los limites del asistente.

**Mitigacion**: Roles separados, escape de delimitadores, filtro y detencion antes de generar; src/seguridad_rag.py y src/registro_rag.py (Bloque 31).

**Supervision**: Si estado=revision_pendiente, el responsable de seguridad revisa la fuente, la corrige o excluye y autoriza repetir la consulta.

**Responsable**: Responsable de seguridad del equipo

**Evidencia**: test_inyeccion_no_llama_modelo; trazas con revision_pendiente, sin consumo de generacion.

**Estado**: Control integrado y probado localmente; asignar persona y medir ataques contra el modelo real.


## R2 Una consulta con datos personales se copia completa a los logs

**Justificacion**: Los usuarios pueden pegar datos personales; los registros persistentes amplian su exposicion.

**Mitigacion**: Allowlist de metadatos, longitud sin contenido crudo y pregunta=null por defecto; src/logging_rag.py y src/registro_rag.py (Bloque 31). Traza nueva del agente tambien minimizada.

**Supervision**: El custodio revisa una muestra y autoriza cada exportacion o acceso excepcional; no usar --guardar-pregunta con datos personales.

**Responsable**: Custodio de datos del equipo

**Evidencia**: test_logs_no_guardan_consulta; test_allowlist_rechaza_contenido.

**Estado**: Minimizacion probada. Permisos de acceso por rol y revision de trazas historicas pendientes.


## R3 Se activa un cambio del prompt sin revision de sus restricciones

**Justificacion**: El prompt se modifica en desarrollo y un cambio altera las reglas del servicio.

**Mitigacion**: Registro con huellas, diff, interrupt, aprobacion de huella exacta y version activa leida por RAG; src/registro_prompts.py y src/grafo_supervision.py (Bloque 32).

**Supervision**: El responsable funcional revisa diff y pruebas; aprueba o rechaza antes de activar la version local.

**Responsable**: Responsable funcional del equipo

**Evidencia**: test_pausa_aprobacion_y_rechazo; test_activacion_persistida; test_huella_incorrecta_no_se_aprueba.

**Estado**: Activacion local integrada. Checkpointer durable, permisos y concurrencia de produccion pendientes.


## R4 El asistente promete un reembolso que las fuentes no autorizan

**Justificacion**: Una respuesta sin respaldo puede generar un reclamo y un compromiso comercial incorrecto.

**Mitigacion**: Prompt con abstencion y limites; citas numeradas y validacion de sus IDs; el RAG no ejecuta herramientas (Bloques 26 y 31).

**Supervision**: Solicitudes de reembolso o excepcion pasan al encargado de soporte antes de comunicar una autorizacion; el agente previo mantiene aprobacion en consola.

**Responsable**: Encargado de soporte

**Evidencia**: test_cita_inventada_retiene_respuesta; revision manual de afirmaciones y fuentes.

**Estado**: Formato y pertenencia de citas probados; respaldo semantico y calidad real pendientes. Una cita valida no prueba veracidad.


## R6 Un dataset de clasificacion contiene salidas contradictorias y sesga el comportamiento entrenado

**Justificacion**: La anotacion manual puede ser inconsistente; el entrenamiento reproduciria etiquetas defectuosas.

**Mitigacion**: 12 ejemplos ficticios, balance por intencion, validacion de JSON, duplicados y contradicciones; src/dataset_tuning.py (Bloque 29).

**Supervision**: El responsable de datos revisa ejemplos y balance antes de cualquier envio a entrenamiento.

**Responsable**: Responsable de datos

**Evidencia**: test_dataset_detecta_duplicado_y_contradiccion; docs/evidencias_simuladas/validacion_dataset.json.

**Estado**: Preparacion probada; no se ejecuto entrenamiento y no existe un modelo ajustado.


## R5 El indice conserva un precio o una regla reemplazada y responde con datos antiguos

**Justificacion**: Cambios del corpus requieren reindexar; un precio obsoleto produce informacion incorrecta reversible.

**Mitigacion**: IDs estables, version de fuente, upsert, eliminacion de chunks obsoletos y manifiesto del modelo; src/indexar_corpus.py (Bloques 24 y 25).

**Supervision**: El responsable documental comprueba fuente, version y precio antes de publicar una actualizacion; no se pausa cada consulta.

**Responsable**: Responsable documental

**Evidencia**: test_reindexacion_actualiza_y_elimina_obsoletos; recarga del indice persistido.

**Estado**: Actualizacion local probada; definir calendario real de actualizacion.

