# Proyecto Gradual Ayudantías — Especialización en Desarrollo con IA Generativa (Accenture)

## Actualizacion hasta el bloque 32

El asistente de tienda incorpora indexacion con fuentes, RAG con citas, evaluacion
de recuperacion, registro de tiempos y consumo, dataset de personalizacion,
decision fundamentada, proteccion ante inyeccion, versionado y supervision de prompts.

El recorrido sin API se ejecuta desde la raiz:

```powershell
.\venv\Scripts\python.exe -m src.demo_bloque32
.\venv\Scripts\python.exe -m pytest -q
```

Los comandos nuevos se ejecutan como modulos, con `python -m src.nombre`.
El modo predeterminado no llama a proveedores. `--real` se pide expresamente.
La demostracion usa Chroma persistente con vectores lexicos locales y respuestas
extractivas: comprueba conexiones y controles, no calidad semantica de un modelo.
No inventa tokens ni costos: si faltan datos, quedan `null`.

Consulta [la guia de ejecucion](docs/guia_bloques24_32.md),
[la matriz de riesgos](docs/matriz_riesgos.md),
[la decision de personalizacion](docs/decision_personalizacion.md) y
[el estado de las evidencias](docs/estado_bloque32.md).

Para revisar y activar la ultima version del prompt:

```powershell
.\venv\Scripts\python.exe -m src.registro_prompts
.\venv\Scripts\python.exe -m src.grafo_supervision
```

El segundo comando pausa y pide `aprobar` o `rechazar`. Solo una aprobacion humana
cambia `.local/prompt_activo.json`, que lee el flujo RAG. `--verificar` prueba ambas
ramas sin cambiar la version activa. Es un flujo local de una consola, con estado
del grafo en memoria; no es un sistema de aprobaciones de produccion.

Para el modo real, agrega en tu `.env` existente las variables documentadas en
`.env.example`: clave, modelo, modelo de embeddings y, si quieres estimar costo
de generacion, las dos tarifas verificadas en USD por millon de tokens. El costo
mostrado no incluye embeddings, indexacion ni otros cargos. No se han ejecutado
consultas reales ni entrenamiento como parte de esta actualizacion.

