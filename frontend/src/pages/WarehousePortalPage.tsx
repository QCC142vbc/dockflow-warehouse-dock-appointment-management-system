import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import {
  Appointment,
  AppointmentStatus,
  Dock,
  DockUnavailability,
  Warehouse,
} from '../types';
import {
  AlertTriangle,
  Calendar,
  CheckCircle2,
  Clock,
  Eye,
  Plus,
  RefreshCw,
  Sliders,
  Trash2,
  Truck,
  Warehouse as WarehouseIcon,
  Wrench,
  XCircle,
} from 'lucide-react';

interface WarehousePortalPageProps {
  onOpenAppointment: (appt: Appointment) => void;
  onOpenStatusModal: (appt: Appointment, status: AppointmentStatus) => void;
}

export const WarehousePortalPage: React.FC<WarehousePortalPageProps> = ({
  onOpenAppointment,
  onOpenStatusModal,
}) => {
  const { user } = useAuth();
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [selectedWarehouseId, setSelectedWarehouseId] = useState<number | ''>('');
  const [activeSubTab, setActiveSubTab] = useState<'schedule' | 'approvals' | 'docks' | 'operations'>('schedule');

  // Data
  const [docks, setDocks] = useState<Dock[]>([]);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [unavailabilities, setUnavailabilities] = useState<DockUnavailability[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>(new Date().toISOString().split('T')[0]);

  // Loading & Error
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // New Maintenance Form State
  const [showMaintModal, setShowMaintModal] = useState(false);
  const [maintDockId, setMaintDockId] = useState<number | ''>('');
  const [maintReason, setMaintReason] = useState('MAINTENANCE');
  const [maintDesc, setMaintDesc] = useState('');
  const [maintStart, setMaintStart] = useState('');
  const [maintEnd, setMaintEnd] = useState('');

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const whList = await api.getWarehouses();
      setWarehouses(whList);

      let whId = selectedWarehouseId;
      if (!whId && whList.length > 0) {
        whId = whList[0].id;
        setSelectedWarehouseId(whId);
      }

      if (whId) {
        const [dockList, apptList, unavailList] = await Promise.all([
          api.getDocks(Number(whId)),
          api.getAppointments({ warehouse_id: Number(whId) }),
          api.getDockUnavailability(),
        ]);
        setDocks(dockList);
        setAppointments(apptList);
        setUnavailabilities(unavailList);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load warehouse data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedWarehouseId]);

  const handleCreateMaintenance = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!maintDockId || !maintStart || !maintEnd) return;

    try {
      await api.createDockUnavailability({
        dock_id: Number(maintDockId),
        reason_type: maintReason,
        description: maintDesc,
        start_time: new Date(maintStart).toISOString(),
        end_time: new Date(maintEnd).toISOString(),
      });
      setShowMaintModal(false);
      setMaintDesc('');
      loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to register maintenance');
    }
  };

  const handleDeleteMaintenance = async (id: number) => {
    if (!confirm('Are you sure you want to remove this maintenance period?')) return;
    try {
      await api.deleteDockUnavailability(id);
      loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to delete maintenance');
    }
  };

  const pendingAppointments = appointments.filter((a) => a.status === 'PENDING');
  const activeOperationalAppointments = appointments.filter((a) =>
    ['CONFIRMED', 'CHECKED_IN', 'ARRIVED', 'IN_PROGRESS'].includes(a.status)
  );

  // Schedule filtering by selectedDate
  const scheduleAppointments = appointments.filter((a) => {
    return a.scheduled_start.startsWith(selectedDate);
  });

  return (
    <div>
      {/* Header with Warehouse Selection */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <div>
          <h2 style={{ fontSize: '1.35rem', fontWeight: 700 }}>Warehouse Operations Portal</h2>
          <p style={{ fontSize: '0.84rem', color: '#64748b' }}>
            Daily dock schedule, appointment reviews, bay assignments, maintenance & live floor dispatch
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <select
            className="form-select"
            value={selectedWarehouseId}
            onChange={(e) => setSelectedWarehouseId(Number(e.target.value))}
            style={{ width: '260px' }}
          >
            {warehouses.map((w) => (
              <option key={w.id} value={w.id}>
                {w.name} ({w.code})
              </option>
            ))}
          </select>

          <button className="btn btn-secondary btn-sm" onClick={loadData} disabled={loading}>
            <RefreshCw size={14} className={loading ? 'spin' : ''} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="alert alert-danger" style={{ marginBottom: '20px' }}>
          <span>{error}</span>
        </div>
      )}

      {/* Sub Navigation Tabs */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid #e2e8f0', marginBottom: '20px', paddingBottom: '2px' }}>
        <button
          className={`btn btn-sm ${activeSubTab === 'schedule' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveSubTab('schedule')}
        >
          <Calendar size={14} />
          <span>Dock Schedule Matrix</span>
        </button>

        <button
          className={`btn btn-sm ${activeSubTab === 'approvals' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveSubTab('approvals')}
          style={{ position: 'relative' }}
        >
          <Clock size={14} />
          <span>Pending Approvals</span>
          {pendingAppointments.length > 0 && (
            <span style={{
              marginLeft: '6px',
              background: '#ef4444',
              color: '#ffffff',
              borderRadius: '9999px',
              padding: '1px 6px',
              fontSize: '0.7rem',
              fontWeight: 700,
            }}>
              {pendingAppointments.length}
            </span>
          )}
        </button>

        <button
          className={`btn btn-sm ${activeSubTab === 'operations' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveSubTab('operations')}
        >
          <Truck size={14} />
          <span>Live Operations</span>
        </button>

        <button
          className={`btn btn-sm ${activeSubTab === 'docks' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveSubTab('docks')}
        >
          <Wrench size={14} />
          <span>Docks & Maintenance</span>
        </button>
      </div>

      {/* TAB 1: SCHEDULE MATRIX */}
      {activeSubTab === 'schedule' && (
        <div>
          <div className="card" style={{ padding: '14px', marginBottom: '18px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <label className="form-label" style={{ margin: 0 }}>Schedule Date:</label>
                <input
                  type="date"
                  className="form-input"
                  value={selectedDate}
                  onChange={(e) => setSelectedDate(e.target.value)}
                  style={{ width: '160px' }}
                />
              </div>

              <div style={{ display: 'flex', gap: '16px', fontSize: '0.78rem', color: '#64748b' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ width: '12px', height: '12px', background: '#dbeafe', borderRadius: '3px' }} /> Confirmed / In Progress
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ width: '12px', height: '12px', background: '#fee2e2', borderRadius: '3px' }} /> Maintenance Closure
                </span>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-title">
              <span>Dock Allocation Timeline for {selectedDate}</span>
            </div>

            {docks.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '30px', color: '#94a3b8' }}>No docks registered for this warehouse.</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {docks.map((dock) => {
                  const dockAppointments = scheduleAppointments.filter((a) => a.dock_id === dock.id);
                  const dockUnavails = unavailabilities.filter((u) => u.dock_id === dock.id);

                  return (
                    <div
                      key={dock.id}
                      style={{
                        border: '1px solid #e2e8f0',
                        borderRadius: '8px',
                        padding: '14px',
                        background: dock.is_active ? '#ffffff' : '#f8fafc',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                        <div>
                          <span style={{ fontWeight: 700, color: '#0284c7' }}>{dock.dock_code}</span>
                          <span style={{ marginLeft: '8px', fontWeight: 600, color: '#0f172a' }}>{dock.name}</span>
                          {!dock.is_active && (
                            <span style={{ marginLeft: '8px', fontSize: '0.72rem', color: '#ef4444', fontWeight: 600 }}>INACTIVE</span>
                          )}
                        </div>
                        <div style={{ fontSize: '0.76rem', color: '#64748b' }}>
                          Capacity: {dock.max_vehicle_length ? `${dock.max_vehicle_length}m` : 'Any'} • {dock.max_vehicle_weight ? `${dock.max_vehicle_weight.toLocaleString()} kg` : 'Any'}
                        </div>
                      </div>

                      {/* Visual Blocks on Dock */}
                      {dockAppointments.length === 0 && dockUnavails.length === 0 ? (
                        <div style={{ fontSize: '0.82rem', color: '#94a3b8', fontStyle: 'italic', padding: '8px 0' }}>
                          No appointments or maintenance scheduled for this dock today.
                        </div>
                      ) : (
                        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                          {dockAppointments.map((appt) => {
                            const startStr = new Date(appt.scheduled_start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                            const endStr = new Date(appt.scheduled_end).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

                            return (
                              <div
                                key={appt.id}
                                onClick={() => onOpenAppointment(appt)}
                                style={{
                                  background: '#dbeafe',
                                  border: '1px solid #bfdbfe',
                                  borderRadius: '6px',
                                  padding: '8px 12px',
                                  cursor: 'pointer',
                                  minWidth: '200px',
                                }}
                              >
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', fontWeight: 600, color: '#1e40af' }}>
                                  <span>{startStr} – {endStr}</span>
                                  <span className={`status-badge badge-${appt.status.toLowerCase()}`}>{appt.status}</span>
                                </div>
                                <div style={{ fontSize: '0.82rem', fontWeight: 600, color: '#0f172a', marginTop: '4px' }}>
                                  {appt.reference_number}
                                </div>
                                <div style={{ fontSize: '0.75rem', color: '#475569' }}>
                                  {appt.carrier_name || `Carrier #${appt.carrier_id}`} • {appt.vehicle_registration}
                                </div>
                              </div>
                            );
                          })}

                          {dockUnavails.map((unavail) => (
                            <div
                              key={unavail.id}
                              style={{
                                background: '#fee2e2',
                                border: '1px solid #fecaca',
                                borderRadius: '6px',
                                padding: '8px 12px',
                                minWidth: '180px',
                              }}
                            >
                              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#991b1b', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                <Wrench size={12} />
                                <span>{unavail.reason_type}</span>
                              </div>
                              <div style={{ fontSize: '0.78rem', color: '#7f1d1d', marginTop: '2px' }}>
                                {unavail.description || 'Closure Window'}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: APPROVAL QUEUE */}
      {activeSubTab === 'approvals' && (
        <div className="card">
          <div className="card-title">
            <span>Pending Appointment Requests Awaiting Warehouse Review</span>
          </div>

          {pendingAppointments.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#94a3b8' }}>
              <CheckCircle2 size={36} color="#10b981" style={{ marginBottom: '8px' }} />
              <div>All appointment requests have been processed! No pending items in queue.</div>
            </div>
          ) : (
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Reference</th>
                    <th>Carrier</th>
                    <th>Vehicle Plate</th>
                    <th>Cargo / Gross Weight</th>
                    <th>Requested Slot</th>
                    <th>Allocated Dock</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {pendingAppointments.map((a) => (
                    <tr key={a.id}>
                      <td>
                        <span style={{ fontWeight: 600, color: '#0284c7' }}>{a.reference_number}</span>
                      </td>
                      <td>{a.carrier_name || `Carrier #${a.carrier_id}`}</td>
                      <td>
                        <span style={{ fontFamily: 'var(--font-mono)' }}>{a.vehicle_registration}</span>
                        <div style={{ fontSize: '0.74rem', color: '#64748b' }}>{a.vehicle_type}</div>
                      </td>
                      <td>
                        {a.cargo_type}
                        {a.cargo_weight_kg && (
                          <div style={{ fontSize: '0.74rem', color: '#64748b' }}>
                            {a.cargo_weight_kg.toLocaleString()} kg
                          </div>
                        )}
                      </td>
                      <td>
                        {new Date(a.scheduled_start).toLocaleDateString([], { month: 'short', day: 'numeric' })}{' '}
                        {new Date(a.scheduled_start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </td>
                      <td>
                        {a.dock_code ? (
                          <span style={{ fontWeight: 600, color: '#0f172a' }}>{a.dock_code}</span>
                        ) : (
                          <span style={{ color: '#d97706', fontWeight: 500, fontSize: '0.8rem' }}>Needs Dock</span>
                        )}
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: '6px' }}>
                          <button
                            className="btn btn-secondary btn-sm"
                            title="Inspect details"
                            onClick={() => onOpenAppointment(a)}
                          >
                            <Eye size={13} />
                          </button>
                          <button
                            className="btn btn-primary btn-sm"
                            onClick={() => onOpenStatusModal(a, 'CONFIRMED')}
                          >
                            <CheckCircle2 size={13} />
                            <span>Confirm Bay</span>
                          </button>
                          <button
                            className="btn btn-danger btn-sm"
                            onClick={() => onOpenStatusModal(a, 'REJECTED')}
                          >
                            <XCircle size={13} />
                            <span>Reject</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* TAB 3: LIVE OPERATIONS */}
      {activeSubTab === 'operations' && (
        <div className="card">
          <div className="card-title">
            <span>On-Site Loading / Unloading Live Floor Workflow</span>
          </div>

          {activeOperationalAppointments.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '30px', color: '#94a3b8' }}>
              No active vehicle operations currently on-site.
            </div>
          ) : (
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Reference</th>
                    <th>Status</th>
                    <th>Dock Bay</th>
                    <th>Carrier / Plate</th>
                    <th>Scheduled Slot</th>
                    <th>Workflow Action</th>
                  </tr>
                </thead>
                <tbody>
                  {activeOperationalAppointments.map((a) => (
                    <tr key={a.id}>
                      <td>
                        <span style={{ fontWeight: 600, color: '#0284c7' }}>{a.reference_number}</span>
                      </td>
                      <td>
                        <span className={`status-badge badge-${a.status.toLowerCase()}`}>{a.status}</span>
                      </td>
                      <td>
                        <span style={{ fontWeight: 700, color: '#0f172a' }}>{a.dock_code || 'Unassigned'}</span>
                      </td>
                      <td>
                        <div>{a.carrier_name}</div>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem' }}>{a.vehicle_registration}</span>
                      </td>
                      <td>
                        {new Date(a.scheduled_start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} –{' '}
                        {new Date(a.scheduled_end).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: '6px' }}>
                          {a.status === 'CONFIRMED' && (
                            <>
                              <button
                                className="btn btn-primary btn-sm"
                                onClick={() => onOpenStatusModal(a, 'CHECKED_IN')}
                              >
                                Check In (Gate)
                              </button>
                              <button
                                className="btn btn-secondary btn-sm"
                                onClick={() => onOpenStatusModal(a, 'NO_SHOW')}
                              >
                                No-Show
                              </button>
                            </>
                          )}

                          {a.status === 'CHECKED_IN' && (
                            <button
                              className="btn btn-primary btn-sm"
                              onClick={() => onOpenStatusModal(a, 'ARRIVED')}
                            >
                              Arrived at Dock
                            </button>
                          )}

                          {a.status === 'ARRIVED' && (
                            <button
                              className="btn btn-primary btn-sm"
                              onClick={() => onOpenStatusModal(a, 'IN_PROGRESS')}
                            >
                              Start Loading
                            </button>
                          )}

                          {a.status === 'IN_PROGRESS' && (
                            <button
                              className="btn btn-primary btn-sm"
                              style={{ backgroundColor: '#10b981' }}
                              onClick={() => onOpenStatusModal(a, 'COMPLETED')}
                            >
                              Complete & Release
                            </button>
                          )}

                          <button
                            className="btn btn-secondary btn-sm"
                            onClick={() => onOpenAppointment(a)}
                          >
                            <Eye size={13} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* TAB 4: DOCKS & MAINTENANCE */}
      {activeSubTab === 'docks' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '16px' }}>
            <button className="btn btn-primary btn-sm" onClick={() => setShowMaintModal(true)}>
              <Plus size={14} />
              <span>Register Maintenance Window</span>
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>
            {/* Docks List */}
            <div className="card">
              <div className="card-title">
                <span>Dock Bays in Warehouse</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {docks.map((dock) => (
                  <div
                    key={dock.id}
                    style={{
                      border: '1px solid #e2e8f0',
                      borderRadius: '8px',
                      padding: '14px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                    }}
                  >
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontWeight: 700, color: '#0284c7' }}>{dock.dock_code}</span>
                        <span style={{ fontWeight: 600 }}>{dock.name}</span>
                        <span style={{
                          fontSize: '0.7rem',
                          padding: '2px 8px',
                          borderRadius: '10px',
                          fontWeight: 600,
                          background: dock.is_active ? '#dcfce7' : '#fee2e2',
                          color: dock.is_active ? '#166534' : '#991b1b',
                        }}>
                          {dock.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                      <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '4px' }}>
                        {dock.description || 'Standard facility bay'}
                      </div>
                      <div style={{ fontSize: '0.76rem', color: '#475569', marginTop: '4px' }}>
                        Max Vehicle Length: {dock.max_vehicle_length ? `${dock.max_vehicle_length} m` : 'Unrestricted'} • Max Weight: {dock.max_vehicle_weight ? `${dock.max_vehicle_weight.toLocaleString()} kg` : 'Unrestricted'}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Scheduled Maintenance Periods */}
            <div className="card">
              <div className="card-title">
                <span>Registered Unavailability Periods</span>
              </div>
              {unavailabilities.length === 0 ? (
                <div style={{ fontSize: '0.84rem', color: '#94a3b8', fontStyle: 'italic' }}>
                  No maintenance closures scheduled.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {unavailabilities.map((u) => {
                    const dock = docks.find((d) => d.id === u.dock_id);
                    return (
                      <div
                        key={u.id}
                        style={{
                          border: '1px solid #fecaca',
                          background: '#fff5f5',
                          borderRadius: '6px',
                          padding: '10px 12px',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#991b1b' }}>
                            {dock ? dock.dock_code : `Dock #${u.dock_id}`} — {u.reason_type}
                          </span>
                          <button
                            className="btn btn-secondary btn-sm"
                            style={{ padding: '2px 6px', color: '#ef4444' }}
                            title="Delete Maintenance Window"
                            onClick={() => handleDeleteMaintenance(u.id)}
                          >
                            <Trash2 size={12} />
                          </button>
                        </div>
                        <div style={{ fontSize: '0.78rem', color: '#475569', marginTop: '4px' }}>
                          {new Date(u.start_time).toLocaleString()} to {new Date(u.end_time).toLocaleString()}
                        </div>
                        {u.description && (
                          <div style={{ fontSize: '0.74rem', color: '#7f1d1d', marginTop: '2px' }}>
                            {u.description}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Register Maintenance Modal */}
      {showMaintModal && (
        <div className="modal-backdrop">
          <div className="modal-content" style={{ maxWidth: '480px' }}>
            <div className="modal-header">
              <h3>Register Dock Maintenance Closure</h3>
              <button className="btn btn-secondary btn-sm" onClick={() => setShowMaintModal(false)}>
                <XCircle size={16} />
              </button>
            </div>

            <form onSubmit={handleCreateMaintenance}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Dock Bay *</label>
                  <select
                    className="form-select"
                    value={maintDockId}
                    onChange={(e) => setMaintDockId(Number(e.target.value))}
                    required
                  >
                    <option value="">Select Dock</option>
                    {docks.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.dock_code} — {d.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Reason Type *</label>
                  <select
                    className="form-select"
                    value={maintReason}
                    onChange={(e) => setMaintReason(e.target.value)}
                  >
                    <option value="MAINTENANCE">Scheduled Maintenance</option>
                    <option value="REPAIR">Emergency Repair</option>
                    <option value="INSPECTION">Safety / Calibration Inspection</option>
                    <option value="CLOSURE">Operational Closure</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Start Time *</label>
                  <input
                    type="datetime-local"
                    className="form-input"
                    value={maintStart}
                    onChange={(e) => setMaintStart(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">End Time *</label>
                  <input
                    type="datetime-local"
                    className="form-input"
                    value={maintEnd}
                    onChange={(e) => setMaintEnd(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Description / Work Order</label>
                  <textarea
                    className="form-textarea"
                    rows={2}
                    placeholder="Details about maintenance crew or tasks..."
                    value={maintDesc}
                    onChange={(e) => setMaintDesc(e.target.value)}
                  />
                </div>
              </div>

              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowMaintModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Save Closure Window
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
