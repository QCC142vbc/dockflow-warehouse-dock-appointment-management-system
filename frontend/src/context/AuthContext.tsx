import React, { createContext, useContext, useEffect, useState } from 'react';
import { User, Role } from '../types';
import api from '../services/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, pass: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  isAuthenticated: boolean;
  isCarrier: boolean;
  isWarehouse: boolean;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(api.getToken());
  const [loading, setLoading] = useState<boolean>(true);

  const refreshUser = async () => {
    try {
      if (api.getToken()) {
        const u = await api.getMe();
        setUser(u);
      } else {
        setUser(null);
      }
    } catch {
      setUser(null);
      api.setToken(null);
      setToken(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshUser();

    const handleUnauthorized = () => {
      setUser(null);
      setToken(null);
    };

    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized);
  }, []);

  const login = async (email: string, pass: string) => {
    setLoading(true);
    try {
      const res = await api.login(email, pass);
      setToken(res.access_token);
      setUser(res.user);
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    await api.logout();
    setToken(null);
    setUser(null);
  };

  const isCarrier = user?.role === Role.CARRIER_ADMIN || user?.role === Role.CARRIER_DISPATCHER;
  const isWarehouse = user?.role === Role.WAREHOUSE_ADMIN || 
                     user?.role === Role.WAREHOUSE_DISPATCHER || 
                     user?.role === Role.WAREHOUSE_OPERATOR;
  const isAdmin = user?.role === Role.SYSTEM_ADMIN;

  return (
    <AuthContext.Provider value={{ 
      user, 
      token, 
      loading, 
      login, 
      logout, 
      refreshUser,
      isAuthenticated: !!user,
      isCarrier,
      isWarehouse,
      isAdmin,
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};
