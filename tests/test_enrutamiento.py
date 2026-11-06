import pytest

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from src.enrutamiento import (
    construir_paso_clasificacion,
    construir_cadena_con_enrutamiento,
    construir_flujo,
)

@pytest.mark.parametrize("categoria,ruta_esperada", [
    ("queja", "queja"),
    ("sugerencia", "sugerencia"),
    ("pregunta", "pregunta"),
    ("categoria_inventada", "pregunta"),
])
def test_selecciona_solo_una_ruta_y_conserva_mensaje(categoria, ruta_esperada):
    ejecutadas = []

    def crear_ruta(nombre):
        def responder(datos):
            ejecutadas.append(nombre)
            assert datos["mensaje"] == "mensaje original"
            assert datos["categoria"] == categoria
            return nombre
        return RunnableLambda(responder)

    clasificador = RunnableLambda(lambda datos: categoria)
    flujo = construir_cadena_con_enrutamiento(
        clasificador,
        crear_ruta("queja"),
        crear_ruta("sugerencia"),
        crear_ruta("pregunta"),
    )
    entrada = {"mensaje": "mensaje original"}
    resultado = flujo.invoke(entrada)

    assert resultado == ruta_esperada
    assert ejecutadas == [ruta_esperada]
    assert entrada == {"mensaje": "mensaje original"}


@pytest.mark.parametrize("salida,esperada", [
    (" Queja \n", "queja"),
    ("QUEJA.", "queja"),
    ("no estoy seguro", "no estoy seguro"),
])
def test_normaliza_la_salida_del_modelo(salida, esperada):
    modelo = RunnableLambda(lambda prompt: AIMessage(content=salida))
    clasificador = construir_paso_clasificacion(modelo)
    assert clasificador.invoke({"mensaje": "un mensaje"}) == esperada


@pytest.mark.parametrize("categoria,ruta", [
    ("queja", "queja"),
    ("sugerencia", "sugerencia"),
    ("pregunta", "pregunta/default"),
    ("desconocida", "pregunta/default"),
])
def test_flujo_completo_usa_dos_consultas_y_preserva_datos(categoria, ruta):
    prompts = []
    respuestas = iter([categoria, "respuesta simulada"])

    def responder(prompt):
        prompts.append(prompt.to_string())
        return AIMessage(content=next(respuestas))

    flujo = construir_flujo(RunnableLambda(responder))
    resultado = flujo.invoke({"mensaje": "MENSAJE ORIGINAL"})

    assert len(prompts) == 2
    assert all("MENSAJE ORIGINAL" in prompt for prompt in prompts)
    assert resultado == {
        "mensaje": "MENSAJE ORIGINAL",
        "categoria": categoria,
        "ruta": ruta,
        "respuesta": "respuesta simulada",
    }