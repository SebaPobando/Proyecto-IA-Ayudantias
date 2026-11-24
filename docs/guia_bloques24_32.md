# Ejecucion de ProyectoIA hasta el bloque 32

Ejecuta desde la raiz del proyecto con el entorno propio. Los comandos de la tabla
suponen el entorno activado; tambien puedes usar `venv\Scripts\python.exe`.

| Bloque | Pieza incorporada | Comando sin API |
|---|---|---|
| 24 | Comparacion de cortes fijos y recursivos | `python -m src.indexar_corpus --comparar` |
| 25 | Chroma persistente, IDs, fuentes y actualizaciones | `python -m src.indexar_corpus` |
| 26 | Recuperacion y respuesta con citas | `python -m src.recuperacion --pregunta "Precio del teclado T01?"` |
| 27 | 10 preguntas etiquetadas, precision, recall y MRR | `python -m src.evaluar_recuperacion` |
| 28 | Medicion por etapa y campos de uso/costo | `python -m src.registro_rag --k 3` |
| 29 | 12 ejemplos ficticios, balance y validacion | `python -m src.dataset_tuning` |
| 30 | Decision RAG, fine-tuning y PEFT, con sensibilidad | `python -m src.decision` |
| 31 | Trazas minimizadas y consulta sospechosa detenida | `python -m src.logging_rag` |
| 32 | Dos versiones y diff | `python -m src.registro_prompts` |
| 32 | Supervision humana del prompt activo | `python -m src.grafo_supervision` |
| 32 | Verificacion automatica de pausa y ambas decisiones | `python -m src.grafo_supervision --verificar` |
| 32 | Matriz de seis riesgos con controles y responsables | `python -m src.matriz_riesgos` |

Para recorrer todo sin API: `python -m src.demo_bloque32`.
Las piezas de los bloques anteriores siguen disponibles; se corrigieron imports
del cliente y la construccion anticipada del modelo del enrutamiento para que la
suite funcione sin claves. El comando de la cadena del bloque 18 vuelve a aceptar
`--simulado`, `--archivo`, `--salida` y `--real` conforme al README.

## Corpus y persistencia

La fuente editable es `data/corpus_tienda.json`, con 10 documentos derivados del
catalogo, reglas y limites del agente que ya existia. No se inventa una politica
de devolucion de 30 dias. `data/evaluacion_recuperacion.json` contiene 10 preguntas
con etiquetas previas. Los resultados se guardan sin alterar esas etiquetas.

El indice de demostracion vive en `.local/vectorstore_demo`; el real usa por
defecto `vectorstore_b32`. Ambos usan una coleccion nueva `proyectoia_b32`, de modo
que no se reemplaza una coleccion antigua creada por versiones previas.
Reindexar actualiza por ID y elimina los chunks que dejaron de pertenecer a esta
coleccion. Un manifiesto identifica el modelo: si cambia, usa otra carpeta e indexa
de nuevo. Los scores de Chroma son distancias: menor significa mas cercano.

El chunk size 200 y overlap 30 mantienen completos los documentos cortos actuales.
Antes de usar textos mas largos, compara los cortes y repite la evaluacion. Un
overlap repite caracteres: sumar longitudes no equivale al tamano del corpus.

## RAG del proveedor y evidencia del bloque 28

El modo real requiere variables en `.env`. No publiques claves. Los IDs de modelos
se configuran segun lo que este disponible en tu cuenta; no se impone uno nuevo.

```powershell
python -m src.indexar_corpus --real
python -m src.evaluar_recuperacion --real
python -m src.registro_rag --real --pregunta "Que precio tiene el teclado T01?" --k 3
python -m src.registro_rag --real --pregunta "Desde que subtotal el despacho es gratis?" --k 3
python -m src.registro_rag --real --pregunta "El reembolso exige aprobacion humana?" --k 3
python -m src.registro_rag --real --pregunta "Que precio tiene el teclado T01?" --k 6
```

Estos comandos si consumen el servicio. No se ejecutaron en esta actualizacion.
Revisa tokens, citas, respuesta y latencia de cada etapa. Con k mayor, el contexto
tiende a crecer; compruebalo con los datos reales, no con tokens inventados.
El costo calculado cubre solamente generacion bajo las tarifas que configures y
los datos de uso recibidos. El costo de embeddings se deja desconocido.

Los registros reales quedan en `.local/registros_reales`, excluida de Git.
La clave `pregunta` es `null` por defecto. Para una evidencia que necesite el texto,
`--guardar-pregunta` permite guardarlo de forma explicita: usa solo consultas
ficticias sin datos personales y revisa el archivo antes de compartirlo.

## Supervision y limites

Una deteccion de inyeccion detiene toda la consulta: no genera aunque queden
documentos limpios. El responsable revisa la fuente marcada y decide corregirla o
excluirla antes de reindexar y repetir. Los patrones pueden fallar o producir falsos
positivos. La validacion de citas comprueba numero y existencia, no que una fuente
respalde semanticamente cada afirmacion.

La version registrada mas reciente no se activa por si sola. Para aprobarla, una
persona ejecuta `python -m src.grafo_supervision`, lee el diff y toma la decision.
Cada solicitud tiene un thread_id unico. La comprobacion automatica no constituye
una aprobacion humana. La activacion local no ofrece concurrencia multiproceso ni
autorizacion por roles. Un sistema de produccion necesita un checkpointer durable,
control de acceso y un mecanismo transaccional de activacion.

## Fuentes del curso y entregables

Se revisaron los materiales de U2.5, U2.6 y U2.7 disponibles en la carpeta del curso.
Los archivos se ubican en `src` siguiendo la estructura del repositorio.
Para la Core 32 estan `src/registro_prompts.py`, `src/grafo_supervision.py` y
`src/matriz_riesgos.py`; la tabla legible esta en `docs/matriz_riesgos.md`.
La Core 30 queda documentada en `docs/decision_personalizacion.md`.
La Core 28 requiere todavia evidencia real, separada de la demostracion.
