import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AppointmentModal } from '../src/components/AppointmentModal';
import { useAuth } from '../src/context/AuthContext';
import { api } from '../src/services/api';
import { Appointment, Carrier, Dock, Warehouse } from '../src/types';

vi.mock('../src/context/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('../src/services/api', () => ({
  api: {
    getWarehouses: vi.fn(),
    getCarriers: vi.fn(),
    getAvailableDocks: vi.fn(),
    createAppointment: vi.fn(),
  },
}));

const warehouse: Warehouse = {
  id: 3,
  name: 'Budapest Hub',
  code: 'BUD-1',
  address: 'Warehouse Road 1',
  city: 'Budapest',
  postal_code: '1000',
  country: 'Hungary',
  timezone: 'Europe/Budapest',
  is_active: true,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

const carrier: Carrier = {
  id: 7,
  company_name: 'North Freight',
  registration_number: 'NF-7',
  contact_email: 'dispatch@example.test',
  country: 'Hungary',
  is_active: true,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

const dock: Dock = {
  id: 11,
  warehouse_id: 3,
  dock_code: 'D-11',
  name: 'Dock 11',
  is_active: true,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

const createdAppointment: Appointment = {
  id: 42,
  reference_number: 'APT-42',
  carrier_id: 7,
  warehouse_id: 3,
  created_by: 2,
  scheduled_start: '2026-11-03T08:00:00Z',
  scheduled_end: '2026-11-03T09:00:00Z',
  status: 'PENDING',
  vehicle_registration: 'ABC-123',
  vehicle_type: 'Standard Semi-Trailer (40t)',
  cargo_type: 'General Palletized Goods',
  created_at: '2026-11-01T10:00:00Z',
  updated_at: '2026-11-01T10:00:00Z',
};

const fieldValue = (label: string) => (screen.getByLabelText(label) as HTMLInputElement).value;

describe('AppointmentModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: 2,
        email: 'carrier@example.test',
        full_name: 'Carrier User',
        role: 'CARRIER',
        is_active: true,
        carrier: {
          id: carrier.id,
          company_name: carrier.company_name,
          registration_number: carrier.registration_number,
        },
      },
      token: 'test-token',
      loading: false,
      login: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
      isAuthenticated: true,
      isCarrier: true,
      isWarehouse: false,
      isAdmin: false,
    });
    vi.mocked(api.getWarehouses).mockResolvedValue([warehouse]);
    vi.mocked(api.getCarriers).mockResolvedValue([carrier]);
    vi.mocked(api.getAvailableDocks).mockResolvedValue([]);
    vi.mocked(api.createAppointment).mockResolvedValue(createdAppointment);
  });

  it('requires appointment details to be entered and associates the carrier account', async () => {
    vi.mocked(api.getAvailableDocks).mockResolvedValue([dock]);
    const onClose = vi.fn();
    const onSuccess = vi.fn();
    render(
      <AppointmentModal
        isOpen
        onClose={onClose}
        onSuccess={onSuccess}
      />,
    );

    expect(await screen.findByRole('heading', { name: 'New Dock Appointment Request' })).toBeTruthy();
    expect(fieldValue('Destination Warehouse *')).toBe('');
    expect(fieldValue('Arrival Date *')).toBe('');
    expect(fieldValue('Vehicle Registration Number *')).toBe('');

    fireEvent.change(screen.getByLabelText('Destination Warehouse *'), {
      target: { value: String(warehouse.id) },
    });
    fireEvent.change(screen.getByLabelText('Arrival Date *'), { target: { value: '2026-11-03' } });
    fireEvent.change(screen.getByLabelText('Arrival Time *'), { target: { value: '08:00' } });
    fireEvent.change(screen.getByLabelText('Departure Date *'), { target: { value: '2026-11-03' } });
    fireEvent.change(screen.getByLabelText('Departure Time *'), { target: { value: '09:00' } });
    fireEvent.change(screen.getByLabelText('Vehicle Registration Number *'), {
      target: { value: 'HU-AB-123' },
    });
    fireEvent.change(screen.getByLabelText('Vehicle Type *'), {
      target: { value: 'Box Truck (18t)' },
    });
    fireEvent.change(screen.getByLabelText('Cargo Type *'), { target: { value: 'Palletized goods' } });
    fireEvent.click(screen.getByRole('button', { name: 'Check Dock Availability' }));
    await waitFor(() => expect(api.getAvailableDocks).toHaveBeenCalledOnce());
    expect(fieldValue('Dock Assignment')).toBe('');
    fireEvent.change(screen.getByLabelText('Dock Assignment'), {
      target: { value: String(dock.id) },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Submit Appointment Request' }));

    await waitFor(() => expect(api.createAppointment).toHaveBeenCalledOnce());
    const payload = vi.mocked(api.createAppointment).mock.calls[0][0];
    expect(payload.warehouse_id).toBe(warehouse.id);
    expect(payload.carrier_id).toBe(carrier.id);
    expect(payload.dock_id).toBe(dock.id);
    expect(payload.vehicle_registration).toBe('HU-AB-123');
    expect(payload.vehicle_type).toBe('Box Truck (18t)');
    expect(payload.cargo_type).toBe('Palletized goods');
    expect(payload.scheduled_start).toBe(new Date('2026-11-03T08:00:00').toISOString());
    expect(payload.scheduled_end).toBe(new Date('2026-11-03T09:00:00').toISOString());
    expect(payload.status).toBe('PENDING');
    expect(onSuccess).toHaveBeenCalledOnce();
    expect(onClose).toHaveBeenCalledOnce();
  });
});
