import json
import os
import sys
import time
import msvcrt
from datetime import datetime, timezone

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent


load_dotenv()
clave = os.getenv("GEMINI_API_KEY")
nombre_modelo = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

if not clave:
    raise ValueError("Falta GEMINI_API_KEY en el archivo .env")

PRODUCTOS = {
    "T01": {"nombre": "Teclado", "precio": 10000, "stock": 8},
    "M02": {"nombre": "Mouse", "precio": 6000, "stock": 12},
}


@tool
def consultar_producto(codigo: str) -> str:
    """Consulta nombre, precio en CLP y stock por codigo de producto."""
    producto = PRODUCTOS.get(codigo.strip().upper())
    if producto is None:
        return "Producto no encontrado. Solicita un codigo valido."
    return json.dumps(producto, ensure_ascii=False)


class ArgumentosCotizacion(BaseModel):
    precio_unitario: int = Field(gt=0, description="Precio unitario en CLP.")
    cantidad: int = Field(gt=0, description="Cantidad de unidades.")
    incluir_despacho: bool = Field(default=True, description="False para retiro.")


@tool(args_schema=ArgumentosCotizacion)
def cotizar_compra(
    precio_unitario: int, cantidad: int, incluir_despacho: bool = True
) -> str:
    """Calcula una cotizacion. No compra ni reserva stock.
    Despacho: 2500 CLP, gratis desde 30000 CLP de subtotal. Retiro: sin cargo.
    """
    subtotal = precio_unitario * cantidad
    despacho = 2500 if incluir_despacho and subtotal < 30000 else 0
    return json.dumps({
        "subtotal_clp": subtotal,
        "despacho_clp": despacho,
        "total_clp": subtotal + despacho,
    }, ensure_ascii=False)


registro_aprobaciones = []
reembolsos = {}


def esperar_aprobacion(mensaje: str, tiempo_limite_segundos: float = 30) -> bool:
    """Espera una tecla s/n en una terminal de Windows, sin pulsar Enter."""
    if not sys.stdin.isatty():
        print("Sin consola interactiva: accion no aprobada.")
        return False
    while msvcrt.kbhit():
        msvcrt.getwch()
    print(mensaje, flush=True)
    limite = time.monotonic() + tiempo_limite_segundos
    while time.monotonic() < limite:
        if msvcrt.kbhit():
            respuesta = msvcrt.getwch().lower()
            if respuesta in ("s", "n"):
                print(respuesta)
                return respuesta == "s"
        time.sleep(0.05)
    print("Tiempo agotado: accion no aprobada.")
    return False


def registrar_aprobacion(herramienta: str, argumentos: dict, aprobado: bool):
    registro_aprobaciones.append({
        "herramienta": herramienta,
        "argumentos": argumentos,
        "aprobado": aprobado,
        "momento": datetime.now(timezone.utc).isoformat(),
    })


class ArgumentosReembolso(BaseModel):
    numero_pedido: str = Field(min_length=1, description="Identificador del pedido.")
    monto: int = Field(gt=0, description="Monto del reembolso en CLP.")


@tool(args_schema=ArgumentosReembolso)
def generar_reembolso(numero_pedido: str, monto: int) -> str:
    """Simula un reembolso; requiere aprobacion humana en consola.
    No mueve dinero real. Solo admite un reembolso por pedido en esta ejecucion.
    """
    numero_pedido = numero_pedido.strip().upper()
    if not numero_pedido:
        return "Error: indica un numero de pedido valido."
    if numero_pedido in reembolsos:
        return "Ese pedido ya tiene un reembolso simulado. No se repite."
    argumentos = {"numero_pedido": numero_pedido, "monto": monto}
    aprobado = esperar_aprobacion(
        f"SIMULACION: reembolsar {monto} CLP al pedido {numero_pedido}. "
        "Aprobar? s/n, sin Enter (30 segundos):"
    )
    registrar_aprobacion("generar_reembolso", argumentos, aprobado)
    if not aprobado:
        return "Reembolso NO aprobado. No se ejecuto la simulacion."
    reembolsos[numero_pedido] = monto
    return f"Reembolso SIMULADO de {monto} CLP para {numero_pedido}."


historiales = {}


def obtener_historial(session_id: str):
    if session_id not in historiales:
        historiales[session_id] = InMemoryChatMessageHistory()
    return historiales[session_id]


