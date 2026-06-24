import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import authService from '../services/authService';

const Login = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    role: 'candidate'
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Calls the backend to authenticate
      await authService.login(formData.email, formData.password, formData.role);
      
      // If successful, navigate to the correct dashboard
      if (formData.role === 'hr') {
        navigate('/hr/dashboard');
      } else {
        navigate('/candidate/dashboard');
      }
    } catch (err) {
      console.error('Login failed:', err);
      // Display the actual error from the backend instead of failing silently
      setError(err.response?.data?.detail || err.message || 'Invalid email or password. Please try again.');
    } finally {
      // THIS GUARANTEES THE BUTTON RESETS EVEN IF LOGIN FAILS
      setLoading(false);
    }
  };

  return (
    <div className="page-container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
      <div className="card" style={{ width: '100%', maxWidth: '400px' }}>
        <h2 style={{ textAlign: 'center', marginBottom: '24px' }}>Welcome Back</h2>
        
        {/* The error banner will now correctly display if auth fails */}
        {error && (
          <div style={{ color: '#991b1b', marginBottom: '16px', textAlign: 'center', padding: '12px', backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: '6px' }}>
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '16px' }}>
            <label className="form-label">Email</label>
            <input 
              type="email" 
              name="email" 
              className="form-input" 
              value={formData.email} 
              onChange={handleChange} 
              required 
              disabled={loading}
            />
          </div>
          
          <div style={{ marginBottom: '16px' }}>
            <label className="form-label">Password</label>
            <input 
              type="password" 
              name="password" 
              className="form-input" 
              value={formData.password} 
              onChange={handleChange} 
              required 
              disabled={loading}
            />
          </div>
          
          <div style={{ marginBottom: '24px' }}>
            <label className="form-label">Role</label>
            <select 
              name="role" 
              className="form-input" 
              value={formData.role} 
              onChange={handleChange} 
              disabled={loading}
            >
              <option value="candidate">Candidate</option>
              <option value="hr">HR Professional</option>
            </select>
          </div>
          
          <button 
            type="submit" 
            className="btn-primary" 
            style={{ width: '100%', marginBottom: '16px' }} 
            disabled={loading}
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>
        
        <p style={{ textAlign: 'center', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
          Don't have an account? <Link to="/register" style={{ color: 'var(--sky)', fontWeight: 'bold' }}>Register</Link>
        </p>
      </div>
    </div>
  );
};

export default Login;