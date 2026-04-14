import { MessageSquare } from "lucide-react";

export function EmptyChat() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center p-8">
      <div className="w-16 h-16 rounded-full bg-surface flex items-center justify-center mb-4">
        <MessageSquare size={28} className="text-text-muted" />
      </div>
      <p className="text-text-secondary font-medium">Selecciona una conversación</p>
      <p className="text-text-muted text-sm mt-1">
        Elige un chat de la lista para ver los mensajes
      </p>
    </div>
  );
}
