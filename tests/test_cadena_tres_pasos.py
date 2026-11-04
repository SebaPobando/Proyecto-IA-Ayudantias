from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from src.cadena_tres_pasos import construir_cadena


def test_cadena_conecta_las_tres_tareas():
    prompts_recibidos = []

    # Una respuesta prefijada para cada consulta al modelo.
    respuestas = iter([
        "IDEAS_EXTRAIDAS",
        "EXPLICACION_SIMPLE",
        "- Resultado final",
    ])

    def responder(prompt):
        prompts_recibidos.append(prompt.to_string())
        return AIMessage(content=next(respuestas))

    modelo_falso = RunnableLambda(responder)
    cadena = construir_cadena(modelo_falso)

    resultado = cadena.invoke({"texto": "TEXTO_ORIGINAL"})

    # Se hicieron exactamente tres consultas.
    assert len(prompts_recibidos) == 3

    # Cada tarea recibió el contenido correspondiente.
    assert prompts_recibidos[0].endswith("TEXTO_ORIGINAL")
    assert prompts_recibidos[1].endswith("IDEAS_EXTRAIDAS")
    assert prompts_recibidos[2].endswith("EXPLICACION_SIMPLE")

    # La cadena devuelve el texto producido por la última tarea.
    assert isinstance(resultado, str)
    assert resultado == "- Resultado final"