import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor

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
def consultar_precio(consulta: str) -> str:
    """Consulta nombre, precio en CLP y stock de un producto.
    Acepta su nombre, como teclado o mouse, o su código, como T01.
    Úsala cuando el usuario pregunte por precio o disponibilidad.
    No calcula cotizaciones ni realiza compras.
    """
    consulta_limpia = consulta.strip().casefold()
    
    for codigo, producto in PRODUCTOS.items():
        coincide_codigo = consulta_limpia == codigo.casefold()
        coincide_nombre = consulta_limpia == producto["nombre"].casefold()
        
        if coincide_codigo or coincide_nombre:
            return (
                f"Producto: {producto['nombre']}. "
                f"Precio unitario: {producto['precio']} CLP. "
                f"Stock disponible: {producto['stock']} unidades."
            )
            
    return "Producto no encontrado. Pide al usuario que revise el nombre o código."

@tool
def cotizar_compra(precio_unitario: int, cantidad: int) -> str:
    """Calcula una cotización en CLP con precio unitario y cantidad conocidos.
    Incluye un despacho fijo de 2500 CLP.
    Úsala cuando el usuario necesite calcular un total.
    No consulta productos, no verifica stock y no realiza compras.
    """
    if precio_unitario <= 0 or cantidad <= 0:
        return "Error: el precio y la cantidad deben ser mayores que cero."
    
    subtotal = precio_unitario * cantidad
    despacho = 2500
    total = subtotal + despacho
    
    return (
        f"Subtotal: {subtotal} CLP. "
        f"Despacho: {despacho} CLP. "
        f"Total: {total} CLP."
    )
    
modelo = ChatGoogleGenerativeAI(
    model=nombre_modelo,
    api_key=clave,
    temperature=0,
    timeout=20,
    max_retries=0,
)

herramientas = [consultar_precio, cotizar_compra]
    
instrucciones = (
    "Eres un asistente de una tienda de práctica. Responde en español. "
    "Para consultar precios o stock del catálogo, usa consultar_producto. "
    "Para calcular totales, usa cotizar_compra. "
    "Si el usuario menciona un producto por nombre o código y pide una cotización, "
    "consulta primero su precio. "
    "Si el usuario proporciona un precio explícito, puedes cotizar directamente. "
    "No inventes productos, precios, cantidades ni resultados. "
    "Si falta información, pídela. "
    "Si el producto no existe, informa eso sin inventar una cotización. "
    "Si la cantidad solicitada supera el stock consultado, informa la limitación. "
    "Para un saludo, responde directamente sin usar herramientas. "
    "Solo informas y cotizas; no realizas compras."
)

prompt = ChatPromptTemplate.from_messages([
    ("system", instrucciones),
    ("human", "{entrada}"),
    MessagesPlaceholder("agent_scratchpad"),
])

agente = create_tool_calling_agent(
    llm=modelo,
    tools=herramientas,
    prompt=prompt,
)

ejecutor = AgentExecutor(
    agent=agente,
    tools=herramientas,
    return_intermediate_steps=True,
    verbose=False,
    max_iterations=4,
)

def probar(entrada: str):
    print("\nPREGUNTA:", entrada)

    resultado = ejecutor.invoke({"entrada": entrada})
    pasos = resultado["intermediate_steps"]

    print("\nTRAZA DE HERRAMIENTAS:")

    if not pasos:
        print("No se utilizaron herramientas.")
        
    for numero, (accion, observacion) in enumerate(pasos, start=1):
        print(f"\nPaso {numero}")
        print("Herramienta:", accion.tool)
        print("Argumentos:", accion.tool_input)
        print("Observación:", observacion)

    print("\nRESPUESTA FINAL:")
    
    salida = resultado["output"]
    
    if isinstance(salida, str):
        print(salida)
    else:
        texto = "\n".join(
            bloque["text"]
            for bloque in salida
            if isinstance(bloque, dict)
            and bloque.get("type") == "text"
            and isinstance(bloque.get("text"), str)
        )
        print(texto)
        
if __name__ == "__main__":
    print("Asistente de tienda")
    
    nombres = ", ".join(
        producto["nombre"]
        for producto in PRODUCTOS.values()
    )
    
    print("Productos disponibles:", nombres)
    print("Escribe 'salir' para terminar.")
    
    while True:
        entrada = input("\nTu pregunta: ").strip()
        
        if entrada.lower() == "salir":
            break
        
        if not entrada:
            continue
        
        probar(entrada)