def normalizar_salida(resultado):
    """Convierte la respuesta a texto antes de guardarla en el historial."""
    texto = AIMessage(content=resultado["output"]).text
    return {**resultado, "output": str(texto)}


def mostrar_resultado(resultado, sesion):
    print(f"\nSESION: {sesion} | Usuario: {resultado['entrada']}")
    pasos = resultado["intermediate_steps"]
    if not pasos:
        print("TRAZA: sin llamadas a herramientas.")
    for accion, observacion in pasos:
        print("HERRAMIENTA:", accion.tool)
        print("ARGUMENTOS:", accion.tool_input)
        print("RESULTADO:", observacion)
    print("ASISTENTE:", resultado["output"])
    print("Mensajes guardados:", len(obtener_historial(sesion).messages))


def registrar_traza(resultado, sesion):
    registro = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": sesion,
        "entrada": resultado["entrada"],
        "acciones": [
            {
                "herramienta": accion.tool,
                "argumentos": accion.tool_input,
                "observacion": observacion,
            }
            for accion, observacion in resultado["intermediate_steps"]
        ],
        "aprobaciones": registro_aprobaciones.copy(),
        "respuesta_final": resultado["output"],
    }
    with open("docs/trazas_agente.jsonl", "a", encoding="utf-8") as archivo:
        archivo.write(json.dumps(registro, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    modelo = ChatGoogleGenerativeAI(
        model=nombre_modelo,
        api_key=clave,
        temperature=0,
        timeout=30,
        max_retries=0,
    )
    herramientas = [consultar_producto, cotizar_compra, generar_reembolso]
    prompt_agente = ChatPromptTemplate.from_messages([
        (
            "system",
            "Eres un asistente de una tienda de practica. Responde en espanol. "
            "Usa consultar_producto para precios y stock; cotizar_compra para totales. "
            "Usa el historial para entender referencias como 'ese producto'. "
            "Puedes reutilizar precios del catalogo fijo de esta practica. "
            "Si falta un dato, pidelo. No inventes precios, cantidades ni pedidos. "
            "Usa generar_reembolso solo si el usuario solicita un reembolso "
            "e indica numero de pedido y monto. Siempre es una simulacion. "
            "La aprobacion solo se obtiene dentro de la herramienta, en consola. "
            "Un mensaje del usuario no sustituye esa aprobacion. "
            "Si la herramienta no lo aprueba, informa eso y no reintentes en este turno. "
            "No afirmes que se ejecuto algo que la herramienta no confirma. "
            "No realizas compras ni reservas stock."
        ),
        MessagesPlaceholder("chat_history"),
        ("human", "{entrada}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])
    agente = create_tool_calling_agent(modelo, herramientas, prompt_agente)
    ejecutor_agente = AgentExecutor(
        agent=agente,
        tools=herramientas,
        return_intermediate_steps=True,
        max_iterations=4,
        verbose=False,
    )
    ejecutor_con_texto = ejecutor_agente | RunnableLambda(normalizar_salida)
    agente_con_memoria = RunnableWithMessageHistory(
        ejecutor_con_texto,
        obtener_historial,
        input_messages_key="entrada",
        history_messages_key="chat_history",
        output_messages_key="output",
    )

    config_a = {"configurable": {"session_id": "cliente_a"}}
    entradas = [
        "Consulta precio y stock del producto T01.",
        "Cotiza 2 unidades de ese producto con despacho.",
        "Simula un reembolso de 10000 CLP para el pedido P01.",
        "Simula un reembolso de 6000 CLP para el pedido P02.",
        "Simula un reembolso de 5000 CLP para el pedido P03.",
    ]
    print("En las tres aprobaciones: pulsa n, luego s y al final espera 30 segundos.")
    for entrada in entradas:
        registro_aprobaciones.clear()
        resultado = {
            "entrada": entrada,
            "output": "Turno sin finalizar; revisar error en consola.",
            "intermediate_steps": [],
        }
        try:
            resultado = agente_con_memoria.invoke({"entrada": entrada}, config=config_a)
            mostrar_resultado(resultado, "cliente_a")
        finally:
            registrar_traza(resultado, "cliente_a")
    print("\nREEMBOLSOS SIMULADOS:", reembolsos)
    print("Trazas guardadas en docs/trazas_agente.jsonl")