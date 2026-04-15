"use client";

import { useState } from "react";
import { ConversationList } from "@/components/chats/ConversationList";
import { ChatWindow } from "@/components/chats/ChatWindow";

export default function ChatsPage() {
  const [selectedId, setSelectedId] = useState<number | null>(null);

  return (
    <div className="flex h-screen">
      {/* Lista: siempre visible en md+, en móvil solo cuando NO hay chat seleccionado */}
      <div className={`${selectedId !== null ? "hidden" : "flex"} md:flex flex-col w-full md:w-80 md:shrink-0`}>
        <ConversationList selectedId={selectedId} onSelect={setSelectedId} />
      </div>

      {/* Chat: siempre visible en md+, en móvil solo cuando HAY chat seleccionado */}
      <div className={`${selectedId !== null ? "flex" : "hidden"} md:flex flex-1 flex-col overflow-hidden`}>
        <ChatWindow convId={selectedId} onBack={() => setSelectedId(null)} />
      </div>
    </div>
  );
}
