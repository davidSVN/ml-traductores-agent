import useSWR from "swr";
import { getStats } from "../api";

export function useStats() {
  return useSWR("stats", getStats, { refreshInterval: 30000 });
}
