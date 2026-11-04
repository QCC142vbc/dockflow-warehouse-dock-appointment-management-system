import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AuthProvider, useAuth } from '../src/context/AuthContext';
import { api } from '../src/services/api';

vi.mock('../src/services/api', () => ({
  api: {
    getToken: vi.fn(),
    setToken: vi.fn(),
    getMe: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
  },
}));

function AuthProbe() {
  const { user, loading, login, logout } = useAuth();
  return (
    <div>
      <span>{loading ? 'loading' : user?.role ?? 'signed out'}</span>
      <button onClick={() => login('carrier@example.test', 'password')}>Sign in</button>
      <button onClick={logout}>Sign out</button>
    </div>
  );
}

describe('AuthProvider', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.getToken).mockReturnValue(null);
    vi.mocked(api.login).mockImplementation(async () => {
      api.setToken('signed-in-token');
      return {
      access_token: 'signed-in-token',
      token_type: 'bearer',
      user: {
        id: 2,
        email: 'carrier@example.test',
        full_name: 'Carrier User',
        role: 'CARRIER',
        is_active: true,
      },
      };
    });
  });

  it('logs in, stores the token, and clears auth state on logout', async () => {
    render(
      <AuthProvider>
        <AuthProbe />
      </AuthProvider>,
    );

    await screen.findByText('signed out');
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }));

    await screen.findByText('CARRIER');
    expect(api.setToken).toHaveBeenCalledWith('signed-in-token');

    fireEvent.click(screen.getByRole('button', { name: 'Sign out' }));
    await waitFor(() => expect(screen.getByText('signed out')).toBeTruthy());
    expect(api.logout).toHaveBeenCalledOnce();
  });
});
