import React from 'react';
import { useAuth } from '../context/AuthContext';
import {
  Warehouse,
  LayoutDashboard,
  Truck,
  CalendarDays,
  Shield,
  LogOut,
  Clock,
  ClipboardList,
} from 'lucide-react';

export type ActiveTab = 'dashboard' | 'carrier' | 'warehouse' | 'admin';

interface NavigationProps {
  activeTab: ActiveTab;
  onSelectTab: (tab: ActiveTab) => void;
}

export const Navigation: React.FC<NavigationProps> = ({ activeTab, onSelectTab }) => {
  const { user, logout } = useAuth();

  if (!user) return null;

  const isCarrier = user.role === 'CARRIER';
  const isWarehouseUser = user.role === 'WAREHOUSE_MANAGER' || user.role === 'WAREHOUSE_STAFF';
  const isAdmin = user.role === 'ADMIN';

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div style={{
          width: '36px',
          height: '36px',
          borderRadius: '8px',
          background: '#0284c7',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#ffffff',
        }}>
          <Warehouse size={22} />
        </div>
        <div>
          <div className="logo-title">DockFlow</div>
          <div className="logo-sub">Scheduling MVP</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-section-title">Overview</div>
        <button
          className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => onSelectTab('dashboard')}
        >
          <LayoutDashboard size={18} />
          <span>Operational Dashboard</span>
        </button>

        {/* Carrier Portal */}
        {(isCarrier || isAdmin) && (
          <>
            <div className="nav-section-title">Carrier Operations</div>
            <button
              className={`nav-item ${activeTab === 'carrier' ? 'active' : ''}`}
              onClick={() => onSelectTab('carrier')}
            >
              <Truck size={18} />
              <span>Carrier Portal</span>
            </button>
          </>
        )}

        {/* Warehouse Portal */}
        {(isWarehouseUser || isAdmin) && (
          <>
            <div className="nav-section-title">Warehouse Operations</div>
            <button
              className={`nav-item ${activeTab === 'warehouse' ? 'active' : ''}`}
              onClick={() => onSelectTab('warehouse')}
            >
              <CalendarDays size={18} />
              <span>Warehouse Portal</span>
            </button>
          </>
        )}

        {/* Admin Portal */}
        {isAdmin && (
          <>
            <div className="nav-section-title">System Management</div>
            <button
              className={`nav-item ${activeTab === 'admin' ? 'active' : ''}`}
              onClick={() => onSelectTab('admin')}
            >
              <Shield size={18} />
              <span>Administration</span>
            </button>
          </>
        )}
      </nav>

      <div className="sidebar-footer">
        <div className="user-badge">
          <div className="user-avatar">
            {user.full_name?.charAt(0) || 'U'}
          </div>
          <div className="user-info">
            <div className="user-name">{user.full_name}</div>
            <div className="user-role-tag">
              {user.role.replace('_', ' ').toLowerCase()}
              {user.carrier && ` • ${user.carrier.company_name.split(' ')[0]}`}
            </div>
          </div>
        </div>

        <button
          className="btn btn-secondary btn-sm"
          style={{ width: '100%', justifyContent: 'center', backgroundColor: '#1e293b', borderColor: '#334155', color: '#e2e8f0' }}
          onClick={logout}
        >
          <LogOut size={14} />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
};
