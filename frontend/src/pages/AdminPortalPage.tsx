import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { AuditLog, Carrier, Dock, User, Warehouse } from '../types';
import {
  Building2,
  FileText,
  Plus,
  RefreshCw,
  Shield,
  Truck,
  Users,
  Warehouse as WarehouseIcon,
  XCircle,
} from 'lucide-react';

export const AdminPortalPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'users' | 'warehouses' | 'carriers' | 'audit'>('users');
  const [users, setUsers] = useState<User[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [carriers, setCarriers] = useState<Carrier[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');

  // New User Form State
  const [showUserModal, setShowUserModal] = useState(false);
  const [userEmail, setUserEmail] = useState('');
  const [userFullName, setUserFullName] = useState('');
  const [userRole, setUserRole] = useState('CARRIER');
  const [userPassword, setUserPassword] = useState('');

  // User Assignment State
  const [selectedUserForAssign, setSelectedUserForAssign] = useState<User | null>(null);
  const [userAssignments, setUserAssignments] = useState<{ carriers: Carrier[]; warehouses: Warehouse[] } | null>(null);
  const [assignCarrierId, setAssignCarrierId] = useState<number | ''>('');
  const [assignWarehouseId, setAssignWarehouseId] = useState<number | ''>('');

  // New Warehouse Form State
  const [showWhModal, setShowWhModal] = useState(false);
  const [editingWarehouse, setEditingWarehouse] = useState<Warehouse | null>(null);
  const [warehouseSearch, setWarehouseSearch] = useState('');
  const [whName, setWhName] = useState('');
  const [whCode, setWhCode] = useState('');
  const [whAddress, setWhAddress] = useState('');
  const [whCity, setWhCity] = useState('');
  const [whPostal, setWhPostal] = useState('');
  const [whCountry, setWhCountry] = useState('Hungary');
  const [whTimezone, setWhTimezone] = useState('Europe/Budapest');

  // Carrier Form State
  const [showCarrierModal, setShowCarrierModal] = useState(false);
  const [editingCarrier, setEditingCarrier] = useState<Carrier | null>(null);
  const [carrierName, setCarrierName] = useState('');
  const [carrierReg, setCarrierReg] = useState('');
  const [carrierEmail, setCarrierEmail] = useState('');
  const [carrierPhone, setCarrierPhone] = useState('');
  const [carrierCountry, setCarrierCountry] = useState('');

  const loadData = async () => {
    setLoading(true);
    setLoadError('');
    const failures: string[] = [];
    const attempt = async <T,>(label: string, request: () => Promise<T>): Promise<T | null> => {
      try {
        return await request();
      } catch {
        failures.push(label);
        return null;
      }
    };
    try {
      if (activeTab === 'users') {
        const [uList, wList, cList] = await Promise.all([
          attempt('users', api.getUsers),
          attempt('warehouses', api.getWarehouses),
          attempt('carriers', api.getCarriers),
        ]);
        if (uList) setUsers(uList);
        if (wList) setWarehouses(wList);
        if (cList) setCarriers(cList);
      } else if (activeTab === 'warehouses') {
        const result = await attempt('warehouses', api.getWarehouses);
        if (result) setWarehouses(result);
      } else if (activeTab === 'carriers') {
        const result = await attempt('carriers', api.getCarriers);
        if (result) setCarriers(result);
      } else if (activeTab === 'audit') {
        const result = await attempt('audit logs', () => api.getAuditLogs({ limit: 100 }));
        if (result) setAuditLogs(result);
      }
    } finally {
      setLoading(false);
      if (failures.length > 0) {
        setLoadError(`Failed to load: ${failures.join(', ')}. The remaining sections are shown; use Refresh to retry.`);
      }
    }
  };

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createUser({
        email: userEmail,
        full_name: userFullName,
        role: userRole,
        password: userPassword,
      });
      setShowUserModal(false);
      setUserEmail('');
      setUserFullName('');
      setUserPassword('');
      loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to create user');
    }
  };

  const handleOpenAssignments = async (u: User) => {
    setSelectedUserForAssign(u);
    try {
      const res = await api.getUserAssignments(u.id);
      setUserAssignments(res);
    } catch (err: any) {
      alert(err.message || 'Failed to load user assignments');
    }
  };

  const handleAssignCarrier = async () => {
    if (!selectedUserForAssign || !assignCarrierId) return;
    try {
      await api.assignUserCarrier(selectedUserForAssign.id, Number(assignCarrierId));
      handleOpenAssignments(selectedUserForAssign);
    } catch (err: any) {
      alert(err.message || 'Failed to assign carrier');
    }
  };

  const handleUnassignCarrier = async (carrierId: number) => {
    if (!selectedUserForAssign) return;
    try {
      await api.unassignUserCarrier(selectedUserForAssign.id, carrierId);
      handleOpenAssignments(selectedUserForAssign);
    } catch (err: any) {
      alert(err.message || 'Failed to unassign carrier');
    }
  };

  const handleAssignWarehouse = async () => {
    if (!selectedUserForAssign || !assignWarehouseId) return;
    try {
      await api.assignUserWarehouse(selectedUserForAssign.id, Number(assignWarehouseId));
      handleOpenAssignments(selectedUserForAssign);
    } catch (err: any) {
      alert(err.message || 'Failed to assign warehouse');
    }
  };

  const handleUnassignWarehouse = async (warehouseId: number) => {
    if (!selectedUserForAssign) return;
    try {
      await api.unassignUserWarehouse(selectedUserForAssign.id, warehouseId);
      handleOpenAssignments(selectedUserForAssign);
    } catch (err: any) {
      alert(err.message || 'Failed to unassign warehouse');
    }
  };

  const openWarehouseForm = (warehouse: Warehouse | null) => {
    setEditingWarehouse(warehouse);
    setWhName(warehouse?.name ?? '');
    setWhCode(warehouse?.code ?? '');
    setWhAddress(warehouse?.address ?? '');
    setWhCity(warehouse?.city ?? '');
    setWhPostal(warehouse?.postal_code ?? '');
    setWhCountry(warehouse?.country ?? 'Hungary');
    setWhTimezone(warehouse?.timezone ?? 'Europe/Budapest');
    setShowWhModal(true);
  };

  const handleSaveWarehouse = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const values = {
        name: whName,
        code: whCode,
        address: whAddress,
        city: whCity,
        postal_code: whPostal,
        country: whCountry,
        timezone: whTimezone,
      };
      if (editingWarehouse) {
        await api.updateWarehouse(editingWarehouse.id, values);
      } else {
        await api.createWarehouse(values);
      }
      setShowWhModal(false);
      setEditingWarehouse(null);
      setWhName('');
      setWhCode('');
      setWhAddress('');
      setWhCity('');
      setWhPostal('');
      loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to create warehouse');
    }
  };

  const handleToggleWarehouse = async (warehouse: Warehouse) => {
    const action = warehouse.is_active ? 'deactivate' : 'reactivate';
    if (!window.confirm(`${action[0].toUpperCase()}${action.slice(1)} ${warehouse.name}? Existing appointments and audit history will be retained.`)) return;
    try {
      if (warehouse.is_active) await api.deleteWarehouse(warehouse.id);
      else await api.updateWarehouse(warehouse.id, { is_active: true });
      await loadData();
    } catch (err: any) {
      alert(err.message || `Failed to ${action} warehouse`);
    }
  };

  const openCarrierForm = (carrier: Carrier | null) => {
    setEditingCarrier(carrier);
    setCarrierName(carrier?.company_name ?? '');
    setCarrierReg(carrier?.registration_number ?? '');
    setCarrierEmail(carrier?.contact_email ?? '');
    setCarrierPhone(carrier?.contact_phone ?? '');
    setCarrierCountry(carrier?.country ?? '');
    setShowCarrierModal(true);
  };

  const handleSaveCarrier = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const values = {
        company_name: carrierName,
        registration_number: carrierReg,
        contact_email: carrierEmail,
        contact_phone: carrierPhone,
        country: carrierCountry,
      };
      if (editingCarrier) {
        await api.updateCarrier(editingCarrier.id, values);
      } else {
        await api.createCarrier(values);
      }
      setShowCarrierModal(false);
      setEditingCarrier(null);
      setCarrierName('');
      setCarrierReg('');
      setCarrierEmail('');
      setCarrierPhone('');
      setCarrierCountry('');
      loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to save carrier');
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <div>
          <h2 style={{ fontSize: '1.35rem', fontWeight: 700 }}>System Administration</h2>
          <p style={{ fontSize: '0.84rem', color: '#64748b' }}>
            User credentials, role authorization, facility hubs, carrier profiles, and audit trail records
          </p>
        </div>

        <button className="btn btn-secondary btn-sm" onClick={loadData} disabled={loading}>
          <RefreshCw size={14} className={loading ? 'spin' : ''} />
          <span>Refresh</span>
        </button>
      </div>

      {loadError && (
        <div role="alert" style={{ marginBottom: '16px', padding: '10px 14px', borderRadius: '6px', border: '1px solid #f59e0b', background: '#fffbeb', color: '#92400e', fontSize: '0.84rem' }}>
          {loadError}
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid #e2e8f0', marginBottom: '20px', paddingBottom: '2px' }}>
        <button
          className={`btn btn-sm ${activeTab === 'users' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('users')}
        >
          <Users size={14} />
          <span>User Accounts & Mappings</span>
        </button>

        <button
          className={`btn btn-sm ${activeTab === 'warehouses' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('warehouses')}
        >
          <Building2 size={14} />
          <span>Warehouses</span>
        </button>

        <button
          className={`btn btn-sm ${activeTab === 'carriers' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('carriers')}
        >
          <Truck size={14} />
          <span>Carriers</span>
        </button>

        <button
          className={`btn btn-sm ${activeTab === 'audit' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('audit')}
        >
          <FileText size={14} />
          <span>Audit Log Trail</span>
        </button>
      </div>

      {/* TAB 1: USERS */}
      {activeTab === 'users' && (
        <div className="card">
          <div className="card-title">
            <span>User Accounts</span>
            <button className="btn btn-primary btn-sm" onClick={() => setShowUserModal(true)}>
              <Plus size={14} />
              <span>New User</span>
            </button>
          </div>

          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Full Name</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id}>
                    <td>#{u.id}</td>
                    <td style={{ fontWeight: 600 }}>{u.full_name}</td>
                    <td>{u.email}</td>
                    <td>
                      <span style={{
                        padding: '2px 8px',
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        background: '#f1f5f9',
                        color: '#334155',
                      }}>
                        {u.role}
                      </span>
                    </td>
                    <td>
                      <span style={{ color: u.is_active ? '#16a34a' : '#dc2626', fontWeight: 600, fontSize: '0.78rem' }}>
                        {u.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => handleOpenAssignments(u)}
                      >
                        Manage Scope
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 2: WAREHOUSES */}
      {activeTab === 'warehouses' && (
        <div className="card">
          <div className="card-title">
            <span>Distribution Centers & Warehouses</span>
            <button className="btn btn-primary btn-sm" onClick={() => openWarehouseForm(null)}>
              <Plus size={14} />
              <span>New Warehouse</span>
            </button>
          </div>

          <div className="table-container">
            <input
              type="search"
              className="form-input"
              aria-label="Search warehouses"
              placeholder="Search by name, code, or city"
              value={warehouseSearch}
              onChange={(event) => setWarehouseSearch(event.target.value)}
              style={{ maxWidth: '360px', marginBottom: '12px' }}
            />
            <table className="data-table">
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Facility Name</th>
                  <th>City / Country</th>
                  <th>Address</th>
                  <th>Timezone</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {warehouses.filter((warehouse) => `${warehouse.name} ${warehouse.code} ${warehouse.city}`.toLowerCase().includes(warehouseSearch.toLowerCase())).map((w) => (
                  <tr key={w.id}>
                    <td><strong style={{ color: '#0284c7' }}>{w.code}</strong></td>
                    <td style={{ fontWeight: 600 }}>{w.name}</td>
                    <td>{w.city}, {w.country}</td>
                    <td>{w.address} ({w.postal_code})</td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem' }}>{w.timezone}</td>
                    <td>
                      <span style={{ color: w.is_active ? '#16a34a' : '#dc2626', fontWeight: 600 }}>
                        {w.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>
                      <button className="btn btn-secondary btn-sm" onClick={() => openWarehouseForm(w)}>Edit</button>
                      <button className="btn btn-secondary btn-sm" style={{ marginLeft: 6 }} onClick={() => handleToggleWarehouse(w)}>
                        {w.is_active ? 'Deactivate' : 'Reactivate'}
                      </button>
                    </td>
                  </tr>
                ))}
                {warehouses.filter((warehouse) => `${warehouse.name} ${warehouse.code} ${warehouse.city}`.toLowerCase().includes(warehouseSearch.toLowerCase())).length === 0 && (
                  <tr><td colSpan={7} style={{ textAlign: 'center', padding: 28, color: '#64748b' }}>No warehouses match this search. Add a warehouse to begin.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 3: CARRIERS */}
      {activeTab === 'carriers' && (
        <div className="card">
          <div className="card-title">
            <span>Registered Carrier Logistics Companies</span>
            <button className="btn btn-primary btn-sm" onClick={() => openCarrierForm(null)}>
              <Plus size={14} />
              <span>New Carrier</span>
            </button>
          </div>

          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Reg Number</th>
                  <th>Company Name</th>
                  <th>Contact Email</th>
                  <th>Phone</th>
                  <th>Country</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {carriers.map((c) => (
                  <tr key={c.id}>
                    <td><strong style={{ color: '#0284c7' }}>{c.registration_number}</strong></td>
                    <td style={{ fontWeight: 600 }}>{c.company_name}</td>
                    <td>{c.contact_email}</td>
                    <td>{c.contact_phone || '—'}</td>
                    <td>{c.country}</td>
                    <td>
                      <span style={{ color: c.is_active ? '#16a34a' : '#dc2626', fontWeight: 600 }}>
                        {c.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>
                      <button className="btn btn-secondary btn-sm" onClick={() => openCarrierForm(c)}>Edit</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 4: AUDIT LOGS */}
      {activeTab === 'audit' && (
        <div className="card">
          <div className="card-title">
            <span>System Audit Trail</span>
          </div>

          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Action</th>
                  <th>Entity</th>
                  <th>Entity ID</th>
                  <th>User ID</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>
                {auditLogs.length === 0 ? (
                  <tr>
                    <td colSpan={6} style={{ textAlign: 'center', padding: '30px', color: '#94a3b8' }}>
                      No audit logs recorded yet.
                    </td>
                  </tr>
                ) : (
                  auditLogs.map((log) => (
                    <tr key={log.id}>
                      <td style={{ whiteSpace: 'nowrap', fontSize: '0.78rem', color: '#64748b' }}>
                        {new Date(log.created_at).toLocaleString()}
                      </td>
                      <td>
                        <span style={{
                          padding: '2px 8px',
                          borderRadius: '4px',
                          background: '#f1f5f9',
                          fontWeight: 600,
                          fontSize: '0.74rem',
                          color: '#0f172a',
                        }}>
                          {log.action}
                        </span>
                      </td>
                      <td>{log.entity_type}</td>
                      <td>{log.entity_id ?? '—'}</td>
                      <td>{log.user_id ? `User #${log.user_id}` : 'System'}</td>
                      <td style={{ maxWidth: '300px', fontSize: '0.8rem' }}>{log.description || '—'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* User Scoping / Assignment Modal */}
      {selectedUserForAssign && (
        <div className="modal-backdrop">
          <div className="modal-content" style={{ maxWidth: '540px' }}>
            <div className="modal-header">
              <h3>Scope & Mappings for {selectedUserForAssign.full_name}</h3>
              <button className="btn btn-secondary btn-sm" onClick={() => setSelectedUserForAssign(null)}>
                <XCircle size={16} />
              </button>
            </div>
            <div className="modal-body">
              <div style={{ fontSize: '0.82rem', color: '#64748b', marginBottom: '16px' }}>
                Role: <strong>{selectedUserForAssign.role}</strong> ({selectedUserForAssign.email})
              </div>

              {/* Carrier assignment */}
              {selectedUserForAssign.role === 'CARRIER' && (
                <div style={{ marginBottom: '20px' }}>
                  <label className="form-label">Associated Carrier Companies</label>
                  <div style={{ display: 'flex', gap: '8px', marginBottom: '10px' }}>
                    <select
                      className="form-select"
                      value={assignCarrierId}
                      onChange={(e) => setAssignCarrierId(e.target.value ? Number(e.target.value) : '')}
                    >
                      <option value="">Select Carrier to Map</option>
                      {carriers.map((c) => (
                        <option key={c.id} value={c.id}>{c.company_name}</option>
                      ))}
                    </select>
                    <button className="btn btn-primary btn-sm" onClick={handleAssignCarrier}>
                      Add
                    </button>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    {userAssignments?.carriers.map((c) => (
                      <div key={c.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 10px', background: '#f8fafc', borderRadius: '4px', fontSize: '0.82rem' }}>
                        <span>{c.company_name} ({c.registration_number})</span>
                        <button className="btn btn-secondary btn-sm" style={{ padding: '2px 6px', color: '#ef4444' }} onClick={() => handleUnassignCarrier(c.id)}>Remove</button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Warehouse assignment */}
              {(selectedUserForAssign.role === 'WAREHOUSE_MANAGER' || selectedUserForAssign.role === 'WAREHOUSE_STAFF') && (
                <div>
                  <label className="form-label">Authorized Warehouses</label>
                  <div style={{ display: 'flex', gap: '8px', marginBottom: '10px' }}>
                    <select
                      className="form-select"
                      value={assignWarehouseId}
                      onChange={(e) => setAssignWarehouseId(e.target.value ? Number(e.target.value) : '')}
                    >
                      <option value="">Select Warehouse to Authorize</option>
                      {warehouses.map((w) => (
                        <option key={w.id} value={w.id}>{w.name} ({w.code})</option>
                      ))}
                    </select>
                    <button className="btn btn-primary btn-sm" onClick={handleAssignWarehouse}>
                      Add
                    </button>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    {userAssignments?.warehouses.map((w) => (
                      <div key={w.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 10px', background: '#f8fafc', borderRadius: '4px', fontSize: '0.82rem' }}>
                        <span>{w.name} ({w.code})</span>
                        <button className="btn btn-secondary btn-sm" style={{ padding: '2px 6px', color: '#ef4444' }} onClick={() => handleUnassignWarehouse(w.id)}>Remove</button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setSelectedUserForAssign(null)}>Done</button>
            </div>
          </div>
        </div>
      )}

      {/* New User Modal */}
      {showUserModal && (
        <div className="modal-backdrop">
          <div className="modal-content" style={{ maxWidth: '440px' }}>
            <div className="modal-header">
              <h3>Create User Account</h3>
              <button className="btn btn-secondary btn-sm" onClick={() => setShowUserModal(false)}><XCircle size={16} /></button>
            </div>
            <form onSubmit={handleCreateUser}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Full Name *</label>
                  <input type="text" className="form-input" required value={userFullName} onChange={(e) => setUserFullName(e.target.value)} />
                </div>
                <div className="form-group">
                  <label className="form-label">Email Address *</label>
                  <input type="email" className="form-input" required value={userEmail} onChange={(e) => setUserEmail(e.target.value)} />
                </div>
                <div className="form-group">
                  <label className="form-label">Role *</label>
                  <select className="form-select" value={userRole} onChange={(e) => setUserRole(e.target.value)}>
                    <option value="CARRIER">Carrier</option>
                    <option value="WAREHOUSE_STAFF">Warehouse Staff</option>
                    <option value="WAREHOUSE_MANAGER">Warehouse Manager</option>
                    <option value="ADMIN">System Administrator</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Password *</label>
                  <input type="password" minLength={8} className="form-input" required value={userPassword} onChange={(e) => setUserPassword(e.target.value)} />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowUserModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Create User</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* New Warehouse Modal */}
      {showWhModal && (
        <div className="modal-backdrop">
          <div className="modal-content" style={{ maxWidth: '480px' }}>
            <div className="modal-header">
              <h3>{editingWarehouse ? 'Edit Warehouse Hub' : 'Register Warehouse Hub'}</h3>
              <button className="btn btn-secondary btn-sm" onClick={() => { setShowWhModal(false); setEditingWarehouse(null); }}><XCircle size={16} /></button>
            </div>
            <form onSubmit={handleSaveWarehouse}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Warehouse Code *</label>
                  <input type="text" className="form-input" required placeholder="WH-XYZ-01" value={whCode} onChange={(e) => setWhCode(e.target.value.toUpperCase())} />
                </div>
                <div className="form-group">
                  <label className="form-label">Name *</label>
                  <input type="text" className="form-input" required placeholder="Central Hub" value={whName} onChange={(e) => setWhName(e.target.value)} />
                </div>
                <div className="form-group">
                  <label className="form-label">Address *</label>
                  <input type="text" className="form-input" required placeholder="Logistics Way 10" value={whAddress} onChange={(e) => setWhAddress(e.target.value)} />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <div className="form-group">
                    <label className="form-label">City *</label>
                    <input type="text" className="form-input" required value={whCity} onChange={(e) => setWhCity(e.target.value)} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Postal Code *</label>
                    <input type="text" className="form-input" required value={whPostal} onChange={(e) => setWhPostal(e.target.value)} />
                  </div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <div className="form-group">
                    <label className="form-label">Country *</label>
                    <input type="text" className="form-input" required value={whCountry} onChange={(e) => setWhCountry(e.target.value)} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Timezone *</label>
                    <input type="text" className="form-input" required value={whTimezone} onChange={(e) => setWhTimezone(e.target.value)} />
                  </div>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => { setShowWhModal(false); setEditingWarehouse(null); }}>Cancel</button>
                <button type="submit" className="btn btn-primary">{editingWarehouse ? 'Save Changes' : 'Create Warehouse'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Carrier Modal */}
      {showCarrierModal && (
        <div className="modal-backdrop">
          <div className="modal-content" style={{ maxWidth: '480px' }}>
            <div className="modal-header">
              <h3>{editingCarrier ? 'Edit Carrier Partner' : 'Register Carrier Partner'}</h3>
              <button className="btn btn-secondary btn-sm" onClick={() => { setShowCarrierModal(false); setEditingCarrier(null); }}><XCircle size={16} /></button>
            </div>
            <form onSubmit={handleSaveCarrier}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Company Name *</label>
                  <input type="text" className="form-input" required placeholder="TransLogistics Kft." value={carrierName} onChange={(e) => setCarrierName(e.target.value)} />
                </div>
                <div className="form-group">
                  <label className="form-label">Registration Number *</label>
                  <input type="text" className="form-input" required placeholder="REG-123456" value={carrierReg} onChange={(e) => setCarrierReg(e.target.value)} />
                </div>
                <div className="form-group">
                  <label className="form-label">Contact Email *</label>
                  <input type="email" className="form-input" required placeholder="dispatch@carrier.com" value={carrierEmail} onChange={(e) => setCarrierEmail(e.target.value)} />
                </div>
                <div className="form-group">
                  <label className="form-label">Contact Phone</label>
                  <input type="text" className="form-input" placeholder="+36 1 234 5678" value={carrierPhone} onChange={(e) => setCarrierPhone(e.target.value)} />
                </div>
                <div className="form-group">
                  <label className="form-label">Country *</label>
                  <input type="text" className="form-input" required placeholder="e.g. Hungary, Germany, Poland" value={carrierCountry} onChange={(e) => setCarrierCountry(e.target.value)} />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => { setShowCarrierModal(false); setEditingCarrier(null); }}>Cancel</button>
                <button type="submit" className="btn btn-primary">{editingCarrier ? 'Save Changes' : 'Create Carrier'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
