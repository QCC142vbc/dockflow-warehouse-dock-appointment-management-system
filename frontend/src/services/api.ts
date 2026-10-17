import {
  Appointment,
  AppointmentCreate,
  AppointmentEvent,
  AppointmentStatus,
  AuditLog,
  Carrier,
  CurrentUserContext,
  DashboardMetrics,
  Dock,
  DockCapability,
  DockUnavailability,
  User,
  Warehouse,
} from '../types';

const API_BASE = '/api/v1';

class ApiClient {
  private token: string | null = null;

  constructor() {
    if (typeof window !== 'undefined' && window.localStorage) {
      this.token = window.localStorage.getItem('dockflow_token');
    }
  }

  setToken(token: string | null) {
    this.token = token;
    if (typeof window !== 'undefined' && window.localStorage) {
      if (token) {
        window.localStorage.setItem('dockflow_token', token);
      } else {
        window.localStorage.removeItem('dockflow_token');
      }
    }
  }

  getToken(): string | null {
    return this.token;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string>),
    };

    if (this.token && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    if (options.body && !(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    const res = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (res.status === 401) {
      // Token invalid or expired
      if (this.token && !endpoint.includes('/auth/login')) {
        this.setToken(null);
        window.dispatchEvent(new Event('auth:unauthorized'));
      }
    }

    if (!res.ok) {
      let errorMessage = `HTTP Error ${res.status}`;
      try {
        const errorJson = await res.json();
        if (errorJson.detail) {
          if (typeof errorJson.detail === 'string') {
            errorMessage = errorJson.detail;
          } else if (Array.isArray(errorJson.detail)) {
            // Pydantic validation error array
            errorMessage = errorJson.detail.map((e: any) => `${e.loc?.join('.') || ''}: ${e.msg}`).join(', ');
          } else if (typeof errorJson.detail === 'object') {
            // Structured detail e.g. conflicts
            if (errorJson.detail.conflicts) {
              errorMessage = errorJson.detail.conflicts.map((c: any) => c.message).join(' | ');
            } else if (errorJson.detail.message) {
              errorMessage = errorJson.detail.message;
            } else {
              errorMessage = JSON.stringify(errorJson.detail);
            }
          }
        }
      } catch {
        // Fallback to response status text
        errorMessage = res.statusText || errorMessage;
      }
      throw new Error(errorMessage);
    }

    if (res.status === 204) {
      return null as unknown as T;
    }

    return res.json();
  }

  // --- Auth ---
  async login(username: string, password: string): Promise<{ access_token: string; token_type: string; user: CurrentUserContext }> {
    const body = new URLSearchParams();
    body.append('username', username);
    body.append('password', password);

    const res = await this.request<{ access_token: string; token_type: string; user: CurrentUserContext }>('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body,
    });

    this.setToken(res.access_token);
    return res;
  }

  async getMe(): Promise<CurrentUserContext> {
    return this.request<CurrentUserContext>('/auth/me');
  }

  // --- Dashboard ---
  async getDashboardMetrics(warehouseId?: number, days = 7): Promise<DashboardMetrics> {
    const params = new URLSearchParams();
    if (warehouseId) params.append('warehouse_id', warehouseId.toString());
    params.append('days', days.toString());
    return this.request<DashboardMetrics>(`/dashboard/metrics?${params.toString()}`);
  }

  // --- Appointments ---
  async getAppointments(filters?: {
    warehouse_id?: number;
    carrier_id?: number;
    dock_id?: number;
    appointment_status?: AppointmentStatus;
    start_date?: string;
    end_date?: string;
  }): Promise<Appointment[]> {
    const params = new URLSearchParams();
    if (filters?.warehouse_id) params.append('warehouse_id', filters.warehouse_id.toString());
    if (filters?.carrier_id) params.append('carrier_id', filters.carrier_id.toString());
    if (filters?.dock_id) params.append('dock_id', filters.dock_id.toString());
    if (filters?.appointment_status) params.append('appointment_status', filters.appointment_status);
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);

    return this.request<Appointment[]>(`/appointments/?${params.toString()}`);
  }

  async getAppointment(id: number): Promise<Appointment> {
    return this.request<Appointment>(`/appointments/${id}`);
  }

  async getAppointmentEvents(id: number): Promise<AppointmentEvent[]> {
    return this.request<AppointmentEvent[]>(`/appointments/${id}/events`);
  }

  async createAppointment(data: AppointmentCreate): Promise<Appointment> {
    return this.request<Appointment>('/appointments/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateAppointment(id: number, data: Partial<AppointmentCreate>): Promise<Appointment> {
    return this.request<Appointment>(`/appointments/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async updateAppointmentStatus(id: number, status: AppointmentStatus, reason?: string, dockId?: number): Promise<Appointment> {
    return this.request<Appointment>(`/appointments/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status, reason, dock_id: dockId }),
    });
  }

  // --- Warehouses ---
  async getWarehouses(): Promise<Warehouse[]> {
    return this.request<Warehouse[]>('/warehouses/');
  }

  async getWarehouse(id: number): Promise<Warehouse> {
    return this.request<Warehouse>(`/warehouses/${id}`);
  }

  async createWarehouse(data: Partial<Warehouse>): Promise<Warehouse> {
    return this.request<Warehouse>('/warehouses/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateWarehouse(id: number, data: Partial<Warehouse>): Promise<Warehouse> {
    return this.request<Warehouse>(`/warehouses/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  // --- Docks ---
  async getDocks(warehouseId?: number): Promise<Dock[]> {
    const params = new URLSearchParams();
    if (warehouseId) params.append('warehouse_id', warehouseId.toString());
    return this.request<Dock[]>(`/docks/?${params.toString()}`);
  }

  async getDock(id: number): Promise<Dock> {
    return this.request<Dock>(`/docks/${id}`);
  }

  async getAvailableDocks(params: {
    warehouse_id: number;
    start_time: string;
    end_time: string;
    vehicle_length?: number;
    vehicle_weight?: number;
    exclude_appointment_id?: number;
  }): Promise<Dock[]> {
    const q = new URLSearchParams();
    q.append('warehouse_id', params.warehouse_id.toString());
    q.append('start_time', params.start_time);
    q.append('end_time', params.end_time);
    if (params.vehicle_length) q.append('vehicle_length', params.vehicle_length.toString());
    if (params.vehicle_weight) q.append('vehicle_weight', params.vehicle_weight.toString());
    if (params.exclude_appointment_id) q.append('exclude_appointment_id', params.exclude_appointment_id.toString());

    return this.request<Dock[]>(`/docks/availability?${q.toString()}`);
  }

  async createDock(data: Partial<Dock>): Promise<Dock> {
    return this.request<Dock>('/docks/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateDock(id: number, data: Partial<Dock>): Promise<Dock> {
    return this.request<Dock>(`/docks/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async getDockCapabilities(dockId: number): Promise<DockCapability[]> {
    return this.request<DockCapability[]>(`/docks/${dockId}/capabilities`);
  }

  async createDockCapability(dockId: number, data: Partial<DockCapability>): Promise<DockCapability> {
    return this.request<DockCapability>(`/docks/${dockId}/capabilities`, {
      method: 'POST',
      body: JSON.stringify({ ...data, dock_id: dockId }),
    });
  }

  // --- Dock Unavailability ---
  async getDockUnavailability(params?: { dock_id?: number; start_date?: string; end_date?: string }): Promise<DockUnavailability[]> {
    const q = new URLSearchParams();
    if (params?.dock_id) q.append('dock_id', params.dock_id.toString());
    if (params?.start_date) q.append('start_date', params.start_date);
    if (params?.end_date) q.append('end_date', params.end_date);
    return this.request<DockUnavailability[]>(`/dock-unavailability/?${q.toString()}`);
  }

  async createDockUnavailability(data: Partial<DockUnavailability>): Promise<DockUnavailability> {
    return this.request<DockUnavailability>('/dock-unavailability/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async deleteDockUnavailability(id: number): Promise<void> {
    return this.request<void>(`/dock-unavailability/${id}`, {
      method: 'DELETE',
    });
  }

  // --- Carriers ---
  async getCarriers(): Promise<Carrier[]> {
    return this.request<Carrier[]>('/carriers/');
  }

  async getCarrier(id: number): Promise<Carrier> {
    return this.request<Carrier>(`/carriers/${id}`);
  }

  async createCarrier(data: Partial<Carrier>): Promise<Carrier> {
    return this.request<Carrier>('/carriers/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateCarrier(id: number, data: Partial<Carrier>): Promise<Carrier> {
    return this.request<Carrier>(`/carriers/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  // --- Users & Assignments ---
  async getUsers(): Promise<User[]> {
    return this.request<User[]>('/users/');
  }

  async createUser(data: any): Promise<User> {
    return this.request<User>('/users/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateUser(id: number, data: any): Promise<User> {
    return this.request<User>(`/users/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async getUserAssignments(userId: number): Promise<{ user_id: number; carriers: Carrier[]; warehouses: Warehouse[] }> {
    return this.request<{ user_id: number; carriers: Carrier[]; warehouses: Warehouse[] }>(`/users/${userId}/assignments`);
  }

  async assignUserCarrier(userId: number, carrierId: number): Promise<any> {
    return this.request(`/users/${userId}/carrier/${carrierId}`, { method: 'POST' });
  }

  async unassignUserCarrier(userId: number, carrierId: number): Promise<any> {
    return this.request(`/users/${userId}/carrier/${carrierId}`, { method: 'DELETE' });
  }

  async assignUserWarehouse(userId: number, warehouseId: number): Promise<any> {
    return this.request(`/users/${userId}/warehouse/${warehouseId}`, { method: 'POST' });
  }

  async unassignUserWarehouse(userId: number, warehouseId: number): Promise<any> {
    return this.request(`/users/${userId}/warehouse/${warehouseId}`, { method: 'DELETE' });
  }

  // --- Audit Logs ---
  async getAuditLogs(params?: { entity_type?: string; entity_id?: number; action?: string; limit?: number }): Promise<AuditLog[]> {
    const q = new URLSearchParams();
    if (params?.entity_type) q.append('entity_type', params.entity_type);
    if (params?.entity_id) q.append('entity_id', params.entity_id.toString());
    if (params?.action) q.append('action', params.action);
    if (params?.limit) q.append('limit', params.limit.toString());
    return this.request<AuditLog[]>(`/audit-logs/?${q.toString()}`);
  }
}

export const api = new ApiClient();
