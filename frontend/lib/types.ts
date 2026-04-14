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
  cliente_nombre: string | null;
  numero_cotizacion: string | null;
  created_at: string | null;
}
