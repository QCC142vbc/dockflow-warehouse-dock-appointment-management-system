import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Appointment, AppointmentEvent } from '../types';
import { Clock, History, Truck, Warehouse, X, AlertTriangle } from 'lucide-react';

interface AppointmentDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  appointment: Appointment | null;
}

export const AppointmentDetailModal: React.FC<AppointmentDetailModalProps> = ({
  isOpen,
  onClose,
  appointment,
}) => {
  const [events, setEvents] = useState<AppointmentEvent[]>([]);
  const [loadingEvents, setLoadingEvents] = useState(false);

  useEffect(() => {
    if (!isOpen || !appointment) return;

    setLoadingEvents(true);
    api.getAppointmentEvents(appointment.id)
      .then(setEvents)
      .catch(() => setEvents([]))
      .finally(() => setLoadingEvents(false));
  }, [isOpen, appointment]);

  if (!isOpen || !appointment) return null;

  const formatDate = (isoString: string) => {
    try {
      const d = new Date(isoString);
      return d.toLocaleString([], {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-content" style={{ maxWidth: '720px' }}>
        <div className="modal-header">
          <div>
            <h3>Appointment Details</h3>
            <span style={{ fontSize: '0.82rem', color: '#64748b' }}>
              Reference: <strong style={{ color: '#0284c7' }}>{appointment.reference_number}</strong>
            </span>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        <div className="modal-body">
          {/* Status Banner */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '14px 18px',
            background: '#f8fafc',
            borderRadius: '8px',
            border: '1px solid #e2e8f0',
            marginBottom: '20px',
          }}>
            <div>
              <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#64748b', fontWeight: 600 }}>
                Lifecycle Status
              </span>
              <div style={{ marginTop: '2px' }}>
                <span className={`status-badge badge-${appointment.status.toLowerCase()}`} style={{ fontSize: '0.85rem' }}>
                  {appointment.status}
                </span>
              </div>
            </div>

            <div style={{ textAlign: 'right' }}>
              <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#64748b', fontWeight: 600 }}>
                Scheduled Slot
              </span>
              <div style={{ fontSize: '0.88rem', fontWeight: 600, color: '#0f172a', marginTop: '2px' }}>
                {formatDate(appointment.scheduled_start)} — {formatDate(appointment.scheduled_end).split(',')[1]}
              </div>
            </div>
          </div>

          {/* Rejection Reason Alert if applicable */}
          {appointment.rejection_reason && (
            <div className="alert alert-danger" style={{ marginBottom: '20px' }}>
              <AlertTriangle size={18} style={{ flexShrink: 0 }} />
              <div>
                <strong>Rejection Reason: </strong>
                {appointment.rejection_reason}
              </div>
            </div>
          )}

          {/* Grid of Key Info */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
            <div className="card" style={{ padding: '14px' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Warehouse size={14} color="#0284c7" />
                Location & Dock
              </div>
              <div style={{ fontSize: '0.86rem' }}>
                <div><strong>Warehouse:</strong> {appointment.warehouse_name || `Warehouse #${appointment.warehouse_id}`}</div>
                <div style={{ marginTop: '4px' }}>
                  <strong>Assigned Bay:</strong>{' '}
                  {appointment.dock_code ? (
                    <span style={{ color: '#0284c7', fontWeight: 600 }}>{appointment.dock_code}</span>
                  ) : (
                    <span style={{ color: '#94a3b8', fontStyle: 'italic' }}>Pending Allocation</span>
                  )}
                </div>
              </div>
            </div>

            <div className="card" style={{ padding: '14px' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Truck size={14} color="#0284c7" />
                Carrier & Vehicle
              </div>
              <div style={{ fontSize: '0.86rem' }}>
                <div><strong>Carrier:</strong> {appointment.carrier_name || `Carrier #${appointment.carrier_id}`}</div>
                <div style={{ marginTop: '4px' }}>
                  <strong>Plate:</strong> <span style={{ fontFamily: 'var(--font-mono)' }}>{appointment.vehicle_registration}</span> ({appointment.vehicle_type})
                </div>
              </div>
            </div>
          </div>

          {/* Cargo Details */}
          <div className="card" style={{ padding: '14px', marginBottom: '24px' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', marginBottom: '8px' }}>
              Cargo Manifest
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px', fontSize: '0.86rem' }}>
              <div>
                <strong>Type:</strong> {appointment.cargo_type}
              </div>
              <div>
                <strong>Gross Weight:</strong> {appointment.cargo_weight_kg ? `${appointment.cargo_weight_kg.toLocaleString()} kg` : 'N/A'}
              </div>
              <div>
                <strong>Container:</strong> {appointment.container_number || 'None'}
              </div>
            </div>
            {appointment.cargo_description && (
              <div style={{ marginTop: '8px', fontSize: '0.82rem', color: '#475569' }}>
                <strong>Description:</strong> {appointment.cargo_description}
              </div>
            )}
            {appointment.notes && (
              <div style={{ marginTop: '8px', fontSize: '0.82rem', color: '#64748b', fontStyle: 'italic' }}>
                <strong>Notes:</strong> {appointment.notes}
              </div>
            )}
          </div>

          {/* Event History Timeline */}
          <div>
            <div style={{ fontSize: '0.88rem', fontWeight: 600, color: '#0f172a', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <History size={16} color="#0284c7" />
              <span>Status Event History</span>
            </div>

            {loadingEvents ? (
              <div style={{ fontSize: '0.82rem', color: '#64748b' }}>Loading history...</div>
            ) : events.length === 0 ? (
              <div style={{ fontSize: '0.82rem', color: '#94a3b8', fontStyle: 'italic' }}>No logged events recorded.</div>
            ) : (
              <div style={{ borderLeft: '2px solid #e2e8f0', marginLeft: '8px', paddingLeft: '16px' }}>
                {events.map((evt, idx) => (
                  <div key={evt.id || idx} style={{ marginBottom: '16px', position: 'relative' }}>
                    <div style={{
                      position: 'absolute',
                      left: '-23px',
                      top: '4px',
                      width: '12px',
                      height: '12px',
                      borderRadius: '50%',
                      background: '#0284c7',
                      border: '2px solid #ffffff',
                    }} />
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span className={`status-badge badge-${evt.new_status.toLowerCase()}`}>
                        {evt.new_status}
                      </span>
                      {evt.previous_status && (
                        <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                          (from {evt.previous_status})
                        </span>
                      )}
                      <span style={{ fontSize: '0.75rem', color: '#64748b', marginLeft: 'auto' }}>
                        {formatDate(evt.created_at)}
                      </span>
                    </div>
                    {evt.reason && (
                      <div style={{ fontSize: '0.8rem', color: '#475569', marginTop: '4px' }}>
                        {evt.reason}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="modal-footer">
          <button type="button" className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
