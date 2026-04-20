import type {
  Contacto,
  LineaCotizacion,
  MensajesResponse,
  MensajesInternosResponse,
  MensajeInterno,
  ModificarLineasPayload,
  PaginatedResponse,
  ResolverSolicitudPayload,
  SolicitudDetalle,
  Stats,
  UpdatePricingPayload,
} from "./types";
import type { Conversacion, Cliente, Servicio, Equipo, Solicitud } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

function qs(params: Record<string, string | number | boolean | undefined | null | string[]>): string {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") {
      p.set(k, String(v));
    }
  }
  return p.toString();
}

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, options);
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`);
  return res.json();
}

// Stats
export const getStats = () => apiFetch<Stats>("/dashboard/stats");

// Conversaciones
export interface ConversacionesParams {
  estado?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export const getConversaciones = (p: ConversacionesParams) =>
  apiFetch<PaginatedResponse<Conversacion>>(`/dashboard/conversaciones?${qs(p as Record<string, string | number | boolean | undefined | null>)}`);

export const getMensajes = (id: number, params?: { limit?: number; before_id?: number }) =>
  apiFetch<MensajesResponse>(`/dashboard/conversaciones/${id}/mensajes?${qs((params ?? {}) as Record<string, string | number | boolean | undefined | null>)}`);

export const patchLeer = (id: number) =>
  apiFetch<{ ok: boolean }>(`/dashboard/conversaciones/${id}/leer`, { method: "PATCH" });

// Clientes
export interface ClientesParams {
  search?: string;
  es_recurrente?: boolean;
  page?: number;
  page_size?: number;
}

export const getClientes = (p: ClientesParams) =>
  apiFetch<PaginatedResponse<Cliente>>(`/dashboard/clientes?${qs(p as Record<string, string | number | boolean | undefined | null>)}`);

export const getContactos = (clienteId: number) =>
  apiFetch<{ data: Contacto[] }>(`/dashboard/clientes/${clienteId}/contactos`);

// Servicios
export const getServicios = (p: { tipo?: string; activo?: boolean; page?: number }) =>
  apiFetch<PaginatedResponse<Servicio | Equipo>>(`/dashboard/servicios?${qs(p as Record<string, string | number | boolean | undefined | null>)}`);

// Solicitudes
export const getSolicitudes = (p: { estado?: string; page?: number }) =>
  apiFetch<PaginatedResponse<Solicitud>>(`/dashboard/solicitudes?${qs(p as Record<string, string | number | boolean | undefined | null>)}`);

export const getSolicitudDetalle = (id: number) =>
  apiFetch<SolicitudDetalle>(`/dashboard/solicitudes/${id}`);

export const getMensajesInternos = (id: number) =>
  apiFetch<MensajesInternosResponse>(`/dashboard/solicitudes/${id}/mensajes`);

export const postMensajeInterno = (id: number, contenido: string) =>
  apiFetch<MensajeInterno>(`/dashboard/solicitudes/${id}/mensajes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ contenido }),
  });

export const resolverSolicitud = (id: number, data: ResolverSolicitudPayload) =>
  apiFetch<SolicitudDetalle>(`/dashboard/solicitudes/${id}/resolver`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

export const updateClientePricing = (clienteId: number, data: UpdatePricingPayload) =>
  apiFetch<Cliente>(`/dashboard/clientes/${clienteId}/pricing`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

export const updateContacto = (contactoId: number, data: Partial<Contacto>) =>
  apiFetch<Contacto>(`/dashboard/contactos/${contactoId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

export const getLineasCotizacion = (cotizacionId: number) =>
  apiFetch<LineaCotizacion[]>(`/dashboard/cotizaciones/${cotizacionId}/lineas`);

export const modificarLineas = (solicitudId: number, data: ModificarLineasPayload) =>
  apiFetch<SolicitudDetalle>(`/dashboard/solicitudes/${solicitudId}/modificar-lineas`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

export const updateCotizacion = (
  cotizacionId: number,
  payload: { incluir_terminos_corporativos?: boolean }
) =>
  apiFetch<{ ok: boolean; incluir_terminos_corporativos: boolean }>(
    `/dashboard/cotizaciones/${cotizacionId}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }
  );
