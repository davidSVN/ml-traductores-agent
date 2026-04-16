import useSWR from "swr";
import { getSolicitudDetalle } from "../api";

export function useSolicitudDetalle(id: number | null) {
  return useSWR(
    id ? ["solicitud-detalle", id] : null,
    () => getSolicitudDetalle(id!),
    { refreshInterval: 5000 }
  );
}
