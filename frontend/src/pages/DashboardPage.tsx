import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Appointment, DashboardMetrics, Warehouse } from '../types';
import {
  Calendar,
  CheckCircle2,
  Clock,
  Layers,
  Percent,
  RefreshCw,
  Truck,
  Warehouse as WarehouseIcon,
  XCircle,
} from 'lucide-react';

interface DashboardPageProps {
  onOpenAppointment: (appt: Appointment) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ onOpenAppointment }) => {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [selectedWarehouseId, setSelectedWarehouseId] = useState<number | ''>('');
  const [recentAppointments, setRecentAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [whList, metricsData, apptList] = await Promise.all([
        api.getWarehouses(),
        api.getDashboardMetrics(selectedWarehouseId ? Number(selectedWarehouseId) : undefined),
        api.getAppointments({
          warehouse_id: selectedWarehouseId ? Number(selectedWarehouseId) : undefined,
        }),
      ]);
      setWarehouses(whList);
      setMetrics(metricsData);
      setRecentAppointments(apptList.slice(0, 8));
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedWarehouseId]);

  return (
    <div>
      {/* Page Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div>
          <h2 style={{ fontSize: '1.35rem', fontWeight: 700 }}>Logistics Operational Dashboard</h2>
          <p style={{ fontSize: '0.84rem', color: '#64748b' }}>
            Real-time dock throughput, capacity metrics, and appointment status distribution
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <select
            className="form-select"
            value={selectedWarehouseId}
            onChange={(e) => setSelectedWarehouseId(e.target.value ? Number(e.target.value) : '')}
            style={{ width: '240px', fontSize: '0.84rem' }}
          >
            <option value="">All Warehouses</option>
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

      {/* Metrics Row 1 */}
      {metrics && (
        <>
          <div className="metrics-grid">
            <div className="metric-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="metric-label">Total Appointments</span>
                <Layers size={18} color="#0284c7" />
              </div>
              <div className="metric-value">{metrics.total_appointments}</div>
            </div>

            <div className="metric-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="metric-label">Pending Approval</span>
                <Clock size={18} color="#f59e0b" />
              </div>
              <div className="metric-value" style={{ color: '#d97706' }}>
                {metrics.pending_appointments}
              </div>
            </div>

            <div className="metric-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="metric-label">Confirmed Slots</span>
                <CheckCircle2 size={18} color="#0284c7" />
              </div>
              <div className="metric-value" style={{ color: '#0284c7' }}>
                {metrics.confirmed_appointments}
              </div>
            </div>

            <div className="metric-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="metric-label">Completed Orders</span>
                <CheckCircle2 size={18} color="#10b981" />
              </div>
              <div className="metric-value" style={{ color: '#16a34a' }}>
                {metrics.completed_appointments}
              </div>
            </div>

            <div className="metric-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="metric-label">Dock Utilization</span>
                <Percent size={18} color="#8b5cf6" />
              </div>
              <div className="metric-value" style={{ color: '#7c3aed' }}>
                {metrics.dock_utilization_percent}%
              </div>
            </div>
          </div>

          {/* Operational Status Breakdown & Active Docks */}
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px', marginBottom: '24px' }}>
            <div className="card">
              <div className="card-title">
                <span>Appointment Distribution by Lifecycle Status</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '12px' }}>
                {Object.entries(metrics.status_distribution).map(([st, cnt]) => (
                  <div
                    key={st}
                    style={{
                      padding: '12px',
                      background: '#f8fafc',
                      borderRadius: '6px',
                      border: '1px solid #e2e8f0',
                      textAlign: 'center',
                    }}
                  >
                    <span className={`status-badge badge-${st.toLowerCase()}`}>{st}</span>
                    <div style={{ fontSize: '1.25rem', fontWeight: 700, marginTop: '6px' }}>{cnt}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="card">
              <div className="card-title">
                <span>Facility Infrastructure</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 14px', background: '#f8fafc', borderRadius: '6px' }}>
                  <span style={{ fontSize: '0.85rem', color: '#475569' }}>Active Warehouses</span>
                  <strong>{metrics.total_warehouses}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 14px', background: '#f8fafc', borderRadius: '6px' }}>
                  <span style={{ fontSize: '0.85rem', color: '#475569' }}>Total Dock Bays</span>
                  <strong>{metrics.total_docks}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 14px', background: '#f8fafc', borderRadius: '6px' }}>
                  <span style={{ fontSize: '0.85rem', color: '#475569' }}>Operational Docks</span>
                  <strong style={{ color: '#16a34a' }}>{metrics.active_docks}</strong>
                </div>
              </div>
            </div>
          </div>

          {/* Daily Appointment Volume Chart (CSS Bar Series) */}
          <div className="card" style={{ marginBottom: '24px' }}>
            <div className="card-title">
              <span>Daily Appointment Volume</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'flex-end', gap: '10px', height: '140px', padding: '10px 0 20px', borderBottom: '1px solid #e2e8f0' }}>
              {metrics.daily_volume.map((item) => {
                const maxCount = Math.max(1, ...metrics.daily_volume.map((v) => v.count));
                const heightPct = Math.max(8, Math.round((item.count / maxCount) * 100));
                return (
                  <div
                    key={item.date}
                    style={{
                      flex: 1,
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: '6px',
                      height: '100%',
                      justifyContent: 'flex-end',
                    }}
                  >
                    <span style={{ fontSize: '0.72rem', fontWeight: 600, color: item.count > 0 ? '#0284c7' : '#94a3b8' }}>
                      {item.count}
                    </span>
                    <div
                      style={{
                        width: '100%',
                        maxWidth: '28px',
                        height: `${heightPct}%`,
                        backgroundColor: item.count > 0 ? '#0284c7' : '#e2e8f0',
                        borderRadius: '4px 4px 0 0',
                      }}
                    />
                    <span style={{ fontSize: '0.68rem', color: '#64748b', whiteSpace: 'nowrap' }}>
                      {item.date.slice(5)}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}

      {/* Recent Appointments Table */}
      <div className="card">
        <div className="card-title">
          <span>Recent Operational Appointments</span>
        </div>
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Reference</th>
                <th>Status</th>
                <th>Warehouse</th>
                <th>Dock</th>
                <th>Carrier</th>
                <th>Vehicle</th>
                <th>Scheduled Slot</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {recentAppointments.length === 0 ? (
                <tr>
                  <td colSpan={8} style={{ textAlign: 'center', padding: '30px', color: '#94a3b8' }}>
                    No appointments scheduled yet.
                  </td>
                </tr>
              ) : (
                recentAppointments.map((a) => (
                  <tr key={a.id}>
                    <td>
                      <span style={{ fontWeight: 600, color: '#0284c7' }}>{a.reference_number}</span>
                    </td>
                    <td>
                      <span className={`status-badge badge-${a.status.toLowerCase()}`}>{a.status}</span>
                    </td>
                    <td>{a.warehouse_name || `WH #${a.warehouse_id}`}</td>
                    <td>
                      {a.dock_code ? (
                        <span style={{ fontWeight: 600, color: '#0f172a' }}>{a.dock_code}</span>
                      ) : (
                        <span style={{ color: '#94a3b8', fontStyle: 'italic' }}>Unassigned</span>
                      )}
                    </td>
                    <td>{a.carrier_name || `Carrier #${a.carrier_id}`}</td>
                    <td>{a.vehicle_registration}</td>
                    <td>
                      {new Date(a.scheduled_start).toLocaleDateString([], { month: 'short', day: 'numeric' })}{' '}
                      {new Date(a.scheduled_start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => onOpenAppointment(a)}
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
