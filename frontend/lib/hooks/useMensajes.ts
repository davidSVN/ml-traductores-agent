import useSWR from "swr";
import { getMensajes } from "../api";

export function useMensajes(convId: number | null) {
  return useSWR(
    convId ? ["mensajes", convId] : null,
    () => getMensajes(convId!),
    { refreshInterval: 3000 }
  );
}
