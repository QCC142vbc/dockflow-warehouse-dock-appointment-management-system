import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { App } from '../src/App';
import { useAuth } from '../src/context/AuthContext';
import { UserRole } from '../src/types';

vi.mock('../src/context/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('../src/pages/LoginPage', () => ({ LoginPage: () => <div>Login screen</div> }));
vi.mock('../src/pages/DashboardPage', () => ({ DashboardPage: () => <div>Dashboard screen</div> }));
vi.mock('../src/pages/CarrierPortalPage', () => ({ CarrierPortalPage: () => <div>Carrier screen</div> }));
vi.mock('../src/pages/WarehousePortalPage', () => ({ WarehousePortalPage: () => <div>Warehouse screen</div> }));
vi.mock('../src/pages/AdminPortalPage', () => ({ AdminPortalPage: () => <div>Admin screen</div> }));
vi.mock('../src/components/AppointmentModal', () => ({ AppointmentModal: () => null }));
vi.mock('../src/components/StatusTransitionModal', () => ({ StatusTransitionModal: () => null }));
vi.mock('../src/components/AppointmentDetailModal', () => ({ AppointmentDetailModal: () => null }));

const authValue = (role: UserRole) => ({
  user: {
    id: 1,
    email: 'user@example.test',
    full_name: 'Test User',
    role,
    is_active: true,
  },
  token: 'test-token',
  loading: false,
  login: vi.fn(),
  logout: vi.fn(),
  refreshUser: vi.fn(),
  isAuthenticated: true,
  isCarrier: role === 'CARRIER',
  isWarehouse: role === 'WAREHOUSE_MANAGER' || role === 'WAREHOUSE_STAFF',
  isAdmin: role === 'ADMIN',
});

describe('App', () => {
  beforeEach(() => vi.clearAllMocks());

  it('returns to an authorized page if the user role changes while an admin page is active', () => {
    vi.mocked(useAuth).mockReturnValue(authValue('ADMIN'));
    const view = render(<App />);

    fireEvent.click(screen.getByRole('button', { name: 'Administration' }));
    expect(screen.getByText('Admin screen')).toBeTruthy();

    vi.mocked(useAuth).mockReturnValue(authValue('CARRIER'));
    view.rerender(<App />);

    expect(screen.getByText('Dashboard screen')).toBeTruthy();
    expect(screen.queryByText('Admin screen')).toBeNull();
    expect(screen.queryByRole('button', { name: 'Administration' })).toBeNull();
  });
});
