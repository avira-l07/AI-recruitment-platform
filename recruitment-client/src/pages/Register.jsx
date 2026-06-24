import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import authService from '../services/authService';

const Register = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    role: 'candidate'
  });
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await authService.register(formData.name, formData.email, formData.password, formData.role);
      navigate('/login');
    } catch (err) {
      setError(err.message || 'Registration failed');
    }
  };

  return (
    <div className="page-container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
      <div className="card" style={{ width: '100%', maxWidth: '400px' }}>
        <h2 style={{ textAlign: 'center', marginBottom: '24px' }}>Create an Account</h2>
        
        {error && <div style={{ color: 'var(--red)', marginBottom: '16px', textAlign: 'center' }}>{error}</div>}
        
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '16px' }}>
            <label className="form-label">Full Name</label>
            <input type="text" name="name" className="form-input" value={formData.name} onChange={handleChange} required />
          </div>
          
          <div style={{ marginBottom: '16px' }}>
            <label className="form-label">Email Address</label>
            <input type="email" name="email" className="form-input" value={formData.email} onChange={handleChange} required />
          </div>
          
          <div style={{ marginBottom: '16px' }}>
            <label className="form-label">Password</label>
            <input type="password" name="password" className="form-input" value={formData.password} onChange={handleChange} required />
          </div>
          
          <div style={{ marginBottom: '24px' }}>
            <label className="form-label">Role</label>
            {/* FIXED: Added value prop to make this a controlled component */}
            <select name="role" className="form-input" value={formData.role} onChange={handleChange} required>
              <option value="candidate">Candidate</option>
              <option value="hr">HR Professional</option>
            </select>
          </div>
          
          <button type="submit" className="btn-primary" style={{ width: '100%', marginBottom: '16px' }}>Register</button>
        </form>
        
        <p style={{ textAlign: 'center', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
          Already have an account? <Link to="/login" style={{ color: 'var(--sky)', fontWeight: 'bold' }}>Log in here</Link>
        </p>
      </div>
    </div>
  );
};

export default Register;