import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# 1. Cargar las variables del archivo .env
load_dotenv()

# 2. Verificar la clave antes de llamar a la API
if not os.environ.get("GEMINI_API_KEY"):
    raise SystemExit('Falta GEMINI_API_KEY. Defínela en tu archivo ".env" y vuelve a ejecutar.')

# 3. Inicializar el modelo de embeddings
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

# 4. Llamar a la API e informar con claridad cualquier fallo
try:
    vector = embeddings.embed_query("El cliente reintenta ante un error")
except Exception as error:
    mensaje = str(error)
    if "429" in mensaje or "RESOURCE_EXHAUSTED" in mensaje:
        print("Límite de peticiones alcanzado. Espera un minuto y vuelve a ejecutar.")
    elif "API key" in mensaje or "401" in mensaje or "403" in mensaje:
        print('La API rechazó tu clave. Revisa el valor de GEMINI_API_KEY en tu ".env".')
    else:
        print("No se pudo generar el embedding:", type(error).__name__)
    print("Detalle técnico:", mensaje)
    raise SystemExit(1)

# 5. Mostrar el resultado
print(len(vector))
print(vector[:5])