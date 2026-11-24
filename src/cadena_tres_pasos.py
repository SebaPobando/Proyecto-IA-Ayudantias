"""Bloque 18: extraer ideas, simplificarlas y organizarlas en viñetas."""

# import argparse 
# import json
# from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


def construir_cadena(modelo):
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
    simplificar =plantilla_simplificar | modelo | StrOutputParser()
    formatear = plantilla_formatear | modelo | StrOutputParser()

    cadena = (
        extraer
        | (lambda resultado: {"ideas": resultado})
        | simplificar
        | (lambda resultado: {"explicacion": resultado})
        | formatear
    )

    return cadena

def main():
    import argparse
    from pathlib import Path
    from langchain_core.language_models.fake import FakeListLLM
    from .configuracion import crear_modelo, guardar_json
    parser = argparse.ArgumentParser()
    modos = parser.add_mutually_exclusive_group()
    modos.add_argument("--real", action="store_true")
    modos.add_argument("--simulado", action="store_true")
    parser.add_argument("--archivo", type=Path)
    parser.add_argument("--salida", type=Path)
    args = parser.parse_args()
    texto = (args.archivo.read_text(encoding="utf-8") if args.archivo
             else "La tokenizacion divide el texto en tokens que un modelo procesa.")
    modelo = crear_modelo() if args.real else FakeListLLM(
        responses=["Ideas extraidas de prueba", "Explicacion de prueba", "- Resultado simulado"])
    resultado = construir_cadena(modelo).invoke({"texto": texto})
    if args.salida:
        guardar_json(args.salida, {"modo": "real" if args.real else "simulado",
                                   "entrada": texto, "resultado": resultado})
    print(resultado)


if __name__ == "__main__":
    main()
