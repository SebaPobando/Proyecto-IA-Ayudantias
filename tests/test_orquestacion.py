import logging
from unittest.mock import MagicMock

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from src.enrutamiento import (
    construir_cadena_con_enrutamiento,
    construir_cadena_queja_segura,
    construir_flujo,
    procesar_mensaje_seguro,
)


def test_cadena_queja_usa_fallback_ante_fallo_del_modelo():
    def fallar_a_proposito(datos):
        # Simula un fallo sin hacer una petición real.
        raise ConnectionError("simulado")

    cadena_queja_falsa = RunnableLambda(fallar_a_proposito)

    cadena_queja_segura = construir_cadena_queja_segura(
        cadena_queja_falsa
    )

    resultado = cadena_queja_segura.invoke({
        "mensaje": "esto no funciona"
    })

    # Comprueba que respondió el fallback.
    assert resultado == (
        "Gracias por tu mensaje. Lo hemos recibido y estamos "
        "trabajando en ello. Te responderemos lo antes posible."
    )


def test_procesar_mensaje_seguro_no_propaga_excepciones():
    clasificacion_falsa = MagicMock()

    # En lugar de devolver una categoría, lanza una excepción.
    clasificacion_falsa.side_effect = ConnectionError("simulado")

    cadena_falsa = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
    )

    resultado = procesar_mensaje_seguro(
        cadena_falsa,
        "mensaje de prueba",
    )

    # El try/except debe entregar una respuesta.
    assert "no pudimos procesar" in resultado.lower()


def test_flujo_completo_conecta_fallback_de_queja(caplog):
    # caplog es una herramienta de pytest para capturar registros.
    consultas = []

    def responder(prompt):
        consultas.append(prompt.to_string())

        if len(consultas) == 1:
            # La clasificación funciona y selecciona queja.
            return AIMessage(content="queja")

        # La segunda consulta, que genera la respuesta, falla.
        raise ConnectionError("simulado en la ruta")

    # Construye el mismo flujo que utilizará el programa.
    flujo = construir_flujo(RunnableLambda(responder))

    # Captura los registros WARNING y superiores de este módulo.
    with caplog.at_level(
        logging.WARNING,
        logger="src.enrutamiento",
    ):
        resultado = procesar_mensaje_seguro(
            flujo,
            "La app se cierra",
        )

    # Confirma que se llegó a la segunda consulta.
    assert len(consultas) == 2

    # Confirma que se eligió la ruta de quejas.
    assert "Responde esta queja" in consultas[1]

    # Confirma que actuó el fallback de la ruta.
    assert resultado == (
        "Gracias por tu mensaje. Lo hemos recibido y estamos "
        "trabajando en ello. Te responderemos lo antes posible."
    )

    # Confirma que quedó registrada la causa del fallo.
    assert "simulado en la ruta" in caplog.text