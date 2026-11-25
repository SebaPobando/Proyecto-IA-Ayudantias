# GATE 2 - CHECKLIST DE ENTREGA PROYECTO

**NOMBRE PROYECTO:**________

## 1. Pipeline RAG Funcional - 25%

- [ ] El corpus se indexa y el índice queda guardado para reutilizarlo.
- [ ] El sistema recupera fragmentos del índice y genera una respuesta de punta a punta.

## 2. Seguridad, versionado y gobernanza - 20%

- [ ] Probé el filtro contra prompt injection y guardé el resultado.
- [ ] Tengo un registro de las versiones del prompt y puedo identificar cuál está activa.
- [ ] Tengo una matriz de riesgos PROPIA con sus controles.

## 3. Calidad de recuperación y citación - 15%

- [ ] Medí precisión y exhaustividad con preguntas de mi propio corpus.
- [ ] Las respuestas citan sus fuentes y puedo abrirlas para comprobar que respaldan lo que se afirma.

## 4. Personalización justificada - 15%

- [ ] Expliqué por qué elegí RAG para mi caso y comparé esa decisión con fine-tuning y PEFT.

## 5. Observabilidad y trazabilidad - 15%

- [ ] El sistema genera logs estructurados en JSON y evita registrar datos sensibles.
- [ ] Puedo seguir las etapas de una consulta con el mismo "trace_id".
- [ ] Registré el consumo de tokens según el modo de ejecución.

## 6. Costo, latencia y checklist operativo - 10%

- [ ] Registré la latencia y el costo por consulta.
- [ ] El README explica cómo instalar, indexar y ejecutar una consulta para comprobar el flujo.

## Opcionales

- [ ] Integración con un agente con  memoria.
- [ ] Uso de LangGraph.