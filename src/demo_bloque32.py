"""Recorre las piezas de bloques 24 a 32 sin credenciales ni servicios remotos."""
from .indexar_corpus import indexar
from .registro_prompts import main as registrar_prompts
from .registro_rag import registrar_consulta
from .evaluar_recuperacion import main as evaluar
from .dataset_tuning import main as preparar_dataset
from .decision import main as documentar_decision
from .matriz_riesgos import main as generar_matriz
from .grafo_supervision import verificar
from .logging_rag import main as probar_seguridad


def main():
    print("DEMOSTRACION SIN API. Los vectores son lexicos y la respuesta es extractiva.")
    print("Indice:", indexar())
    registrar_prompts()
    evaluar()
    for pregunta in ("Que precio tiene el teclado T01?", "Desde cuando el despacho es gratis?",
                      "El reembolso requiere aprobacion humana?"):
        resultado = registrar_consulta(pregunta, k=3)
        print(resultado["respuesta"])
    registrar_consulta("Que precio tiene el teclado T01?", k=6)
    probar_seguridad()
    preparar_dataset()
    documentar_decision()
    generar_matriz()
    verificar()
    print("Listo. Documentacion en docs y evidencias locales en docs/evidencias_simuladas.")
    print("No cambia el prompt activo ni ejecuta entrenamiento. La evidencia real del bloque 28 sigue pendiente.")


if __name__ == "__main__":
    main()
