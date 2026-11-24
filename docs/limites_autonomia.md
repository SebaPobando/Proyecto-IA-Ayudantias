# Limites de autonomia del asistente de tienda

El agente existente consulta precio y stock y calcula cotizaciones. Cotizar no
compra ni reserva productos. Su historial se separa por session_id y vive en
memoria. El catalogo del ejercicio es fijo, no representa stock de una tienda real.

La herramienta generar_reembolso solo simula. Exige numero de pedido y monto
positivo, pide aprobacion por consola con limite de 30 segundos y rechaza si no
hay consola, hay una negativa o vence el plazo. La peticion del usuario no es una
aprobacion. Dentro de una ejecucion evita repetir un reembolso por pedido; el
registro no es durable y no protege frente a reinicios o procesos concurrentes.

El flujo RAG nuevo es consultivo: no dispone de herramientas para comprar o mover
dinero. Recupera fuentes, filtra contexto y genera una respuesta con citas, o la
retiene para revision. Las decisiones comerciales de excepcion se derivan a una
persona. El cambio del prompt se revisa en el grafo de supervision antes de alterar
la version local activa.

Las trazas nuevas contienen metadatos para reconstruir el flujo sin copiar entradas,
argumentos de herramientas ni respuestas completas. Las trazas historicas previas
a esta actualizacion no se modifican automaticamente. No hay control de acceso
por roles ni aprobaciones persistentes de produccion: esos controles siguen pendientes.
