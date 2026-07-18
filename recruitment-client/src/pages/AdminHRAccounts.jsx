import React, { useState, useEffect, useCallback } from 'react';
import { UserPlus, Search, ShieldAlert, KeyRound, CheckCircle, XCircle, RefreshCw, Eye, EyeOff } from 'lucide-react';
import adminService from '../services/adminService';
import './AdminHRAccounts.css';

const AdminHRAccounts = () => {
  const [hrAccounts, setHrAccounts] = useState([]);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Modals state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showResetModal, setShowResetModal] = useState(false);
  const [targetHR, setTargetHR] = useState(null);

  // Form states
  const [createForm, setCreateForm] = useState({
    full_name: '',
    email: '',
    temporary_password: '',
    confirm_temporary_password: '',
  });
  const [resetForm, setResetForm] = useState({
    temporary_password: '',
    confirm_temporary_password: '',
  });
  const [formLoading, setFormLoading] = useState(false);
  const [formError, setFormError] = useState('');

  // Password visibility
  const [showCreatePass, setShowCreatePass] = useState(false);
  const [showResetPass, setShowResetPass] = useState(false);

  const fetchAccounts = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await adminService.getHRAccounts({
        page,
        page_size: pageSize,
        search: search.trim() || undefined,
        status: statusFilter,
        sort_by: sortBy,
        sort_order: sortOrder,
      });
      setHrAccounts(data.items || []);
      setTotal(data.total || 0);
      setTotalPages(data.total_pages || 0);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to fetch HR accounts');
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, search, statusFilter, sortBy, sortOrder]);

  useEffect(() => {
    fetchAccounts();
  }, [fetchAccounts]);

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    setFormError('');

    if (createForm.temporary_password !== createForm.confirm_temporary_password) {
      setFormError('Temporary password and confirmation do not match.');
      return;
    }

    setFormLoading(true);
    try {
      await adminService.createHRAccount(createForm);
      setSuccessMsg(`HR login account created for ${createForm.email}. Share the temporary password securely.`);
      setCreateForm({ full_name: '', email: '', temporary_password: '', confirm_temporary_password: '' });
      setShowCreateModal(false);
      setPage(1);
      fetchAccounts();
    } catch (err) {
      setFormError(err.response?.data?.detail || err.message || 'Failed to create HR account');
    } finally {
      setFormLoading(false);
    }
  };

  const handleStatusToggle = async (hr) => {
    const nextStatus = !hr.is_active;
    const actionText = nextStatus ? 'activate' : 'deactivate';
    if (!window.confirm(`Are you sure you want to ${actionText} HR account for ${hr.email}?`)) return;

    try {
      const res = await adminService.updateHRAccountStatus(hr.id, nextStatus);
      setSuccessMsg(res.message);
      fetchAccounts();
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to update HR status');
    }
  };

  const handleResetSubmit = async (e) => {
    e.preventDefault();
    setFormError('');

    if (resetForm.temporary_password !== resetForm.confirm_temporary_password) {
      setFormError('Temporary password and confirmation do not match.');
      return;
    }

    setFormLoading(true);
    try {
      const res = await adminService.resetHRPassword(targetHR.id, resetForm);
      setSuccessMsg(res.message);
      setResetForm({ temporary_password: '', confirm_temporary_password: '' });
      setShowResetModal(false);
      fetchAccounts();
    } catch (err) {
      setFormError(err.response?.data?.detail || err.message || 'Failed to reset HR password');
    } finally {
      setFormLoading(false);
    }
  };

  return (
    <div className="admin-container">
      <div className="admin-header">
        <div className="admin-title-area">
          <h1>HR Account Management</h1>
          <p>Create, manage, activate, and reset credentials for HR team accounts.</p>
        </div>
        <button className="btn-create-hr" onClick={() => { setShowCreateModal(true); setFormError(''); }}>
          <UserPlus size={18} />
          Create HR Account
        </button>
      </div>

      {successMsg && (
        <div className="error-banner" style={{ background: 'rgba(16, 185, 129, 0.15)', borderColor: 'rgba(16, 185, 129, 0.3)', color: '#34d399' }}>
          {successMsg}
          <button style={{ float: 'right', background: 'none', border: 'none', color: '#34d399', cursor: 'pointer' }} onClick={() => setSuccessMsg('')}>✕</button>
        </div>
      )}

      {error && <div className="error-banner">{error}</div>}

      <div className="admin-controls-bar">
        <div className="search-input-box">
          <Search size={16} className="search-icon" />
          <input
            type="text"
            placeholder="Search by name or email..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          />
        </div>

        <select className="filter-select" value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}>
          <option value="all">All Statuses</option>
          <option value="active">Active Only</option>
          <option value="inactive">Inactive Only</option>
        </select>

        <select className="filter-select" value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
          <option value="created_at">Sort by Created Date</option>
          <option value="full_name">Sort by Name</option>
          <option value="email">Sort by Email</option>
          <option value="last_login_at">Sort by Last Login</option>
          <option value="is_active">Sort by Status</option>
        </select>

        <select className="filter-select" value={sortOrder} onChange={(e) => setSortOrder(e.target.value)}>
          <option value="desc">Descending</option>
          <option value="asc">Ascending</option>
        </select>

        <button className="btn-action" onClick={fetchAccounts} title="Refresh list">
          <RefreshCw size={14} />
        </button>
      </div>

      <div className="admin-table-card">
        {loading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#94a3b8' }}>Loading HR accounts...</div>
        ) : hrAccounts.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#94a3b8' }}>No HR accounts found.</div>
        ) : (
          <table className="hr-table">
            <thead>
              <tr>
                <th>HR Name</th>
                <th>Email</th>
                <th>Status</th>
                <th>Password Change</th>
                <th>Created</th>
                <th>Last Login</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {hrAccounts.map((hr) => (
                <tr key={hr.id}>
                  <td style={{ fontWeight: 600 }}>{hr.full_name}</td>
                  <td>{hr.email}</td>
                  <td>
                    <span className={`status-badge ${hr.is_active ? 'active' : 'inactive'}`}>
                      {hr.is_active ? <CheckCircle size={12} /> : <XCircle size={12} />}
                      {hr.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td>
                    <span className={`pwd-flag-badge ${hr.must_change_password ? 'required' : 'normal'}`}>
                      {hr.must_change_password ? 'Password Change Required' : 'Normal'}
                    </span>
                  </td>
                  <td>{new Date(hr.created_at).toLocaleDateString()}</td>
                  <td>{hr.last_login_at ? new Date(hr.last_login_at).toLocaleString() : 'Never'}</td>
                  <td>
                    <div className="action-buttons">
                      <button
                        className={`btn-action ${hr.is_active ? 'deactivate' : 'activate'}`}
                        onClick={() => handleStatusToggle(hr)}
                      >
                        {hr.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                      <button
                        className="btn-action"
                        onClick={() => { setTargetHR(hr); setShowResetModal(true); setFormError(''); }}
                      >
                        <KeyRound size={13} style={{ display: 'inline', marginRight: 4 }} />
                        Reset Pwd
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        <div className="pagination-bar">
          <div>
            Showing {hrAccounts.length} of {total} accounts (Page {page} of {totalPages || 1})
          </div>
          <div className="pagination-controls">
            <button className="btn-page" disabled={page <= 1} onClick={() => setPage(p => Math.max(1, p - 1))}>
              Previous
            </button>
            <button className="btn-page" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>
              Next
            </button>
          </div>
        </div>
      </div>

      {/* CREATE HR MODAL */}
      {showCreateModal && (
        <div className="modal-overlay">
          <div className="modal-card">
            <h3 className="modal-title">Create HR Login Account</h3>
            <p className="modal-desc">Create a new HR account with temporary login credentials.</p>

            {formError && <div className="error-banner">{formError}</div>}

            <form onSubmit={handleCreateSubmit}>
              <div className="form-group" style={{ marginBottom: 14 }}>
                <label style={{ display: 'block', marginBottom: 6, fontSize: '0.85rem' }}>Full Name</label>
                <input
                  type="text"
                  className="filter-select"
                  style={{ width: '100%' }}
                  value={createForm.full_name}
                  onChange={(e) => setCreateForm({ ...createForm, full_name: e.target.value })}
                  required
                />
              </div>

              <div className="form-group" style={{ marginBottom: 14 }}>
                <label style={{ display: 'block', marginBottom: 6, fontSize: '0.85rem' }}>Email Address</label>
                <input
                  type="email"
                  className="filter-select"
                  style={{ width: '100%' }}
                  value={createForm.email}
                  onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })}
                  required
                />
              </div>

              <div className="form-group" style={{ marginBottom: 14 }}>
                <label style={{ display: 'block', marginBottom: 6, fontSize: '0.85rem' }}>Temporary Password</label>
                <div style={{ position: 'relative' }}>
                  <input
                    type={showCreatePass ? 'text' : 'password'}
                    className="filter-select"
                    style={{ width: '100%', paddingRight: 36 }}
                    value={createForm.temporary_password}
                    onChange={(e) => setCreateForm({ ...createForm, temporary_password: e.target.value })}
                    required
                  />
                  <button
                    type="button"
                    style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}
                    onClick={() => setShowCreatePass(!showCreatePass)}
                  >
                    {showCreatePass ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              <div className="form-group" style={{ marginBottom: 14 }}>
                <label style={{ display: 'block', marginBottom: 6, fontSize: '0.85rem' }}>Confirm Temporary Password</label>
                <input
                  type={showCreatePass ? 'text' : 'password'}
                  className="filter-select"
                  style={{ width: '100%' }}
                  value={createForm.confirm_temporary_password}
                  onChange={(e) => setCreateForm({ ...createForm, confirm_temporary_password: e.target.value })}
                  required
                />
              </div>

              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowCreateModal(false)}>Cancel</button>
                <button type="submit" className="btn-primary" disabled={formLoading}>
                  {formLoading ? 'Creating...' : 'Create HR Account'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* RESET PASSWORD MODAL */}
      {showResetModal && targetHR && (
        <div className="modal-overlay">
          <div className="modal-card">
            <h3 className="modal-title">Reset HR Password</h3>
            <p className="modal-desc">Issue a new temporary password for <strong>{targetHR.email}</strong>.</p>

            {formError && <div className="error-banner">{formError}</div>}

            <form onSubmit={handleResetSubmit}>
              <div className="form-group" style={{ marginBottom: 14 }}>
                <label style={{ display: 'block', marginBottom: 6, fontSize: '0.85rem' }}>New Temporary Password</label>
                <div style={{ position: 'relative' }}>
                  <input
                    type={showResetPass ? 'text' : 'password'}
                    className="filter-select"
                    style={{ width: '100%', paddingRight: 36 }}
                    value={resetForm.temporary_password}
                    onChange={(e) => setResetForm({ ...resetForm, temporary_password: e.target.value })}
                    required
                  />
                  <button
                    type="button"
                    style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}
                    onClick={() => setShowResetPass(!showResetPass)}
                  >
                    {showResetPass ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              <div className="form-group" style={{ marginBottom: 14 }}>
                <label style={{ display: 'block', marginBottom: 6, fontSize: '0.85rem' }}>Confirm Temporary Password</label>
                <input
                  type={showResetPass ? 'text' : 'password'}
                  className="filter-select"
                  style={{ width: '100%' }}
                  value={resetForm.confirm_temporary_password}
                  onChange={(e) => setResetForm({ ...resetForm, confirm_temporary_password: e.target.value })}
                  required
                />
              </div>

              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowResetModal(false)}>Cancel</button>
                <button type="submit" className="btn-primary" disabled={formLoading}>
                  {formLoading ? 'Resetting...' : 'Reset Password'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminHRAccounts;
