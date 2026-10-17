import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { Appointment, AppointmentCreate, AppointmentStatus, Carrier, Dock, Warehouse } from '../types';
import { Calendar, CheckCircle2, Clock, ShieldAlert, Truck, X } from 'lucide-react';

interface AppointmentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  initialAppointment?: Appointment | null;
}

export const AppointmentModal: React.FC<AppointmentModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  initialAppointment,
}) => {
  const { user } = useAuth();
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [carriers, setCarriers] = useState<Carrier[]>([]);
  const [availableDocks, setAvailableDocks] = useState<Dock[]>([]);
  const [checkingDocks, setCheckingDocks] = useState(false);

  // Form State
  const [warehouseId, setWarehouseId] = useState<number | ''>('');
  const [carrierId, setCarrierId] = useState<number | ''>('');
  const [dockId, setDockId] = useState<number | ''>('');
  const [startDate, setStartDate] = useState('');
  const [startTime, setStartTime] = useState('');
  const [durationMinutes, setDurationMinutes] = useState(60);
  const [vehicleReg, setVehicleReg] = useState('');
  const [vehicleType, setVehicleType] = useState('Standard Semi-Trailer (40t)');
  const [cargoType, setCargoType] = useState('General Palletized Goods');
  const [cargoDesc, setCargoDesc] = useState('');
  const [cargoWeightKg, setCargoWeightKg] = useState<number | ''>('');
  const [containerNumber, setContainerNumber] = useState('');
  const [notes, setNotes] = useState('');

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!isOpen) return;

    const loadLookups = async () => {
      try {
        const [whList, crList] = await Promise.all([
          api.getWarehouses(),
          api.getCarriers(),
        ]);
        setWarehouses(whList);
        setCarriers(crList);

        if (initialAppointment) {
          setWarehouseId(initialAppointment.warehouse_id);
          setCarrierId(initialAppointment.carrier_id);
          setDockId(initialAppointment.dock_id || '');

          const s = new Date(initialAppointment.scheduled_start);
          const e = new Date(initialAppointment.scheduled_end);

          setStartDate(s.toISOString().split('T')[0]);
          setStartTime(s.toTimeString().substring(0, 5));
          setDurationMinutes(Math.max(30, Math.round((e.getTime() - s.getTime()) / 60000)));

          setVehicleReg(initialAppointment.vehicle_registration);
          setVehicleType(initialAppointment.vehicle_type);
          setCargoType(initialAppointment.cargo_type);
          setCargoDesc(initialAppointment.cargo_description || '');
          setCargoWeightKg(initialAppointment.cargo_weight_kg || '');
          setContainerNumber(initialAppointment.container_number || '');
          setNotes(initialAppointment.notes || '');
        } else {
          // Defaults for new appointment
          if (whList.length > 0) setWarehouseId(whList[0].id);

          if (user?.role === 'CARRIER' && user.carrier) {
            setCarrierId(user.carrier.id);
          } else if (crList.length > 0) {
            setCarrierId(crList[0].id);
          }

          const tomorrow = new Date();
          tomorrow.setDate(tomorrow.getDate() + 1);
          setStartDate(tomorrow.toISOString().split('T')[0]);
          setStartTime('09:00');
          setDurationMinutes(60);

          setVehicleReg('ABC-123');
          setVehicleType('Standard Semi-Trailer (40t)');
          setCargoType('General Palletized Goods');
          setCargoDesc('');
          setCargoWeightKg(15000);
          setContainerNumber('');
          setNotes('');
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load warehouses/carriers');
      }
    };

    loadLookups();
  }, [isOpen, initialAppointment, user]);

  const calculateInterval = () => {
    if (!startDate || !startTime) return null;
    const start = new Date(`${startDate}T${startTime}:00`);
    const end = new Date(start.getTime() + durationMinutes * 60000);
    return {
      scheduled_start: start.toISOString(),
      scheduled_end: end.toISOString(),
    };
  };

  const handleCheckAvailability = async () => {
    if (!warehouseId || !startDate || !startTime) {
      setError('Please select warehouse, date, and start time first.');
      return;
    }

    const interval = calculateInterval();
    if (!interval) return;

    setError(null);
    setCheckingDocks(true);
    try {
      const docks = await api.getAvailableDocks({
        warehouse_id: Number(warehouseId),
        start_time: interval.scheduled_start,
        end_time: interval.scheduled_end,
        vehicle_weight: cargoWeightKg ? Number(cargoWeightKg) : undefined,
        exclude_appointment_id: initialAppointment?.id,
      });
      setAvailableDocks(docks);
      if (docks.length > 0) {
        // Select first available dock if none selected
        if (!dockId || !docks.some(d => d.id === dockId)) {
          setDockId(docks[0].id);
        }
      } else {
        setDockId('');
        setError('No active docks are available for this specific warehouse and time slot.');
      }
    } catch (err: any) {
      setError(err.message || 'Error checking dock availability');
    } finally {
      setCheckingDocks(false);
    }
  };

  const handleSubmit = async (targetStatus: AppointmentStatus) => {
    setError(null);
    const interval = calculateInterval();
    if (!interval) {
      setError('Please provide valid date and start time.');
      return;
    }

    if (!warehouseId || !carrierId || !vehicleReg || !cargoType) {
      setError('Please complete all required fields (*).');
      return;
    }

    setSubmitting(true);
    try {
      if (initialAppointment) {
        // Update
        await api.updateAppointment(initialAppointment.id, {
          dock_id: dockId ? Number(dockId) : null,
          scheduled_start: interval.scheduled_start,
          scheduled_end: interval.scheduled_end,
          vehicle_registration: vehicleReg,
          vehicle_type: vehicleType,
          cargo_type: cargoType,
          cargo_description: cargoDesc || undefined,
          cargo_weight_kg: cargoWeightKg ? Number(cargoWeightKg) : undefined,
          container_number: containerNumber || undefined,
          notes: notes || undefined,
        });
      } else {
        // Create
        const payload: AppointmentCreate = {
          warehouse_id: Number(warehouseId),
          carrier_id: Number(carrierId),
          dock_id: dockId ? Number(dockId) : undefined,
          scheduled_start: interval.scheduled_start,
          scheduled_end: interval.scheduled_end,
          vehicle_registration: vehicleReg,
          vehicle_type: vehicleType,
          cargo_type: cargoType,
          cargo_description: cargoDesc || undefined,
          cargo_weight_kg: cargoWeightKg ? Number(cargoWeightKg) : undefined,
          container_number: containerNumber || undefined,
          notes: notes || undefined,
          status: targetStatus,
        };
        await api.createAppointment(payload);
      }
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Operation failed');
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-backdrop">
      <div className="modal-content" style={{ maxWidth: '680px' }}>
        <div className="modal-header">
          <h3>{initialAppointment ? `Edit Appointment (${initialAppointment.reference_number})` : 'New Dock Appointment Request'}</h3>
          <button className="btn btn-secondary btn-sm" onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        <div className="modal-body">
          {error && (
            <div className="alert alert-danger">
              <ShieldAlert size={18} style={{ flexShrink: 0 }} />
              <span>{error}</span>
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            {/* Warehouse */}
            <div className="form-group">
              <label className="form-label">Destination Warehouse *</label>
              <select
                className="form-select"
                value={warehouseId}
                onChange={(e) => setWarehouseId(Number(e.target.value))}
                disabled={!!initialAppointment}
                required
              >
                {warehouses.map((w) => (
                  <option key={w.id} value={w.id}>
                    {w.name} ({w.code})
                  </option>
                ))}
              </select>
            </div>

            {/* Carrier */}
            <div className="form-group">
              <label className="form-label">Carrier Company *</label>
              <select
                className="form-select"
                value={carrierId}
                onChange={(e) => setCarrierId(Number(e.target.value))}
                disabled={user?.role === 'CARRIER' || !!initialAppointment}
                required
              >
                {carriers.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.company_name} ({c.registration_number})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Time Scheduling */}
          <div style={{ padding: '14px', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0', marginBottom: '16px' }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#334155', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Clock size={16} color="#0284c7" />
              <span>Scheduled Time Interval (Half-Open [Start, End))</span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
              <div>
                <label className="form-label">Date *</label>
                <input
                  type="date"
                  className="form-input"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  required
                />
              </div>

              <div>
                <label className="form-label">Start Time *</label>
                <input
                  type="time"
                  className="form-input"
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                  required
                />
              </div>

              <div>
                <label className="form-label">Duration</label>
                <select
                  className="form-select"
                  value={durationMinutes}
                  onChange={(e) => setDurationMinutes(Number(e.target.value))}
                >
                  <option value={30}>30 Minutes</option>
                  <option value={60}>60 Minutes (Standard)</option>
                  <option value={90}>90 Minutes</option>
                  <option value={120}>120 Minutes (Heavy)</option>
                </select>
              </div>
            </div>

            {/* Dock Availability Verification */}
            <div style={{ marginTop: '12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={handleCheckAvailability}
                disabled={checkingDocks}
              >
                <CheckCircle2 size={14} color="#0284c7" />
                {checkingDocks ? 'Checking Engine...' : 'Check Dock Availability'}
              </button>

              <div style={{ flex: 1, marginLeft: '16px' }}>
                <select
                  className="form-select"
                  value={dockId}
                  onChange={(e) => setDockId(e.target.value ? Number(e.target.value) : '')}
                  style={{ fontSize: '0.82rem' }}
                >
                  <option value="">Leave Unassigned (Warehouse Allocates)</option>
                  {availableDocks.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.dock_code} - {d.name} (Available)
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Vehicle and Cargo info */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div className="form-group">
              <label className="form-label">Vehicle Registration Number *</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. HU-AB-123"
                value={vehicleReg}
                onChange={(e) => setVehicleReg(e.target.value.toUpperCase())}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Vehicle Type *</label>
              <select
                className="form-select"
                value={vehicleType}
                onChange={(e) => setVehicleType(e.target.value)}
              >
                <option value="Curtainsider Semi-Trailer (40t)">Curtainsider Semi-Trailer (40t)</option>
                <option value="Box Truck (18t)">Box Truck (18t)</option>
                <option value="Reefer Semi-Trailer (-20°C)">Reefer Semi-Trailer (-20°C)</option>
                <option value="Express Delivery Van (3.5t)">Express Delivery Van (3.5t)</option>
                <option value="Container Chassis (40ft)">Container Chassis (40ft)</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div className="form-group">
              <label className="form-label">Cargo Type *</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. FMCG / Palletized Goods"
                value={cargoType}
                onChange={(e) => setCargoType(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Cargo Gross Weight (kg)</label>
              <input
                type="number"
                className="form-input"
                placeholder="e.g. 15000"
                value={cargoWeightKg}
                onChange={(e) => setCargoWeightKg(e.target.value ? Number(e.target.value) : '')}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div className="form-group">
              <label className="form-label">Container Number (Optional)</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. MSKU-123456-7"
                value={containerNumber}
                onChange={(e) => setContainerNumber(e.target.value.toUpperCase())}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Cargo Description</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. 33 Euro-pallets packed groceries"
                value={cargoDesc}
                onChange={(e) => setCargoDesc(e.target.value)}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Operational Notes</label>
            <textarea
              className="form-textarea"
              rows={2}
              placeholder="e.g. Tail-lift required, driver contact phone, etc."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </div>
        </div>

        <div className="modal-footer">
          <button type="button" className="btn btn-secondary" onClick={onClose} disabled={submitting}>
            Cancel
          </button>
          {!initialAppointment && (
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => handleSubmit('DRAFT')}
              disabled={submitting}
            >
              Save as Draft
            </button>
          )}
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => handleSubmit('PENDING')}
            disabled={submitting}
          >
            {initialAppointment ? 'Save Changes' : 'Submit Appointment Request'}
          </button>
        </div>
      </div>
    </div>
  );
};
