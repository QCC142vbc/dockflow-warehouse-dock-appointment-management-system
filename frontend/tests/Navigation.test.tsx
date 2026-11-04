import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { Navigation } from '../src/components/Navigation';
import { useAuth } from '../src/context/AuthContext';
import { UserRole } from '../src/types';

vi.mock('../src/context/AuthContext', () => ({
  useAuth: vi.fn(),
}));

const makeUser = (role: UserRole) => ({
  id: 1,
  email: 'user@example.test',
  full_name: 'Test User',
  role,
  is_active: true,
});

const renderNavigation = (role: UserRole) => {
  const onSelectTab = vi.fn();
  vi.mocked(useAuth).mockReturnValue({
    user: makeUser(role),
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

  render(<Navigation activeTab="dashboard" onSelectTab={onSelectTab} />);
  return onSelectTab;
};

describe('role-based navigation', () => {
  beforeEach(() => vi.clearAllMocks());

  it('limits carrier navigation to the dashboard and carrier portal', () => {
    const onSelectTab = renderNavigation('CARRIER');

    expect(screen.getByRole('button', { name: 'Carrier Portal' })).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Warehouse Portal' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Administration' })).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: 'Carrier Portal' }));
    expect(onSelectTab).toHaveBeenCalledWith('carrier');
  });

  it('limits warehouse staff to the warehouse portal and dashboard', () => {
    renderNavigation('WAREHOUSE_STAFF');

    expect(screen.getByRole('button', { name: 'Warehouse Portal' })).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Carrier Portal' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Administration' })).toBeNull();
  });

  it('shows all operational portals to administrators', () => {
    renderNavigation('ADMIN');

    expect(screen.getByRole('button', { name: 'Carrier Portal' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Warehouse Portal' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Administration' })).toBeTruthy();
  });
});
