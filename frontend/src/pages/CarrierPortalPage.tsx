import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { Appointment, AppointmentStatus, Warehouse } from '../types';
import {
  Calendar,
  CheckCircle2,
  Clock,
  Edit2,
  Eye,
  FileText,
  Plus,
  RefreshCw,
  Search,
  Send,
  Truck,
  XCircle,
} from 'lucide-react';

interface CarrierPortalPageProps {
  onOpenAppointment: (appt: Appointment) => void;
  onEditAppointment: (appt: Appointment) => void;
  onOpenNewModal: () => void;
  onOpenStatusModal: (appt: Appointment, status: AppointmentStatus) => void;
}

export const CarrierPortalPage: React.FC<CarrierPortalPageProps> = ({
  onOpenAppointment,
  onEditAppointment,
  onOpenNewModal,
  onOpenStatusModal,
}) => {
  const { user } = useAuth();
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [selectedWarehouseId, setSelectedWarehouseId] = useState<number | ''>('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadAppointments = async () => {
    setLoading(true);
    setError(null);
    try {
      const [whList, apptList] = await Promise.all([
        api.getWarehouses(),
        api.getAppointments({
          warehouse_id: selectedWarehouseId ? Number(selectedWarehouseId) : undefined,
          appointment_status: statusFilter !== 'ALL' ? (statusFilter as AppointmentStatus) : undefined,
        }),
      ]);
      setWarehouses(whList);
      setAppointments(apptList);
    } catch (err: any) {
      setError(err.message || 'Failed to load carrier appointments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAppointments();
  }, [selectedWarehouseId, statusFilter]);

  const filteredAppointments = appointments.filter((a) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      a.reference_number.toLowerCase().includes(term) ||
      a.vehicle_registration.toLowerCase().includes(term) ||
      (a.cargo_type && a.cargo_type.toLowerCase().includes(term))
    );
  });

  return (
    <div>
      {/* Carrier Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h2 style={{ fontSize: '1.35rem', fontWeight: 700 }}>Carrier Booking Portal</h2>
            {user?.carrier && (
              <span style={{ fontSize: '0.8rem', background: '#e0f2fe', color: '#0369a1', padding: '3px 10px', borderRadius: '12px', fontWeight: 600 }}>
                {user.carrier.company_name}
              </span>
            )}
          </div>
          <p style={{ fontSize: '0.84rem', color: '#64748b' }}>
            Schedule dock slots, submit freight details, track confirmation progress, and manage vehicle check-ins
          </p>
        </div>

        <button className="btn btn-primary" onClick={onOpenNewModal}>
          <Plus size={16} />
          <span>Request Appointment</span>
        </button>
      </div>

      {error && (
        <div className="alert alert-danger" style={{ marginBottom: '20px' }}>
          <span>{error}</span>
        </div>
      )}

      {/* Control Filters Bar */}
      <div className="card" style={{ padding: '16px', marginBottom: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
          {/* Search */}
          <div style={{ position: 'relative', width: '260px' }}>
            <input
              type="text"
              className="form-input"
              placeholder="Search ref #, plate..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{ paddingLeft: '32px' }}
            />
            <Search size={15} style={{ position: 'absolute', left: '10px', top: '10px', color: '#94a3b8' }} />
          </div>

          {/* Warehouse */}
          <div style={{ width: '220px' }}>
            <select
              className="form-select"
              value={selectedWarehouseId}
              onChange={(e) => setSelectedWarehouseId(e.target.value ? Number(e.target.value) : '')}
            >
              <option value="">All Warehouses</option>
              {warehouses.map((w) => (
                <option key={w.id} value={w.id}>
                  {w.name} ({w.code})
                </option>
              ))}
            </select>
          </div>

          {/* Status Tabs */}
          <div style={{ width: '180px' }}>
            <select
              className="form-select"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="ALL">All Statuses</option>
              <option value="PENDING">Pending Review</option>
              <option value="CONFIRMED">Confirmed</option>
              <option value="CHECKED_IN">Checked-In</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="COMPLETED">Completed</option>
              <option value="DRAFT">Drafts</option>
              <option value="REJECTED">Rejected</option>
              <option value="CANCELLED">Cancelled</option>
            </select>
          </div>

          <button className="btn btn-secondary btn-sm" onClick={loadAppointments} disabled={loading} style={{ marginLeft: 'auto' }}>
            <RefreshCw size={14} className={loading ? 'spin' : ''} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Appointments Data Table */}
      <div className="card">
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Reference</th>
                <th>Status</th>
                <th>Destination Hub</th>
                <th>Assigned Bay</th>
                <th>Vehicle / Plate</th>
                <th>Cargo / Weight</th>
                <th>Scheduled Slot</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={8} style={{ textAlign: 'center', padding: '30px', color: '#64748b' }}>
                    Loading appointments...
                  </td>
                </tr>
              ) : filteredAppointments.length === 0 ? (
                <tr>
                  <td colSpan={8} style={{ textAlign: 'center', padding: '40px', color: '#94a3b8' }}>
                    <div style={{ marginBottom: '8px' }}><Truck size={32} color="#cbd5e1" /></div>
                    No appointments found matching current filters.
                  </td>
                </tr>
              ) : (
                filteredAppointments.map((a) => {
                  const isDraft = a.status === 'DRAFT';
                  const isPending = a.status === 'PENDING';
                  const canCancel = ['DRAFT', 'PENDING', 'CONFIRMED'].includes(a.status);
                  const canEdit = ['DRAFT', 'PENDING'].includes(a.status);

                  return (
                    <tr key={a.id}>
                      <td>
                        <span style={{ fontWeight: 600, color: '#0284c7' }}>{a.reference_number}</span>
                      </td>
                      <td>
                        <span className={`status-badge badge-${a.status.toLowerCase()}`}>{a.status}</span>
                        {a.rejection_reason && (
                          <div style={{ fontSize: '0.72rem', color: '#ef4444', marginTop: '2px', maxWidth: '180px' }}>
                            {a.rejection_reason}
                          </div>
                        )}
                      </td>
                      <td>{a.warehouse_name || `Warehouse #${a.warehouse_id}`}</td>
                      <td>
                        {a.dock_code ? (
                          <span style={{ fontWeight: 600, color: '#0f172a' }}>{a.dock_code}</span>
                        ) : (
                          <span style={{ color: '#94a3b8', fontStyle: 'italic' }}>Pending Assign</span>
                        )}
                      </td>
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
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <button
                            className="btn btn-secondary btn-sm"
                            title="Inspect Details"
                            onClick={() => onOpenAppointment(a)}
                          >
                            <Eye size={13} />
                          </button>

                          {isDraft && (
                            <button
                              className="btn btn-primary btn-sm"
                              title="Submit Draft as Pending"
                              onClick={() => onOpenStatusModal(a, 'PENDING')}
                            >
                              <Send size={13} />
                              <span>Submit</span>
                            </button>
                          )}

                          {canEdit && (
                            <button
                              className="btn btn-secondary btn-sm"
                              title="Edit Appointment"
                              onClick={() => onEditAppointment(a)}
                            >
                              <Edit2 size={13} />
                            </button>
                          )}

                          {canCancel && (
                            <button
                              className="btn btn-danger btn-sm"
                              title="Cancel Request"
                              onClick={() => onOpenStatusModal(a, 'CANCELLED')}
                            >
                              <XCircle size={13} />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
