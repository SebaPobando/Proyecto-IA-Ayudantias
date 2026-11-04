"""Bloque 18: extraer ideas, simplificarlas y organizarlas en viñetas."""

import argparse
import json
from pathlib import Path

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


def construir_cadena(modelo):
    """Conecta tres tareas; recibe el modelo para poder probarlas sin API."""
    plantilla_extraer = PromptTemplate.from_template(
        "Extrae las tres ideas principales del siguiente texto. "
        "No agregues información:\n\n{texto}"
    )

    plantilla_simplificar = PromptTemplate.from_template(
        "Explica estas ideas con palabras sencillas para una "
        "persona sin conocimientos técnicos. "
        "Conserva su significado:\n\n{ideas}"
    )

    plantilla_formatear = PromptTemplate.from_template(
        "Organiza esta explicación en un máximo de tres viñetas. "
        "No agregues información ni introducción:\n\n{explicacion}"
    )

    extraer = plantilla_extraer | modelo | StrOutputParser()
    simplificar = plantilla_simplificar | modelo | StrOutputParser()
    formatear = plantilla_formatear | modelo | StrOutputParser()

    cadena = (
        extraer
        | (lambda resultado: {"ideas": resultado})
        | simplificar
        | (lambda resultado: {"explicacion": resultado})
        | formatear
    )

    return cadena


TEXTO_EJEMPLO = """
    La tokenización divide un texto en unidades llamadas tokens.
    Un token puede corresponder a una palabra, parte de una palabra
    o un signo de puntuación. Los modelos de lenguaje procesan
    secuencias de tokens y generan su respuesta progresivamente.
    """


def construir_modelo_simulado():
    """Respuestas prefijadas para comprobar las conexiones, sin IA real."""
    from langchain_core.messages import AIMessage
    from langchain_core.runnables import RunnableLambda

    respuestas = iter([
        "SIMULADO: ideas extraídas del texto de ejemplo.",
        "SIMULADO: explicación simplificada de esas ideas.",
        "- SIMULADO: resultado prefijado para ensayar las conexiones.",
    ])

    def responder(prompt):
        return AIMessage(content=next(respuestas))

    return RunnableLambda(responder)


def construir_modelo_real():
    from dotenv import load_dotenv
    from langchain_google_genai import ChatGoogleGenerativeAI

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    return ChatGoogleGenerativeAI(model="gemini-3.8-flash")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--simulado", action="store_true", help="Ensaya sin API.")
    parser.add_argument("--archivo", type=Path, help="Archivo de texto UTF-8 de entrada.")
    parser.add_argument("--salida", type=Path, help="Guarda entrada y resultado en JSON.")
    args = parser.parse_args(argv)

    texto = TEXTO_EJEMPLO
    if args.archivo is not None:
        try:
            texto = args.archivo.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as error:
            parser.error(f"No se pudo leer el archivo de entrada: {error}")
    if not texto.strip():
        parser.error("El texto de entrada no puede estar vacío.")
    if args.salida is not None and args.archivo is not None:
        if args.salida.resolve() == args.archivo.resolve():
            parser.error("La salida debe ser distinta del archivo de entrada.")

    modo = "simulado" if args.simulado else "real"
    if args.simulado:
        print("MODO SIMULADO: respuestas prefijadas; no se evalúa la calidad del texto.")
        modelo = construir_modelo_simulado()
    else:
        print("MODO REAL: tres consultas a Gemini, sin contar posibles reintentos.")
        modelo = construir_modelo_real()

    cadena = construir_cadena(modelo)
    resultado = cadena.invoke({"texto": texto})
    print(resultado)

    if args.salida is not None:
        registro = {
            "modo": modo,
            "archivo_entrada": str(args.archivo.resolve()) if args.archivo else None,
            "texto_entrada": texto,
            "resultado": resultado,
        }
        args.salida.parent.mkdir(parents=True, exist_ok=True)
        args.salida.write_text(
            json.dumps(registro, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"Registro guardado en: {args.salida}")


if __name__ == "__main__":
    main()