Si el entorno `venv` informa `No Python at ...`, su interprete base no esta
disponible en esa sesion. Puedes crear otro entorno sin borrar el anterior:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m src.demo_bloque32
```

Si usas ese entorno, reemplaza `venv` por `.venv` en los comandos de esta guia.

Esta es la estructura base que vas a usar como punto de partida para tu proyecto en este programa. Es la misma estructura que vas a ir ampliando bloque a bloque, hasta llegar a la aplicación completa que entregas en el Gate 3.

## Cómo empezar

Estos pasos se completan de forma progresiva a lo largo de la Unidad U1.2, no todos el mismo día:

1. Descarga este archivo comprimido (adjunto en la plataforma) y descomprímelo en tu computador. Inicializa el control de versiones sobre esa carpeta y registra tu primer commit con esta estructura base, tal como llegó, antes de modificar nada.
2. Crea tu entorno virtual de Python (por ejemplo, con `venv`) y actívalo.
3. Instala las dependencias que necesites y regístralas en `requirements.txt` (al inicio puede estar vacío o con muy pocas).
4. Copia `.env.example` a un archivo nuevo llamado `.env`, y completa ahí tus credenciales reales (llaves de API, tokens). El archivo `.env` nunca se sube al repositorio: ya está excluido en `.gitignore`.

## Estructura de carpetas

- `src/` : todo el código fuente de tu proyecto va aquí.
- `docs/` : documentación técnica del proyecto (diagramas, decisiones de arquitectura, notas).
- `tests/` : pruebas de tu código (las vas a usar más adelante en el programa, cuando el proyecto lo requiera).
- `requirements.txt` : dependencias de Python de tu proyecto, para que cualquier otra persona pueda reconstruir tu entorno con un solo comando.
- `.env.example` : plantilla de las variables de entorno que tu proyecto necesita, sin valores reales. Tu archivo `.env` real (con tus credenciales) nunca se commitea.
- `.gitignore` : le dice a Git qué archivos y carpetas ignorar (entre ellos, tu entorno virtual y tu archivo `.env`).

## Reglas que se mantienen durante todo el programa

- Ningún secreto (contraseña, llave de API, token) va escrito directamente en el código ni en ningún archivo que se suba al repositorio.
- Cada proyecto nuevo tiene su propio entorno virtual: no se comparten dependencias entre proyectos distintos.
- Todo el trabajo que se entrega en este programa vive en un repositorio de GitHub, sin excepción.

## Bloque 18 — Cadena de tres tareas

`src/cadena_tres_pasos.py` conecta extracción de ideas, simplificación y formato.
Cada tarea tiene su propia plantilla y usa el resultado de la anterior. La función
`construir_cadena(modelo)` recibe el modelo para poder reemplazarlo en las pruebas.

Ejecuta los comandos desde la raíz de `ProyectoIA`, utilizando su entorno virtual.
Para ensayar las conexiones con respuestas prefijadas, sin consumir API:

```powershell
.\venv\Scripts\python.exe -m src.cadena_tres_pasos --simulado
```

Para usar una entrada real del proyecto, consultar Gemini y guardar entrada y resultado:

```powershell
.\venv\Scripts\python.exe -m src.cadena_tres_pasos --real --archivo README.md --salida docs/bloque18_real.json
```

Puedes reemplazar `README.md` por otro archivo de texto UTF-8 relacionado con tu
proyecto. El modo real realiza tres consultas al modelo, sin contar reintentos.
Requiere `GEMINI_API_KEY` en el `.env` de la raíz; el conector prioriza
`GOOGLE_API_KEY` si ambas variables están definidas.

La simulación comprueba las conexiones con resultados prefijados; no evalúa la
calidad ni sustituye una corrida real para la entrega. Revisa el registro real
contra la entrada y explica por qué las tres tareas aportan valor a tu caso.

## Bloque 19 — Clasificación y enrutamiento

`src/enrutamiento.py` clasifica mensajes como pregunta, queja o sugerencia.
`RunnablePassthrough.assign` agrega la categoría conservando el mensaje original.
`RunnableBranch` ejecuta una ruta con instrucciones específicas para ese caso.
La salida conserva mensaje, categoría, ruta y respuesta para poder inspeccionarla.

Como en el material del curso, la ruta de preguntas es también la ruta por defecto:
recibe cualquier categoría que no coincida con queja o sugerencia. Una categoría
desconocida no es un error de conexión; la gestión de fallos corresponde al bloque 20.

Demostración sin API de tres categorías y una categoría desconocida:

```powershell
.\venv\Scripts\python.exe -m src.enrutamiento
```

Una ejecución real con un mensaje propio:

```powershell
.\venv\Scripts\python.exe -m src.enrutamiento --real --mensaje "La aplicación se cierra cuando subo una foto."
```

Cada mensaje real realiza dos consultas al modelo: clasificación y respuesta en la
ruta elegida, sin contar reintentos. Las instrucciones de las tres rutas se adaptan
en `construir_flujo`; el modelo se crea únicamente al pedir el modo real.

## Comprobación de los bloques 18 y 19

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m pytest -q
```

Las pruebas verifican que los resultados del bloque 18 alimentan el paso siguiente,
que cada categoría del bloque 19 elige una sola ruta, que el mensaje se conserva y
que la ruta por defecto y la normalización funcionan. Utilizan modelos simulados.

Para cerrar la evidencia del bloque 18 falta ejecutar y revisar una corrida real
sobre un texto propio, más allá del ejemplo introductorio de tokenización. El
comando con `--archivo` y `--salida` permite conservar esa evidencia. Para el bloque
19, prueba además mensajes reales de las tres categorías y revisa sus resultados.
