import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { StatusTransitionModal } from '../src/components/StatusTransitionModal';
import { api } from '../src/services/api';
import { Appointment } from '../src/types';

vi.mock('../src/services/api', () => ({
  api: {
    getDocks: vi.fn(),
    updateAppointmentStatus: vi.fn(),
  },
}));

const appointment: Appointment = {
  id: 42,
  reference_number: 'APT-42',
  carrier_id: 7,
  warehouse_id: 3,
  dock_id: null,
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

describe('StatusTransitionModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.getDocks).mockResolvedValue([{
      id: 9,
      warehouse_id: 3,
      dock_code: 'D-09',
      name: 'Dock Nine',
      is_active: true,
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    }]);
    vi.mocked(api.updateAppointmentStatus).mockResolvedValue(appointment);
  });

  it('requires a rejection reason and submits a valid rejection', async () => {
    const onClose = vi.fn();
    const onSuccess = vi.fn();
    render(
      <StatusTransitionModal
        isOpen
        onClose={onClose}
        onSuccess={onSuccess}
        appointment={appointment}
        targetStatus="REJECTED"
      />,
    );

    fireEvent.submit(screen.getByRole('button', { name: 'Confirm Action' }).closest('form')!);
    expect(await screen.findByText('Please provide a rejection reason for the carrier.')).toBeTruthy();
    expect(api.updateAppointmentStatus).not.toHaveBeenCalled();

    fireEvent.change(screen.getByPlaceholderText(/State clearly why/), {
      target: { value: 'No dock capacity' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Confirm Action' }));

    await waitFor(() => expect(api.updateAppointmentStatus).toHaveBeenCalledWith(
      42,
      'REJECTED',
      'No dock capacity',
      undefined,
    ));
    expect(onSuccess).toHaveBeenCalledOnce();
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('reports dock lookup failures instead of leaving an unhandled rejection', async () => {
    vi.mocked(api.getDocks).mockRejectedValueOnce(new Error('Dock service unavailable'));
    render(
      <StatusTransitionModal
        isOpen
        onClose={vi.fn()}
        onSuccess={vi.fn()}
        appointment={appointment}
        targetStatus="CONFIRMED"
      />,
    );

    expect(await screen.findByText('Dock service unavailable')).toBeTruthy();
    expect(api.getDocks).toHaveBeenCalledWith(3);
    expect(api.updateAppointmentStatus).not.toHaveBeenCalled();
  });

  it('requires a user to select an active dock before confirming', async () => {
    const onClose = vi.fn();
    const onSuccess = vi.fn();
    render(
      <StatusTransitionModal
        isOpen
        onClose={onClose}
        onSuccess={onSuccess}
        appointment={appointment}
        targetStatus="CONFIRMED"
      />,
    );

    const dockSelect = screen.getByRole('combobox') as HTMLSelectElement;
    await screen.findByRole('option', { name: /D-09 — Dock Nine/ });
    expect(dockSelect.value).toBe('');
    fireEvent.submit(dockSelect.closest('form')!);
    expect(await screen.findByText('A dock must be assigned before confirming the appointment.')).toBeTruthy();
    expect(api.updateAppointmentStatus).not.toHaveBeenCalled();

    fireEvent.change(dockSelect, { target: { value: '9' } });
    fireEvent.click(screen.getByRole('button', { name: 'Confirm Action' }));

    await waitFor(() => expect(api.updateAppointmentStatus).toHaveBeenCalledWith(
      42,
      'CONFIRMED',
      undefined,
      9,
    ));
    expect(onSuccess).toHaveBeenCalledOnce();
    expect(onClose).toHaveBeenCalledOnce();
  });
});
