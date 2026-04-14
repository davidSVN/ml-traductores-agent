import useSWR from "swr";
import { getConversaciones, type ConversacionesParams } from "../api";

export function useConversaciones(params: ConversacionesParams) {
  return useSWR(
    ["conversaciones", params],
    () => getConversaciones(params),
    { refreshInterval: 5000, keepPreviousData: true }
  );
}
