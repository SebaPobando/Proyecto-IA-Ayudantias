from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from src.cadena_tres_pasos import construir_cadena, main


def test_conecta_los_tres_pasos():
    prompts_recibidos = []

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

    assert len(prompts_recibidos) == 3
    assert "TEXTO_ORIGINAL" in prompts_recibidos[0]
    assert "IDEAS_EXTRAIDAS" in prompts_recibidos[1]
    assert "EXPLICACION_SIMPLE" in prompts_recibidos[2]
    assert resultado == "- Resultado final"


def test_simulacion_lee_archivo_y_registra_que_no_es_evidencia_real(tmp_path):
    import json

    entrada = tmp_path / "entrada.txt"
    salida = tmp_path / "registro.json"
    entrada.write_text("Un texto del proyecto para ensayar.", encoding="utf-8")

    main(["--simulado", "--archivo", str(entrada), "--salida", str(salida)])

    registro = json.loads(salida.read_text(encoding="utf-8"))
    assert registro["modo"] == "simulado"
    assert registro["texto_entrada"] == "Un texto del proyecto para ensayar."
    assert "SIMULADO" in registro["resultado"]


def test_rechaza_archivo_vacio_antes_de_crear_modelo(tmp_path, monkeypatch):
    from unittest.mock import Mock
    import pytest
    from src import cadena_tres_pasos

    entrada = tmp_path / "entrada.txt"
    entrada.write_text(" \n", encoding="utf-8")
    modelo = Mock()
    monkeypatch.setattr(cadena_tres_pasos, "construir_modelo_real", modelo)

    with pytest.raises(SystemExit) as error:
        main(["--archivo", str(entrada)])

    assert error.value.code == 2
    modelo.assert_not_called()


def test_impide_sobrescribir_el_archivo_de_entrada(tmp_path):
    import pytest

    entrada = tmp_path / "entrada.txt"
    entrada.write_text("Texto original.", encoding="utf-8")

    with pytest.raises(SystemExit):
        main(["--simulado", "--archivo", str(entrada), "--salida", str(entrada)])

    assert entrada.read_text(encoding="utf-8") == "Texto original."
