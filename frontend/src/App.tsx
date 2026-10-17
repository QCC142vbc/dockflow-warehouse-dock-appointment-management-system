import React, { useState } from 'react';
import { useAuth } from './context/AuthContext';
import { LoginPage } from './pages/LoginPage';
import { Navigation, ActiveTab } from './components/Navigation';
import { DashboardPage } from './pages/DashboardPage';
import { CarrierPortalPage } from './pages/CarrierPortalPage';
import { WarehousePortalPage } from './pages/WarehousePortalPage';
import { AdminPortalPage } from './pages/AdminPortalPage';
import { AppointmentModal } from './components/AppointmentModal';
import { StatusTransitionModal } from './components/StatusTransitionModal';
import { AppointmentDetailModal } from './components/AppointmentDetailModal';
import { Appointment, AppointmentStatus } from './types';
import { Warehouse as WarehouseIcon, Plus, Bell } from 'lucide-react';

export const App: React.FC = () => {
  const { user, loading } = useAuth();
  const [activeTab, setActiveTab] = useState<ActiveTab>('dashboard');

  // Modals state
  const [isAppointmentModalOpen, setIsAppointmentModalOpen] = useState(false);
  const [appointmentToEdit, setAppointmentToEdit] = useState<Appointment | null>(null);

  const [detailAppointment, setDetailAppointment] = useState<Appointment | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);

  const [statusModalAppointment, setStatusModalAppointment] = useState<Appointment | null>(null);
  const [targetStatus, setTargetStatus] = useState<AppointmentStatus>('CONFIRMED');
  const [isStatusModalOpen, setIsStatusModalOpen] = useState(false);

  // Global trigger to refresh current view after modal mutations
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  if (loading) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#0f172a',
        color: '#ffffff',
        fontFamily: 'var(--font-sans)',
      }}>
        <div style={{ textAlign: 'center' }}>
          <WarehouseIcon size={40} color="#0284c7" style={{ marginBottom: '12px' }} />
          <div style={{ fontSize: '1rem', fontWeight: 600 }}>Initializing DockFlow System...</div>
        </div>
      </div>
    );
  }

  if (!user) {
    return <LoginPage />;
  }

  const handleOpenAppointmentDetail = (appt: Appointment) => {
    setDetailAppointment(appt);
    setIsDetailModalOpen(true);
  };

  const handleOpenEdit = (appt: Appointment) => {
    setAppointmentToEdit(appt);
    setIsAppointmentModalOpen(true);
  };

  const handleOpenNewAppointment = () => {
    setAppointmentToEdit(null);
    setIsAppointmentModalOpen(true);
  };

  const handleOpenStatusModal = (appt: Appointment, status: AppointmentStatus) => {
    setStatusModalAppointment(appt);
    setTargetStatus(status);
    setIsStatusModalOpen(true);
  };

  const handleSuccess = () => {
    setRefreshTrigger((prev) => prev + 1);
  };

  const pageTitles: Record<ActiveTab, string> = {
    dashboard: 'Operational Overview & KPIs',
    carrier: 'Carrier Portal — Freight Booking & Tracking',
    warehouse: 'Warehouse Portal — Schedules & Bay Allocations',
    admin: 'System Administration & Security Control',
  };

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <Navigation activeTab={activeTab} onSelectTab={setActiveTab} />

      {/* Main Content Area */}
      <div className="main-wrapper">
        <header className="top-bar">
          <div className="top-bar-title">{pageTitles[activeTab]}</div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            {(user.role === 'CARRIER' || user.role === 'ADMIN') && (
              <button className="btn btn-primary btn-sm" onClick={handleOpenNewAppointment}>
                <Plus size={14} />
                <span>Request Appointment</span>
              </button>
            )}

            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 10px',
              background: '#f1f5f9',
              borderRadius: '6px',
              fontSize: '0.8rem',
              color: '#475569',
            }}>
              <span style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: '#16a34a',
              }} />
              <span>Backend Connected (UTC Mode)</span>
            </div>
          </div>
        </header>

        <main className="content-body" key={refreshTrigger}>
          {activeTab === 'dashboard' && (
            <DashboardPage onOpenAppointment={handleOpenAppointmentDetail} />
          )}

          {activeTab === 'carrier' && (
            <CarrierPortalPage
              onOpenAppointment={handleOpenAppointmentDetail}
              onEditAppointment={handleOpenEdit}
              onOpenNewModal={handleOpenNewAppointment}
              onOpenStatusModal={handleOpenStatusModal}
            />
          )}

          {activeTab === 'warehouse' && (
            <WarehousePortalPage
              onOpenAppointment={handleOpenAppointmentDetail}
              onOpenStatusModal={handleOpenStatusModal}
            />
          )}

          {activeTab === 'admin' && (
            <AdminPortalPage />
          )}
        </main>
      </div>

      {/* Appointment Create/Edit Modal */}
      <AppointmentModal
        isOpen={isAppointmentModalOpen}
        onClose={() => setIsAppointmentModalOpen(false)}
        onSuccess={handleSuccess}
        initialAppointment={appointmentToEdit}
      />

      {/* Status Transition Modal */}
      <StatusTransitionModal
        isOpen={isStatusModalOpen}
        onClose={() => setIsStatusModalOpen(false)}
        onSuccess={handleSuccess}
        appointment={statusModalAppointment}
        targetStatus={targetStatus}
      />

      {/* Appointment Detailed Inspector Modal */}
      <AppointmentDetailModal
        isOpen={isDetailModalOpen}
        onClose={() => setIsDetailModalOpen(false)}
        appointment={detailAppointment}
      />
    </div>
  );
};
