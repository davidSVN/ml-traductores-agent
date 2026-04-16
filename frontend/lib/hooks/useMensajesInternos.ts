import useSWR from "swr";
import { getMensajesInternos } from "../api";

export function useMensajesInternos(solicitudId: number | null) {
  return useSWR(
    solicitudId ? ["mensajes-internos", solicitudId] : null,
    () => getMensajesInternos(solicitudId!),
    { refreshInterval: 3000 }
  );
}
