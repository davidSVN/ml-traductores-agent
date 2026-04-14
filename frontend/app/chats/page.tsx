"use client";

import { useState } from "react";
import { ConversationList } from "@/components/chats/ConversationList";
import { ChatWindow } from "@/components/chats/ChatWindow";

export default function ChatsPage() {
  const [selectedId, setSelectedId] = useState<number | null>(null);

  return (
    <div className="flex h-screen">
      <ConversationList selectedId={selectedId} onSelect={setSelectedId} />
      <div className="flex-1 overflow-hidden">
        <ChatWindow convId={selectedId} />
      </div>
    </div>
  );
}
