import json
import os

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
    "M02": {"nombre": "Mouse", "precio": 6000, "stock": 12}
}

@tool
def consultar_producto(codigo: str) -> str:
    """Consulta nombre, precio en CLP y stock por codigo de producto.
    Usar para consultar datos de un producto. No calcula cotizaciones.
    """
    producto = PRODUCTOS.get(codigo.strip().upper())
    
    if producto is None:
        return "Producto no encontrado. Solicita un código que sea válido."
    
    return json.dumps(producto, ensure_ascii=False)

class ArgumentosCotizacion(BaseModel):
    precio_unitario: int = Field(
        gt=0,
        description="Precio de una unidad en CLP, obtenido de la consulta o del usuario."
    )
    cantidad: int = Field(
        gt=0,
        description="Cantidad de unidades; entero mayor que cero."
    )
    incluir_despacho: bool = Field(
        default=True,
        description="True para entrega a domicilio; False para retiro."
    )
    
@tool(args_schema=ArgumentosCotizacion)
def cotizar_compra(precio_unitario: int, cantidad: int, 
incluir_despacho: bool = True) -> str:
    """Calcula una cotizacion con precio unitario y cantidad conocidos.
    Despacho: 2500 CLP, gratis desde 30000 CLP de subtotal. Retiro: sin cargo.
    No consulta precios ni stock, no realiza compras ni reserva unidades.
    """
    subtotal = precio_unitario * cantidad
    despacho = 2500 if incluir_despacho and subtotal < 30000 else 0
    
    return json.dumps({
        "subtotal_clp": subtotal,
        "despacho_clp": despacho,
        "total_clp": subtotal + despacho,
    }, ensure_ascii=False) 
    
historiales = {}
    
def obtener_historial(session_id= str):
    if session_id not in historiales:
        historiales[session_id] = InMemoryChatMessageHistory()
    return historiales[session_id]

def normalizar_salida(resultado):
    """"Convierte la respuesta final a texto antes de guardarla en el historial."""
    texto = AIMessage(content=resultado["output"]).text
    
    return {
        **resultado,
        "output": str(texto),
    }

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
    print("Mensaje guardados:", len(obtener_historial(sesion).messages))
    
if __name__ == "__main__":
    modelo = ChatGoogleGenerativeAI(
    model=nombre_modelo,
    api_key=clave,
    temperature=0,
    timeout=30,
    max_retries=0,
)
    
    herramientas = [consultar_producto, cotizar_compra]
    prompt_agente = ChatPromptTemplate.from_messages([
        (
            "system",
            "Eres un asistente de una tienda de practica. Responde en espanol. "
            "Usa consultar_producto para consultar precios o stock y cotizar_compra "
            "para calcular totales. Usa el historial para entender referencias "
            "como 'ese producto' y cambios de cantidad. Puedes reutilizar el precio "
            "consultado antes en esta conversacion de practica. "
            "Si falta un dato y no esta en el historial, pidelo. "
            "No elijas un producto por tu cuenta ni inventes precios o cantidades. "
            "Solo cotizas; no realizas compras ni reservas stock."
        ),
        MessagesPlaceholder("chat_history"),
        ("human", "{entrada}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])
    
    agente = create_tool_calling_agent(
        modelo,
        herramientas,
        prompt_agente,
    )
    
    ejecutor_agente = AgentExecutor(
        agent=agente,
        tools=herramientas,
        return_intermediate_steps=True,
        max_iterations=4,
        verbose=False,
    )
    
    ejecutor_con_texto = (
        ejecutor_agente | RunnableLambda(normalizar_salida)
    )
    
    agente_con_memoria = RunnableWithMessageHistory(
        ejecutor_con_texto,
        obtener_historial,
        input_messages_key="entrada",
        history_messages_key="chat_history",
        output_messages_key="output",
    )
    
    config_a = {"configurable": {"session_id": "cliente_a"}}
    config_b = {"configurable": {"session_id": "cliente_b"}}

    resultado_1 = agente_con_memoria.invoke(
        {"entrada": "Consulta precio y stock del producto T01."},
        config=config_a,
    )
    mostrar_resultado(resultado_1, "cliente_a")

    resultado_2 = agente_con_memoria.invoke(
        {"entrada": "Cotiza 2 unidades de ese producto con despacho."},
        config=config_a,
    )
    mostrar_resultado(resultado_2, "cliente_a")

    resultado_3 = agente_con_memoria.invoke(
        {"entrada": "Y si fueran 3 unidades, tambien con despacho?"},
        config=config_a,
    )
    mostrar_resultado(resultado_3, "cliente_a")

    resultado_4 = agente_con_memoria.invoke(
        {"entrada": "Y si fueran 3 unidades, tambien con despacho?"},
        config=config_b,
    )
    mostrar_resultado(resultado_4, "cliente_b")
    