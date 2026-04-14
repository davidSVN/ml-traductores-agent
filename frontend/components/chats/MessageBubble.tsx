import type { Mensaje } from "@/lib/types";
import { formatRelativeTime } from "@/lib/utils";
import { cn } from "@/lib/utils";

export function MessageBubble({ msg }: { msg: Mensaje }) {
  const isAgent = msg.origen === "agente";

  return (
    <div className={cn("flex", isAgent ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[75%] rounded-2xl px-4 py-2.5 text-sm",
          isAgent
            ? "bg-accent-purple/20 text-text-primary rounded-tr-sm"
            : "bg-surface text-text-primary rounded-tl-sm"
        )}
      >
        {msg.tipo_contenido === "documento" && msg.url_archivo ? (
          <a
            href={msg.url_archivo}
            target="_blank"
            rel="noopener noreferrer"
            className="text-accent-purple underline"
          >
            📄 Ver documento
          </a>
        ) : (
          <p className="whitespace-pre-wrap break-words">{msg.contenido}</p>
        )}
        <p
          className={cn(
            "text-xs mt-1",
            isAgent ? "text-text-muted text-right" : "text-text-muted"
          )}
        >
          {formatRelativeTime(msg.created_at)}
        </p>
      </div>
    </div>
  );
}
