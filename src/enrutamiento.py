"""Bloques 19 y 20: rutas inyectables y fallback, sin modelo al importar."""
import argparse
import logging
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableBranch, RunnablePassthrough, RunnableLambda

logger = logging.getLogger(__name__)
plantilla_clasificacion = PromptTemplate.from_template(
    "Clasifica este mensaje como pregunta, queja o sugerencia. "
    "Devuelve solo la categoria.\n\n{mensaje}")


def construir_paso_clasificacion(modelo):
    return (plantilla_clasificacion | modelo | StrOutputParser()
            | (lambda texto: texto.strip().lower().rstrip(".!")))


def fallback_con_log(datos):
    logger.warning("Fallo una etapa; se utiliza respuesta generica")
    return "Gracias por tu mensaje. Lo hemos recibido y estamos trabajando en ello. Te responderemos lo antes posible."


respuesta_generica = RunnableLambda(fallback_con_log)


def construir_cadena_queja_segura(cadena_queja):
    return cadena_queja.with_fallbacks([respuesta_generica])


def construir_cadena_con_enrutamiento(paso_clasificacion, cadena_queja=None,
                                     cadena_sugerencia=None, cadena_pregunta=None):
    return (RunnablePassthrough.assign(categoria=paso_clasificacion) | RunnableBranch(
        (lambda x: x["categoria"] == "queja", cadena_queja or RunnablePassthrough()),
        (lambda x: x["categoria"] == "sugerencia", cadena_sugerencia or RunnablePassthrough()),
        cadena_pregunta or RunnablePassthrough()))


def construir_flujo(modelo):
    def ruta(nombre, instruccion):
        cadena = PromptTemplate.from_template(instruccion + "\n\n{mensaje}") | modelo | StrOutputParser()
        return RunnablePassthrough.assign(respuesta=cadena) | RunnableLambda(
            lambda datos: {**datos, "ruta": nombre})
    return construir_cadena_con_enrutamiento(
        construir_paso_clasificacion(modelo),
        ruta("queja", "Responde con empatia y propone el siguiente paso."),
        ruta("sugerencia", "Agradece la sugerencia y explica como se revisara."),
        ruta("pregunta/default", "Responde con precision; si falta informacion, pidela."))


def procesar_mensaje_seguro(cadena, mensaje):
    try:
        return cadena.invoke({"mensaje": mensaje})
    except Exception:
        logger.error("No se pudo procesar el mensaje")
        return "no pudimos procesar tu mensaje. Por favor, intenta de nuevo más tarde."


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--real", action="store_true")
    parser.add_argument("--mensaje", default="Que precio tiene el teclado?")
    args = parser.parse_args()
    if args.real:
        from .configuracion import crear_modelo
        print(procesar_mensaje_seguro(construir_flujo(crear_modelo()), args.mensaje))
    else:
        from langchain_core.messages import AIMessage
        for categoria in ("pregunta", "queja", "sugerencia", "desconocida"):
            respuestas = iter([categoria, "Respuesta simulada"])
            modelo = RunnableLambda(lambda _: AIMessage(content=next(respuestas)))
            print(construir_flujo(modelo).invoke({"mensaje": args.mensaje}))


if __name__ == "__main__":
    main()
