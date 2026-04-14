from langgraph.graph import MessagesState


class State(MessagesState):
    """Conversational agent state.

    Inherits `messages` from MessagesState with the add_messages reducer.
    """

    client_phone: str = ""
    client_name: str = ""
    channel: str = ""  # whatsapp, instagram, gmail, web
    active_skill: str = ""  # currently loaded skill name, if any
