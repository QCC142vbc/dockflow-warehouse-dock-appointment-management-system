import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Appointment, AppointmentStatus, Dock } from '../types';
import { CheckCircle2, ShieldAlert, X } from 'lucide-react';

interface StatusTransitionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  appointment: Appointment | null;
  targetStatus: AppointmentStatus;
}

export const StatusTransitionModal: React.FC<StatusTransitionModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  appointment,
  targetStatus,
}) => {
  const [reason, setReason] = useState('');
  const [dockId, setDockId] = useState<number | ''>('');
  const [docks, setDocks] = useState<Dock[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isOpen || !appointment) return;

    setReason('');
    setDockId(appointment.dock_id || '');
    setError(null);

    if (targetStatus === 'CONFIRMED') {
      api.getDocks(appointment.warehouse_id).then((allDocks) => {
        setDocks(allDocks.filter((d) => d.is_active));
        if (!appointment.dock_id && allDocks.length > 0) {
          const firstActive = allDocks.find((d) => d.is_active);
          if (firstActive) setDockId(firstActive.id);
        }
      });
    }
  }, [isOpen, appointment, targetStatus]);

  if (!isOpen || !appointment) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (targetStatus === 'CONFIRMED' && !dockId) {
      setError('A dock must be assigned before confirming the appointment.');
      return;
    }

    if (targetStatus === 'REJECTED' && !reason.trim()) {
      setError('Please provide a rejection reason for the carrier.');
      return;
    }

    setLoading(true);
    try {
      await api.updateAppointmentStatus(
        appointment.id,
        targetStatus,
        reason || undefined,
        dockId ? Number(dockId) : undefined
      );
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to update appointment status.');
    } finally {
      setLoading(false);
    }
  };

  const titles: Record<AppointmentStatus, string> = {
    CONFIRMED: 'Confirm Appointment & Assign Dock',
    REJECTED: 'Reject Appointment Request',
    CANCELLED: 'Cancel Appointment',
    CHECKED_IN: 'Register Carrier Check-In at Gate',
    ARRIVED: 'Mark Vehicle Arrived at Dock Bay',
    IN_PROGRESS: 'Begin Unloading / Loading Operations',
    COMPLETED: 'Complete Appointment & Dispatch Driver',
    NO_SHOW: 'Mark Appointment as No-Show',
    DRAFT: 'Save Draft',
    PENDING: 'Submit Request',
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-content" style={{ maxWidth: '520px' }}>
        <div className="modal-header">
          <h3>{titles[targetStatus] || `Change Status to ${targetStatus}`}</h3>
          <button className="btn btn-secondary btn-sm" onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            {error && (
              <div className="alert alert-danger">
                <ShieldAlert size={18} style={{ flexShrink: 0 }} />
                <span>{error}</span>
              </div>
            )}

            <div style={{ marginBottom: '16px', fontSize: '0.88rem', color: '#475569' }}>
              Reference Number: <strong style={{ color: '#0f172a' }}>{appointment.reference_number}</strong>
              <br />
              Current Status: <span className={`status-badge badge-${appointment.status.toLowerCase()}`}>{appointment.status}</span>
            </div>

            {targetStatus === 'CONFIRMED' && (
              <div className="form-group">
                <label className="form-label">Assign Dock Bay *</label>
                <select
                  className="form-select"
                  value={dockId}
                  onChange={(e) => setDockId(Number(e.target.value))}
                  required
                >
                  <option value="">Select a Dock Bay</option>
                  {docks.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.dock_code} — {d.name} {d.max_vehicle_length ? `(max ${d.max_vehicle_length}m)` : ''}
                    </option>
                  ))}
                </select>
                <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '4px' }}>
                  The scheduling engine will verify no conflicts exist before confirming.
                </div>
              </div>
            )}

            <div className="form-group">
              <label className="form-label">
                {targetStatus === 'REJECTED' ? 'Rejection Reason *' : 'Operational Note / Reason (Optional)'}
              </label>
              <textarea
                className="form-textarea"
                rows={3}
                placeholder={
                  targetStatus === 'REJECTED'
                    ? 'State clearly why this request cannot be accommodated...'
                    : 'Add any optional notes regarding this status change...'
                }
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                required={targetStatus === 'REJECTED'}
              />
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose} disabled={loading}>
              Back
            </button>
            <button
              type="submit"
              className={`btn ${targetStatus === 'REJECTED' || targetStatus === 'CANCELLED' ? 'btn-danger' : 'btn-primary'}`}
              disabled={loading}
            >
              <CheckCircle2 size={16} />
              {loading ? 'Processing...' : 'Confirm Action'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
