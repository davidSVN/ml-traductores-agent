import useSWR from "swr";
import { getServicios } from "../api";

export function useServicios(tipo?: string) {
  return useSWR(
    ["servicios", tipo],
    () => getServicios({ tipo, activo: true }),
    { refreshInterval: 60000 }
  );
}
