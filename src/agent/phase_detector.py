from src.agent.state import AgentState, is_ready_to_qualify


def detect_phase(state: AgentState) -> str:
    """
    Detecta la fase de la conversacion a partir del AgentState (dict en LangGraph).
    Python puro — NO es una tool del LLM, no consume tokens extra.

    Fases:
    - inicial: primera interaccion, sin datos del contacto
    - recopilando: recopilando nombre/empresa/email, aun no identificado en DB
    - cualificando: datos basicos completos, buscando cliente en DB
    - listo_para_cotizar: cliente_id resuelto, cotizacion aun no enviada
    - cotizando: cotizacion enviada por PDF, esperando decision del cliente

    NOTA: servicio/fecha/horario NO gatean la fase — el chatbot los ve en la
    conversacion y llama calcular_cotizacion cuando tenga suficiente informacion.
    """
    messages = state.get("messages", [])
    user_messages = [m for m in messages if getattr(m, "type", None) == "human"]

    cliente_id = state.get("cliente_id")
    cotizacion_id = state.get("cotizacion_id")

    # Sin ningun mensaje del cliente todavia → saludo inicial
    if len(user_messages) == 0:
        return "inicial"

    # A partir del primer mensaje del cliente, siempre tiene acceso a tools de cliente.
    # Las fases se evaluan en orden de prioridad:

    # Cotizacion enviada → esperando aprobacion/rechazo del cliente
    if cliente_id is not None and cotizacion_id is not None:
        return "cotizando"

    # Cliente identificado en DB → herramientas de cotizacion disponibles
    if cliente_id is not None:
        return "listo_para_cotizar"

    # Datos basicos completos (nombre+empresa+email en state via tools), sin cliente_id aun
    if is_ready_to_qualify(state):
        return "cualificando"

    # Default desde el primer mensaje: recopilando
    # El LLM tiene buscar_cliente, crear_cliente, crear_contacto disponibles
    return "recopilando"
