from src.agent.state import AgentState, is_ready_to_qualify


def detect_phase(state: AgentState) -> str:
    """
    Detecta la fase de la conversación a partir del AgentState (dict en LangGraph).
    Python puro — NO es una tool del LLM, no consume tokens extra.

    Fases:
    - inicial: primera interacción, sin datos del contacto
    - recopilando: recopilando nombre/empresa/email, aún no identificado en DB
    - cualificando: datos básicos completos, buscando cliente en DB
    - listo_para_cotizar: cliente_id resuelto → chatbot tiene calcular_cotizacion disponible

    NOTA: servicio/fecha/horario NO gatean la fase — el chatbot los ve en la
    conversación y llama calcular_cotizacion cuando tenga suficiente información.
    """
    messages = state.get("messages", [])
    user_messages = [m for m in messages if getattr(m, "type", None) == "human"]

    nombre = state.get("nombre")
    empresa = state.get("empresa")
    cliente_id = state.get("cliente_id")

    # Sin mensajes del cliente todavía (o solo uno) y sin datos de contacto
    if len(user_messages) <= 1 and not nombre and not empresa:
        return "inicial"

    # Cliente identificado en DB → todas las herramientas de cotización disponibles
    if cliente_id is not None:
        return "listo_para_cotizar"

    # Datos básicos completos, aún sin cliente_id → buscar/crear cliente
    if is_ready_to_qualify(state):
        return "cualificando"

    # Recopilando datos de contacto
    if nombre or empresa:
        return "recopilando"

    return "inicial"
