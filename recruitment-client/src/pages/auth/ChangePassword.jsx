import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Eye, EyeOff, Lock, CheckCircle2, XCircle } from 'lucide-react';
import authService from '../../services/authService';
import './ChangePassword.css';

const ChangePassword = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    current_password: '',
    new_password: '',
    confirm_new_password: '',
  });
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const newPass = formData.new_password;
  const rules = [
    { label: 'At least 10 characters', met: newPass.length >= 10 },
    { label: 'At least one uppercase letter', met: /[A-Z]/.test(newPass) },
    { label: 'At least one lowercase letter', met: /[a-z]/.test(newPass) },
    { label: 'At least one number', met: /[0-9]/.test(newPass) },
    { label: 'At least one special character', met: /[^A-Za-z0-9]/.test(newPass) },
  ];

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (formData.new_password !== formData.confirm_new_password) {
      setError('New password and confirmation do not match.');
      return;
    }

    const failedRule = rules.find((r) => !r.met);
    if (failedRule) {
      setError(`Password requirement failed: ${failedRule.label}`);
      return;
    }

    setLoading(true);
    try {
      const data = await authService.changePassword(
        formData.current_password,
        formData.new_password,
        formData.confirm_new_password
      );

      setFormData({ current_password: '', new_password: '', confirm_new_password: '' });

      const user = authService.getCurrentUser();
      const role = user?.role?.toLowerCase();

      if (role === 'admin') {
        navigate('/admin/hr-accounts');
      } else if (role === 'hr') {
        navigate('/hr/dashboard');
      } else {
        navigate('/candidate/dashboard');
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to change password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="change-password-container">
      <div className="change-password-card">
        <h2 className="change-password-title">Change Password Required</h2>
        <p className="change-password-subtitle">
          Please update your temporary password to secure your account before proceeding.
        </p>

        {error && <div className="error-banner">{error}</div>}

        <form onSubmit={handleSubmit} className="change-password-form">
          <div className="form-group">
            <label>Current / Temporary Password</label>
            <div className="password-input-wrap">
              <input
                type={showCurrent ? 'text' : 'password'}
                name="current_password"
                value={formData.current_password}
                onChange={handleChange}
                required
              />
              <button
                type="button"
                className="toggle-password-btn"
                onClick={() => setShowCurrent(!showCurrent)}
              >
                {showCurrent ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <div className="form-group">
            <label>New Password</label>
            <div className="password-input-wrap">
              <input
                type={showNew ? 'text' : 'password'}
                name="new_password"
                value={formData.new_password}
                onChange={handleChange}
                required
              />
              <button
                type="button"
                className="toggle-password-btn"
                onClick={() => setShowNew(!showNew)}
              >
                {showNew ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>

            {newPass.length > 0 && (
              <div className="password-strength-box">
                {rules.map((rule, idx) => (
                  <div key={idx} className={`strength-rule ${rule.met ? 'met' : ''}`}>
                    {rule.met ? <CheckCircle2 size={14} /> : <XCircle size={14} />}
                    <span>{rule.label}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="form-group">
            <label>Confirm New Password</label>
            <div className="password-input-wrap">
              <input
                type={showConfirm ? 'text' : 'password'}
                name="confirm_new_password"
                value={formData.confirm_new_password}
                onChange={handleChange}
                required
              />
              <button
                type="button"
                className="toggle-password-btn"
                onClick={() => setShowConfirm(!showConfirm)}
              >
                {showConfirm ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <button type="submit" className="change-password-btn" disabled={loading}>
            {loading ? 'Updating Password...' : 'Set New Password'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChangePassword;
