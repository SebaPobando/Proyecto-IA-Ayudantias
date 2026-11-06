import logging

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import (
    RunnableBranch,
    RunnablePassthrough,
    RunnableLambda,
)


# Identifica los registros generados por este módulo.
logger = logging.getLogger(__name__)


def construir_paso_clasificacion(modelo):
    # Recibimos el modelo para poder reemplazarlo durante las pruebas.
    plantilla = PromptTemplate.from_template(
        "Clasifica el siguiente mensaje de soporte en una sola palabra: "
        "pregunta, queja o sugerencia. Responde solo con esa palabra.\n\n"
        "{mensaje}"
    )

    return (
        plantilla
        | modelo
        | StrOutputParser()
        # Quita espacios, convierte a minúsculas y elimina puntos finales.
        | (lambda texto: texto.strip().lower().rstrip(".").strip())
    )


def construir_cadena_con_enrutamiento(
    paso_clasificacion,
    cadena_queja=None,
    cadena_sugerencia=None,
    cadena_pregunta=None,
):
    # Si una prueba omite una ruta, esa ruta simplemente deja pasar los datos.
    cadena_queja = cadena_queja or RunnablePassthrough()
    cadena_sugerencia = cadena_sugerencia or RunnablePassthrough()
    cadena_pregunta = cadena_pregunta or RunnablePassthrough()

    bifurcacion = RunnableBranch(
        # Cada condición recibe el diccionario completo.
        (lambda datos: datos["categoria"] == "queja", cadena_queja),
        (lambda datos: datos["categoria"] == "sugerencia", cadena_sugerencia),

        # Se ejecuta si ninguna condición anterior coincide.
        cadena_pregunta,
    )

    return (
        # Conserva mensaje y agrega la categoría calculada.
        RunnablePassthrough.assign(categoria=paso_clasificacion)
        | bifurcacion
    )


def fallback_con_log(datos):
    # Registra la excepción que provocó el uso del fallback.
    logger.warning(
        "Fallo la ruta de queja; se ejecuta el fallback: %s",
        datos.get("error"),
    )

    return (
        "Gracias por tu mensaje. Lo hemos recibido y estamos "
        "trabajando en ello. Te responderemos lo antes posible."
    )


# Convierte la función de Python en una pieza ejecutable de LangChain.
respuesta_generica = RunnableLambda(fallback_con_log)


def construir_cadena_queja_segura(cadena_queja):
    return cadena_queja.with_fallbacks(
        # Alternativa que se ejecutará si falla la cadena de quejas.
        [respuesta_generica],

        # Entrega la excepción al fallback bajo la clave "error".
        exception_key="error",
    )


def construir_flujo(modelo):
    # Construye el clasificador con el modelo recibido.
    paso_clasificacion = construir_paso_clasificacion(modelo)

    cadena_pregunta = (
        PromptTemplate.from_template(
            "Responde esta pregunta tecnica con precision, "
            "en un solo parrafo:\n\n{mensaje}"
        )
        | modelo
        | StrOutputParser()
    )

    cadena_queja = (
        PromptTemplate.from_template(
            "Responde esta queja con empatia, reconociendo el problema "
            "antes de ofrecer una solucion, en un solo parrafo:\n\n{mensaje}"
        )
        | modelo
        | StrOutputParser()
    )

    cadena_sugerencia = (
        PromptTemplate.from_template(
            "Responde a esta sugerencia con gratitud y consideracion, "
            "en un solo parrafo:\n\n{mensaje}"
        )
        | modelo
        | StrOutputParser()
    )

    # Protege la ruta de quejas antes de conectarla al enrutador.
    cadena_queja_segura = construir_cadena_queja_segura(cadena_queja)

    # Devuelve un único flujo con todas sus conexiones.
    return construir_cadena_con_enrutamiento(
        paso_clasificacion=paso_clasificacion,
        cadena_queja=cadena_queja_segura,
        cadena_sugerencia=cadena_sugerencia,
        cadena_pregunta=cadena_pregunta,
    )


def procesar_mensaje_seguro(cadena, mensaje):
    try:
        # Ejecuta el flujo completo con el mensaje recibido.
        return cadena.invoke({"mensaje": mensaje})

    except Exception as error:
        # Captura y registra fallos que no resolvió el fallback.
        logger.error("Error al procesar el mensaje: %s", error)

        return (
            "no pudimos procesar tu mensaje. "
            "Por favor, intenta de nuevo mas tarde."
        )


if __name__ == "__main__":
    # Configura los registros solamente al ejecutar este módulo.
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s - %(levelname)s - %(message)s",
        filename="errores.log",
        filemode="a",
        encoding="utf-8",
    )

    # Carga las variables de entorno y prepara el modelo.
    load_dotenv()
    modelo = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite")

    # Construye el flujo, incluyendo el fallback de quejas.
    cadena_con_enrutamiento = construir_flujo(modelo)

    mensaje = "La app se cierra cada vez que subo una foto."

    # Ejecuta el flujo bajo la protección general del try/except.
    resultado = procesar_mensaje_seguro(
        cadena_con_enrutamiento,
        mensaje,
    )

    print(resultado)