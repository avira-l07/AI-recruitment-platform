import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import authService from '../services/authService';
import { Sparkles } from 'lucide-react';
import '../pages/LandingPage.css';

const Navbar = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const currentUser = user !== undefined ? user : authService.getCurrentUser();

  const handleLogout = () => {
    if (onLogout) {
      onLogout();
    } else {
      authService.logout();
      navigate('/');
    }
  };

  return (
    <nav className="ra-nav">
      <Link to="/" className="ra-logo">
        <span className="ra-logo-mark"><Sparkles size={14} color="#fff" /></span>
        <span className="ra-display">RecruitAI</span>
      </Link>
      
      <div className="ra-nav-links">
        <a href="#product">Product</a>
        <a href="#candidates">For Candidates</a>
        <a href="#employers">For Employers</a>
        <a href="#analytics">Analytics</a>
      </div>

      <div className="ra-nav-actions">
        {currentUser ? (
          <>
            <span className="nav-user" style={{ color: '#fff', fontSize: '14px', marginRight: '10px', display: 'inline-flex', alignItems: 'center' }}>
              Hello, {currentUser.fullName || currentUser.name || 'User'}
            </span>
            <button className="ra-btn ra-btn-ghost-dark" onClick={handleLogout}>Logout</button>
          </>
        ) : (
          <>
            <Link to="/login" className="ra-btn ra-btn-ghost-dark">Login</Link>
            <Link to="/register" className="ra-btn ra-btn-solid-amber">Register</Link>
          </>
        )}
      </div>
    </nav>
  );
};

export default Navbar;

