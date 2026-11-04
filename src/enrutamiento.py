"""Ejemplo docente del bloque 19. Por defecto usa respuestas simuladas."""

import argparse
from pathlib import Path

from langchain_core.messages import AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import (
    RunnableBranch,
    RunnableLambda,
    RunnablePassthrough,
)


def normalizar_categoria(texto):
    # strip() quita espacios; el segundo strip tambien quita puntos finales.
    # Esto NO convierte cualquier respuesta inesperada en una categoria valida.
    return texto.strip().lower().rstrip(".").strip()


def construir_paso_clasificacion(modelo):
    """Reutiliza plantilla, modelo y parser del bloque 18 para obtener una categoría."""
    plantilla = PromptTemplate.from_template(
        "Clasifica este mensaje de soporte en una sola palabra: "
        "pregunta, queja o sugerencia. Responde solo con esa palabra.\n\n"
        "{mensaje}"
    )
    return plantilla | modelo | StrOutputParser() | normalizar_categoria


def construir_cadena_con_enrutamiento(
    paso_clasificacion, cadena_queja, cadena_sugerencia, cadena_pregunta
):
    """Agrega categoría sin perder mensaje y ejecuta una sola ruta."""
    bifurcacion = RunnableBranch(
        (lambda datos: datos["categoria"] == "queja", cadena_queja),
        (lambda datos: datos["categoria"] == "sugerencia", cadena_sugerencia),
        cadena_pregunta,  # Ruta por defecto, igual que en el material del curso.
    )
    return RunnablePassthrough.assign(categoria=paso_clasificacion) | bifurcacion


def construir_ruta(modelo, nombre, instruccion):
    plantilla = PromptTemplate.from_template(
        instruccion
        + " No inventes funcionalidades, acciones ya realizadas ni compromisos "
        "de la empresa. Responde en un maximo de tres oraciones.\n\n{mensaje}"
    )
    paso_respuesta = plantilla | modelo | StrOutputParser()

    def adjuntar_respuesta(datos):
        return {**datos, "ruta": nombre}

    # Conservamos categoria y mensaje, y agregamos la respuesta de la ruta.
    return (
        RunnablePassthrough.assign(respuesta=paso_respuesta)
        | RunnableLambda(adjuntar_respuesta)
    )


def construir_flujo(modelo):
    clasificador = construir_paso_clasificacion(modelo)
    queja = construir_ruta(
        modelo, "queja",
        "Reconoce con empatia el problema de esta queja y pide un dato util "
        "para investigarlo."
    )
    sugerencia = construir_ruta(
        modelo, "sugerencia",
        "Agradece esta sugerencia y pide una aclaracion que ayude a entenderla."
    )
    pregunta = construir_ruta(
        modelo, "pregunta/default",
        "Responde esta consulta de soporte. Si falta informacion, pide "
        "una aclaracion en lugar de inventar instrucciones del producto."
    )
    return construir_cadena_con_enrutamiento(clasificador, queja, sugerencia, pregunta)


CASOS = [
    ("pregunta", "¿Como cambio mi contraseña?",
     "¿En que aplicacion necesitas cambiar tu contraseña?"),
    ("queja", "La app se cierra cada vez que subo una foto.",
     "Lamento el inconveniente. ¿Que dispositivo y version de la app usas?"),
    ("sugerencia", "Seria bueno tener modo oscuro.",
     "Gracias por la sugerencia. ¿En que pantalla te resultaria mas util?"),
    ("desconocida", "Hola, necesito ayuda.",
     "¿Puedes contarme con que necesitas ayuda?"),
]


def mostrar(resultado):
    print("Mensaje:", resultado["mensaje"])
    print("Categoria:", resultado["categoria"])
    print("Ruta:", resultado["ruta"])
    print("Respuesta:", resultado["respuesta"])
    print()


def ejecutar_simulacion():
    print("MODO SIMULADO: categorias y respuestas prefijadas; sin API ni IA real.\n")
    for categoria, mensaje, respuesta in CASOS:
        respuestas = iter([categoria, respuesta])

        def responder(prompt):
            return AIMessage(content=next(respuestas))

        flujo = construir_flujo(RunnableLambda(responder))
        mostrar(flujo.invoke({"mensaje": mensaje}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--real", action="store_true", help="Consulta Gemini.")
    parser.add_argument("--mensaje", help="Un mensaje para el modo real.")
    args = parser.parse_args()

    if not args.real:
        if args.mensaje:
            parser.error("--mensaje se usa junto con --real")
        ejecutar_simulacion()
        return

    from dotenv import load_dotenv
    from langchain_google_genai import ChatGoogleGenerativeAI

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    modelo = ChatGoogleGenerativeAI(model="gemini-3.8-flash")
    flujo = construir_flujo(modelo)
    mensajes = [args.mensaje] if args.mensaje else [caso[1] for caso in CASOS[:3]]
    print("MODO REAL: dos consultas al modelo por mensaje, sin contar reintentos.\n")
    for mensaje in mensajes:
        mostrar(flujo.invoke({"mensaje": mensaje}))


if __name__ == "__main__":
    main()
