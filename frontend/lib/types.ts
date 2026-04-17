export interface PaginationMeta {
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  meta: PaginationMeta;
}

export interface Stats {
  conversaciones_activas: number;
  cotizaciones_total: number;
  cotizaciones_este_mes: number;
  ingresos_total: number;
  ingresos_este_mes: number;
  solicitudes_pendientes: number;
  clientes_total: number;
}

export interface Conversacion {
  id: number;
  cliente_id: number | null;
  cliente_nombre: string | null;
  nombre_temporal: string | null;
  telefono_whatsapp: string | null;
  estado: string;
  ultimo_mensaje_preview: string | null;
  ultimo_mensaje_at: string | null;
  mensajes_no_leidos: number;
  created_at: string | null;
}

export interface ConversacionDetalle {
  id: number;
  nombre_temporal: string | null;
  telefono_whatsapp: string | null;
  estado: string;
  cliente_nombre: string | null;
}

export interface Mensaje {
  id: number;
  origen: "cliente" | "agente" | string;
  contenido: string;
  tipo_contenido: string;
  url_archivo: string | null;
  created_at: string | null;
}

export interface MensajesResponse {
  conversacion: ConversacionDetalle;
  mensajes: Mensaje[];
  has_more: boolean;
}

export interface Cliente {
  id: number;
  nombre_empresa: string | null;
  tipo_cliente: string | null;
  nit: string | null;
  es_recurrente: boolean | null;
  ciudad: string | null;
  nivel_precio: string | null;
  exento_iva: boolean | null;
  servicios_confirmados: number | null;
  ultima_cotizacion: string | null;
  contactos_count: number;
}

export interface Contacto {
  id: number;
  nombre_completo: string;
  email: string | null;
  telefono: string | null;
  cargo: string | null;
  es_principal: boolean | null;
  puede_aprobar_cotizacion: boolean | null;
}

export interface Servicio {
  id: number;
  nombre: string;
  categoria: string;
  unidad_cobro: string;
  idioma_origen: string;
  idioma_destino: string;
  precio_base: number;
  precio_cliente: number;
  es_presencial: boolean;
  activo: boolean;
}

export interface Equipo {
  id: number;
  tipo_equipo: string;
  cantidad_min: number;
  cantidad_max: number;
  num_dias: number | null;
  precio_proveedor: number;
  precio_cliente: number;
  descripcion: string | null;
  activo: boolean;
}

export interface Solicitud {
  id: number;
  tipo: string;
  estado: string;
  prioridad: string | null;
  titulo: string;
  descripcion: string | null;
  cliente_nombre: string | null;
  numero_cotizacion: string | null;
  created_at: string | null;
}

export interface SolicitudDetalle {
  id: number;
  tipo: string;
  estado: string;
  prioridad: string | null;
  titulo: string;
  descripcion: string | null;
  datos_formulario: Record<string, unknown>;
  respuesta_encargada: string | null;
  created_at: string | null;
  resuelta_at: string | null;
  cliente_id: number | null;
  cliente_nombre: string | null;
  cliente_nivel_precio: string | null;
  cliente_descuento_min: number | null;
  cliente_descuento_max: number | null;
  cliente_markup: number | null;
  cliente_notas_pricing: string | null;
  contacto_id: number | null;
  contacto_nombre: string | null;
  contacto_email: string | null;
  contacto_telefono: string | null;
  contacto_cargo: string | null;
  cotizacion_id: number | null;
  numero_cotizacion: string | null;
  cotizacion_total: number | null;
  cotizacion_estado: string | null;
}

export interface MensajeInterno {
  id: number;
  origen: "agente" | "encargada";
  contenido: string;
  tipo_contenido: string;
  created_at: string | null;
}

export interface MensajesInternosResponse {
  mensajes: MensajeInterno[];
  solicitud_estado: string;
}

export interface ResolverSolicitudPayload {
  accion: "aprobar" | "rechazar" | "modificar";
  respuesta?: string;
  nivel_precio?: string;
  descuento_min?: number;
  descuento_max?: number;
  markup_personalizado?: number;
  notas_pricing?: string;
}

export interface UpdatePricingPayload {
  nivel_precio?: string;
  descuento_min_porcentaje?: number;
  descuento_max_porcentaje?: number;
  markup_personalizado?: number;
  notas_pricing?: string;
}

export interface LineaCotizacion {
  id: number;
  descripcion: string;
  precio_total: number;
  fecha_inicio: string | null;
  fecha_fin: string | null;
  horario: string | null;
}

export interface ModificarLineaPayload {
  linea_id: number;
  nuevo_precio: number;
}

export interface ModificarLineasPayload {
  lineas: ModificarLineaPayload[];
  respuesta?: string;
}
