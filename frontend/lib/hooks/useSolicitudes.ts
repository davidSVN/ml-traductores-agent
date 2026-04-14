import useSWR from "swr";
import { getSolicitudes } from "../api";

export function useSolicitudes(estado?: string) {
  return useSWR(
    ["solicitudes", estado],
    () => getSolicitudes({ estado }),
    { refreshInterval: 30000 }
  );
}
