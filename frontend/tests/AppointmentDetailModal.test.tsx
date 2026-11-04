import React from 'react';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AppointmentDetailModal } from '../src/components/AppointmentDetailModal';
import { api } from '../src/services/api';
import { Appointment } from '../src/types';

vi.mock('../src/services/api', () => ({
  api: {
    getAppointmentEvents: vi.fn(),
  },
}));

const appointment: Appointment = {
  id: 42,
  reference_number: 'APT-42',
  carrier_id: 7,
  warehouse_id: 3,
  created_by: 1,
  scheduled_start: '2026-11-03T08:00:00Z',
  scheduled_end: '2026-11-03T09:00:00Z',
  status: 'PENDING',
  vehicle_registration: 'AB-123',
  vehicle_type: 'Truck',
  cargo_type: 'Pallets',
  created_at: '2026-11-01T10:00:00Z',
  updated_at: '2026-11-01T10:00:00Z',
};

describe('AppointmentDetailModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows an explicit message when appointment history cannot be loaded', async () => {
    vi.mocked(api.getAppointmentEvents).mockRejectedValue(new Error('History service unavailable'));

    render(
      <AppointmentDetailModal
        isOpen
        onClose={vi.fn()}
        appointment={appointment}
      />,
    );

    expect((await screen.findByRole('alert')).textContent).toContain('History service unavailable');
    expect(api.getAppointmentEvents).toHaveBeenCalledWith(appointment.id);
  });
});
