"""Bloque 32: riesgos del codigo actual y estado explicito de los controles."""
from .configuracion import DOCS, guardar_json

RIESGOS = [
    {"id": "R1", "riesgo": "Un documento recuperado ordena ignorar reglas y revelar el prompt",
     "probabilidad": 4, "impacto": 4,
     "justificacion": "El corpus puede incorporar texto externo; obedecerlo altera los limites del asistente.",
     "mitigacion": "Roles separados, escape de delimitadores, filtro y detencion antes de generar; src/seguridad_rag.py y src/registro_rag.py (Bloque 31).",
     "supervision": "Si estado=revision_pendiente, el responsable de seguridad revisa la fuente, la corrige o excluye y autoriza repetir la consulta.",
     "responsable": "Responsable de seguridad del equipo",
     "evidencia": "test_inyeccion_no_llama_modelo; trazas con revision_pendiente, sin consumo de generacion.",
     "estado": "Control integrado y probado localmente; asignar persona y medir ataques contra el modelo real."},
    {"id": "R2", "riesgo": "Una consulta con datos personales se copia completa a los logs",
     "probabilidad": 3, "impacto": 5,
     "justificacion": "Los usuarios pueden pegar datos personales; los registros persistentes amplian su exposicion.",
     "mitigacion": "Allowlist de metadatos, longitud sin contenido crudo y pregunta=null por defecto; src/logging_rag.py y src/registro_rag.py (Bloque 31). Traza nueva del agente tambien minimizada.",
     "supervision": "El custodio revisa una muestra y autoriza cada exportacion o acceso excepcional; no usar --guardar-pregunta con datos personales.",
     "responsable": "Custodio de datos del equipo",
     "evidencia": "test_logs_no_guardan_consulta; test_allowlist_rechaza_contenido.",
     "estado": "Minimizacion probada. Permisos de acceso por rol y revision de trazas historicas pendientes."},
    {"id": "R3", "riesgo": "Se activa un cambio del prompt sin revision de sus restricciones",
     "probabilidad": 3, "impacto": 4,
     "justificacion": "El prompt se modifica en desarrollo y un cambio altera las reglas del servicio.",
     "mitigacion": "Registro con huellas, diff, interrupt, aprobacion de huella exacta y version activa leida por RAG; src/registro_prompts.py y src/grafo_supervision.py (Bloque 32).",
     "supervision": "El responsable funcional revisa diff y pruebas; aprueba o rechaza antes de activar la version local.",
     "responsable": "Responsable funcional del equipo",
     "evidencia": "test_pausa_aprobacion_y_rechazo; test_activacion_persistida; test_huella_incorrecta_no_se_aprueba.",
     "estado": "Activacion local integrada. Checkpointer durable, permisos y concurrencia de produccion pendientes."},
    {"id": "R4", "riesgo": "El asistente promete un reembolso que las fuentes no autorizan",
     "probabilidad": 3, "impacto": 3,
     "justificacion": "Una respuesta sin respaldo puede generar un reclamo y un compromiso comercial incorrecto.",
     "mitigacion": "Prompt con abstencion y limites; citas numeradas y validacion de sus IDs; el RAG no ejecuta herramientas (Bloques 26 y 31).",
     "supervision": "Solicitudes de reembolso o excepcion pasan al encargado de soporte antes de comunicar una autorizacion; el agente previo mantiene aprobacion en consola.",
     "responsable": "Encargado de soporte",
     "evidencia": "test_cita_inventada_retiene_respuesta; revision manual de afirmaciones y fuentes.",
     "estado": "Formato y pertenencia de citas probados; respaldo semantico y calidad real pendientes. Una cita valida no prueba veracidad."},
    {"id": "R5", "riesgo": "El indice conserva un precio o una regla reemplazada y responde con datos antiguos",
     "probabilidad": 3, "impacto": 2,
     "justificacion": "Cambios del corpus requieren reindexar; un precio obsoleto produce informacion incorrecta reversible.",
     "mitigacion": "IDs estables, version de fuente, upsert, eliminacion de chunks obsoletos y manifiesto del modelo; src/indexar_corpus.py (Bloques 24 y 25).",
     "supervision": "El responsable documental comprueba fuente, version y precio antes de publicar una actualizacion; no se pausa cada consulta.",
     "responsable": "Responsable documental",
     "evidencia": "test_reindexacion_actualiza_y_elimina_obsoletos; recarga del indice persistido.",
     "estado": "Actualizacion local probada; definir calendario real de actualizacion."},
    {"id": "R6", "riesgo": "Un dataset de clasificacion contiene salidas contradictorias y sesga el comportamiento entrenado",
     "probabilidad": 3, "impacto": 3,
     "justificacion": "La anotacion manual puede ser inconsistente; el entrenamiento reproduciria etiquetas defectuosas.",
     "mitigacion": "12 ejemplos ficticios, balance por intencion, validacion de JSON, duplicados y contradicciones; src/dataset_tuning.py (Bloque 29).",
     "supervision": "El responsable de datos revisa ejemplos y balance antes de cualquier envio a entrenamiento.",
     "responsable": "Responsable de datos",
     "evidencia": "test_dataset_detecta_duplicado_y_contradiccion; docs/evidencias_simuladas/validacion_dataset.json.",
     "estado": "Preparacion probada; no se ejecuto entrenamiento y no existe un modelo ajustado."},
]


