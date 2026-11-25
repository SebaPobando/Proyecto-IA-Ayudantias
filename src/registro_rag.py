"""Bloques 28 y 31: RAG medido y auditable; el modo real se pide explicitamente."""
import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from langchain_core.messages import AIMessage
from .configuracion import DOCS, LOCAL, crear_modelo
from .logging_rag import Auditor, nueva_traza
from .recuperacion import recuperar
from .registro_prompts import obtener_activa
from .seguridad_rag import filtrar_contexto, construir_mensajes, citas_validas, numeros_citados


def calcular_costo_generacion(tokens, entrada_millon=None, salida_millon=None):
    if tokens is None or entrada_millon is None or salida_millon is None:
        return None
    if any(tokens.get(k) is None for k in ("input_tokens", "output_tokens")):
        return None
    if entrada_millon < 0 or salida_millon < 0:
        raise ValueError("Las tarifas no pueden ser negativas")
    return (tokens["input_tokens"] * entrada_millon + tokens["output_tokens"] * salida_millon) / 1_000_000


def registrar_consulta(pregunta, k=3, real=False, store=None, modelo=None,
                       ruta_registros=None, auditor=None, guardar_pregunta=False,
                       tarifas=None):
    if not pregunta.strip() or type(k) is not int or k < 1:
        raise ValueError("Indica una pregunta y k entero positivo")
    modo = "real" if real else "simulado"
    carpeta = LOCAL / "registros_reales" if real else DOCS / "evidencias_simuladas"
    ruta = Path(ruta_registros or carpeta / "registros_latencia_costo.jsonl")
    auditor = auditor or Auditor(carpeta / "trazas_rag.jsonl")
    version = obtener_activa()
    tiempos = {"embed_y_busqueda": 0.0, "construccion_prompt": 0.0, "generacion": 0.0}
    tokens = None
    respuesta = "No tengo evidencia suficiente para responder."
    citas = {}
    with nueva_traza() as trace_id:
        inicio_total = time.perf_counter()
        auditor.emitir("consulta_recibida", modo=modo, pregunta_len=len(pregunta),
                       k=k, prompt_huella=version["huella"])
        try:
            inicio = time.perf_counter()
            pares = recuperar(pregunta, k=k, real=real, store=store)
            tiempos["embed_y_busqueda"] = (time.perf_counter() - inicio) * 1000
            docs, sospechosos = filtrar_contexto([doc for doc, _ in pares])
            auditor.emitir("contexto_filtrado", n_documentos=len(docs), n_sospechosos=len(sospechosos))
            if sospechosos:
                estado = "revision_pendiente"
                respuesta = "Consulta detenida: un documento requiere revision humana antes de continuar."
                auditor.emitir("revision_pendiente", documento_ids=[d.metadata["id"] for d in sospechosos])
            elif not docs:
                estado = "sin_evidencia"
            else:
                inicio = time.perf_counter()
                mensajes, citas = construir_mensajes(pregunta, docs, version["texto"])
                tiempos["construccion_prompt"] = (time.perf_counter() - inicio) * 1000
                inicio = time.perf_counter()
                if real:
                    resultado = (modelo or crear_modelo()).invoke(mensajes)
                elif modelo is not None:
                    resultado = modelo.invoke(mensajes)
                else:
                    resultado = AIMessage(content="SIMULACION: " + docs[0].page_content + " [1]")
                tiempos["generacion"] = (time.perf_counter() - inicio) * 1000
                respuesta = str(resultado.text)
                tokens = dict(resultado.usage_metadata) if resultado.usage_metadata else None
                abstencion = respuesta.lower().strip().startswith("no tengo evidencia suficiente")
                if not abstencion and not citas_validas(respuesta, citas):
                    estado = "revision_pendiente"
                    respuesta = "Respuesta retenida: faltan citas validas; requiere revision humana."
                else:
                    estado = "respondido" if real else "respondido_simulado"
                auditor.emitir("consumo_llm", input_tokens=tokens.get("input_tokens") if tokens else None,
                               output_tokens=tokens.get("output_tokens") if tokens else None,
                               total_tokens=tokens.get("total_tokens") if tokens else None)
            total = (time.perf_counter() - inicio_total) * 1000
            precios = tarifas if tarifas is not None else (
                os.getenv("GEMINI_INPUT_USD_PER_MILLION"), os.getenv("GEMINI_OUTPUT_USD_PER_MILLION"))
            precios = tuple(float(p) if p is not None and str(p).strip() else None for p in precios)
            costo = calcular_costo_generacion(tokens, *precios) if real else None
            registro = {"timestamp": datetime.now(timezone.utc).isoformat(), "trace_id": trace_id,
                        "modo": modo, "estado": estado, "pregunta": pregunta if guardar_pregunta else None,
                        "pregunta_len": len(pregunta), "k": k, "prompt_huella": version["huella"],
                        "tiempos_ms": {n: round(v, 3) for n, v in tiempos.items()},
                        "tiempo_total_ms": round(total, 3), "tokens": tokens,
                        "costo_generacion_estimado_usd": costo,
                        "costo_embeddings_usd": None,
                        "modelo": os.getenv("GEMINI_MODEL") if real else "respuesta-extractiva-local",
                        "documentos": [{"id": d.metadata["id"], "fuente": d.metadata["fuente"],
                                        "distancia": float(distancia)} for d, distancia in pares]}
            ruta.parent.mkdir(parents=True, exist_ok=True)
            with ruta.open("a", encoding="utf-8") as archivo:
                archivo.write(json.dumps(registro, ensure_ascii=False) + "\n")
            auditor.emitir("consulta_finalizada", estado=estado, tiempo_total_ms=registro["tiempo_total_ms"])
            return {"registro": registro, "respuesta": respuesta, "citas": citas}
        except Exception as error:
            auditor.emitir("consulta_fallida", error_tipo=type(error).__name__)
            raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pregunta", default="Cual es el precio del teclado T01?")
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--real", action="store_true")
    parser.add_argument("--guardar-pregunta", action="store_true", help="Solo con textos ficticios autorizados; guarda contenido crudo")
    args = parser.parse_args()
    if args.real:
        from .configuracion import cargar_configuracion_real
        cargar_configuracion_real()
    try:
        resultado = registrar_consulta(args.pregunta, args.k, args.real, guardar_pregunta=args.guardar_pregunta)
    except Exception as error:
        raise SystemExit("No se completo la consulta. Tipo de error: " + type(error).__name__) from None
    print(resultado["respuesta"])
    for numero in numeros_citados(resultado["respuesta"]):
        cita = resultado["citas"].get(numero)
        if cita:
            print(f"Fuente [{numero}] {cita['fuente']} ({cita['id']})")
    print(json.dumps(resultado["registro"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
