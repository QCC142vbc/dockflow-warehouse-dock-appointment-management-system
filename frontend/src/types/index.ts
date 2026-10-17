export type UserRole = 'ADMIN' | 'WAREHOUSE_MANAGER' | 'WAREHOUSE_STAFF' | 'CARRIER';

export type AppointmentStatus =
  | 'DRAFT'
  | 'PENDING'
  | 'CONFIRMED'
  | 'REJECTED'
  | 'CANCELLED'
  | 'CHECKED_IN'
  | 'ARRIVED'
  | 'IN_PROGRESS'
  | 'COMPLETED'
  | 'NO_SHOW';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface CurrentUserContext extends User {
  carrier?: {
    id: number;
    company_name: string;
    registration_number: string;
  } | null;
  warehouses?: Array<{
    id: number;
    name: string;
    code: string;
  }>;
}

export interface Carrier {
  id: number;
  company_name: string;
  registration_number: string;
  contact_email: string;
  contact_phone?: string | null;
  address?: string | null;
  country: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Warehouse {
  id: number;
  name: string;
  code: string;
  address: string;
  city: string;
  postal_code: string;
  country: string;
  timezone: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Dock {
  id: number;
  warehouse_id: number;
  dock_code: string;
  name: string;
  description?: string | null;
  max_vehicle_length?: number | null;
  max_vehicle_weight?: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface DockCapability {
  id: number;
  dock_id: number;
  capability_type: string;
  capability_value: string;
  description?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface DockUnavailability {
  id: number;
  dock_id: number;
  reason_type: string;
  description?: string | null;
  start_time: string;
  end_time: string;
  reported_by?: number | null;
  created_at: string;
}

export interface Appointment {
  id: number;
  reference_number: string;
  carrier_id: number;
  warehouse_id: number;
  dock_id?: number | null;
  created_by: number;
  scheduled_start: string;
  scheduled_end: string;
  status: AppointmentStatus;
  vehicle_registration: string;
  vehicle_type: string;
  cargo_type: string;
  cargo_description?: string | null;
  cargo_weight_kg?: number | null;
  container_number?: string | null;
  notes?: string | null;
  rejection_reason?: string | null;
  created_at: string;
  updated_at: string;
  carrier_name?: string | null;
  warehouse_name?: string | null;
  dock_code?: string | null;
}

export interface AppointmentCreate {
  warehouse_id: number;
  carrier_id: number;
  dock_id?: number | null;
  scheduled_start: string;
  scheduled_end: string;
  vehicle_registration: string;
  vehicle_type: string;
  cargo_type: string;
  cargo_description?: string | null;
  cargo_weight_kg?: number | null;
  container_number?: string | null;
  notes?: string | null;
  status?: AppointmentStatus;
}

export interface AppointmentEvent {
  id: number;
  appointment_id: number;
  changed_by?: number | null;
  previous_status?: string | null;
  new_status: string;
  reason?: string | null;
  event_type: string;
  created_at: string;
}

export interface AuditLog {
  id: number;
  user_id?: number | null;
  action: string;
  entity_type: string;
  entity_id?: number | null;
  description?: string | null;
  old_values?: Record<string, unknown> | null;
  new_values?: Record<string, unknown> | null;
  ip_address?: string | null;
  created_at: string;
}

export interface DailyVolumeItem {
  date: string;
  count: number;
}

export interface DashboardMetrics {
  total_appointments: number;
  pending_appointments: number;
  confirmed_appointments: number;
  completed_appointments: number;
  cancelled_appointments: number;
  no_show_appointments: number;
  in_progress_appointments: number;
  checked_in_appointments: number;
  dock_utilization_percent: number;
  status_distribution: Record<string, number>;
  daily_volume: DailyVolumeItem[];
  total_docks: number;
  active_docks: number;
  total_warehouses: number;
}