def puntaje_riesgo(probabilidad, impacto):
    if any(type(n) is not int or not 1 <= n <= 5 for n in (probabilidad, impacto)):
        raise ValueError("P e I deben ser enteros entre 1 y 5")
    return probabilidad * impacto


def categoria_riesgo(puntaje):
    if puntaje >= 15:
        return "CRITICO"
    if puntaje >= 9:
        return "ALTO"
    if puntaje >= 4:
        return "MEDIO"
    return "BAJO"


def esta_en_el_limite(probabilidad, impacto):
    actual = categoria_riesgo(puntaje_riesgo(probabilidad, impacto))
    vecinos = [(probabilidad + 1, impacto), (probabilidad - 1, impacto),
               (probabilidad, impacto + 1), (probabilidad, impacto - 1)]
    return any(categoria_riesgo(p * i) != actual for p, i in vecinos if 1 <= p <= 5 and 1 <= i <= 5)


def completar_matriz():
    filas = []
    for riesgo in RIESGOS:
        fila = dict(riesgo)
        fila["puntaje"] = puntaje_riesgo(fila["probabilidad"], fila["impacto"])
        fila["categoria"] = categoria_riesgo(fila["puntaje"])
        fila["al_limite"] = esta_en_el_limite(fila["probabilidad"], fila["impacto"])
        filas.append(fila)
    return sorted(filas, key=lambda r: -r["puntaje"])


def main():
    filas = completar_matriz()
    guardar_json(DOCS / "matriz_riesgos.json", filas)
    lineas = ["# Matriz de riesgos de ProyectoIA", "",
              "Estimaciones didacticas previas a los controles, no probabilidades medidas. BAJO 1-3; MEDIO 4-8; ALTO 9-14; CRITICO 15-25. Los cortes son la convencion del programa.", "",
              "AL LIMITE indica que variar un punto en P o I cambia la categoria. Cada responsable es un rol que el equipo debe asignar a una persona. Los controles pendientes no se presentan como implementados.", "",
              "| ID | Riesgo | P | I | Puntaje | Categoria | AL LIMITE |",
              "|---|---|---:|---:|---:|---|---|"]
    for r in filas:
        lineas.append(f"| {r['id']} | {r['riesgo']} | {r['probabilidad']} | {r['impacto']} | {r['puntaje']} | {r['categoria']} | {'Si' if r['al_limite'] else 'No'} |")
    for r in filas:
        lineas.extend(["", f"## {r['id']} {r['riesgo']}", ""])
        for campo in ("justificacion", "mitigacion", "supervision", "responsable", "evidencia", "estado"):
            lineas.append(f"**{campo.capitalize()}**: {r[campo]}\n")
    (DOCS / "matriz_riesgos.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    for r in filas:
        print(r["id"], r["categoria"], r["puntaje"], "AL LIMITE" if r["al_limite"] else "")


if __name__ == "__main__":
    main()
