# Decision de personalizacion de ProyectoIA

## 1 El problema

El asistente de tienda necesita responder con el catalogo y las reglas de cotizacion y autonomia del proyecto, citando la fuente. El problema actual es aportar informacion comprobable. No se ha medido un defecto persistente de formato en un modelo real.

## 2 Resultado del metodo

Puntajes del metodo del curso: {'RAG': 2, 'Fine-tuning completo': 0, 'PEFT': 1}. Candidata: RAG.

Se fija como restriccion de esta iteracion no entrenar y poder probar cambios localmente en menos de un dia: iteracion rapida=True. El corpus tiene 10 documentos, pero no hay historial de tres meses que demuestre cambios mensuales: informacion_cambia_seguido=False provisional. No hay muestra de 20 respuestas reales con 3 fallos de formato: problema_de_formato_o_tono=False provisional, no es una tasa de fallo cero. Hay 12 ejemplos ficticios, menos que los 200 del criterio del curso: dataset_grande_y_de_calidad=False. Se mantiene un solo asistente: multiples_variantes=False.

Sensibilidad: si se confirmara que la informacion cambia mensualmente, los puntos pasarian a {'RAG': 5, 'Fine-tuning completo': 0, 'PEFT': 1}. La preferencia por RAG se mantiene. Revisar las respuestas provisionales al contar con evidencia real.

## 3 Tecnica elegida y por que

Se mantiene RAG, con instrucciones versionadas y supervisadas. Las fuentes se pueden corregir y reindexar sin entrenamiento. Los 12 ejemplos sirven para ensayar balance y validacion; no demuestran que el tuning mejore el sistema. No se realizo fine-tuning, PEFT ni soft-prompting. PEFT ajusta una fraccion de parametros; el soft-prompting aprende vectores de entrada y no consiste en editar un prompt de texto. No se presenta ninguna de esas tecnicas como ejecutada.

## 4 Que se necesita para ejecutarla

El corpus preparado contiene 10 documentos con IDs y fuentes; faltan 0 por preparar. El indice local se puede regenerar sin API. Para validar el RAG del proveedor faltan indexacion real, las 10 preguntas de recuperacion y al menos 3 consultas con tokens y tiempos reales, mas una comparacion de k=3 y k=6. No se han obtenido esas evidencias en esta actualizacion.

El dataset tiene 12 ejemplos ficticios, 4 por cada una de 3 intenciones. Frente al criterio orientativo de 200 ejemplos faltan 188, ademas de revisar y separar entrenamiento de evaluacion. No se aprueba invertir en entrenamiento hasta medir primero el problema de comportamiento y el costo de datos, computo y tiempo.
