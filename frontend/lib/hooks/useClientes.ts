import useSWR from "swr";
import { getClientes, type ClientesParams } from "../api";

export function useClientes(params: ClientesParams) {
  return useSWR(
    ["clientes", params],
    () => getClientes(params),
    { refreshInterval: 60000, keepPreviousData: true }
  );
}
