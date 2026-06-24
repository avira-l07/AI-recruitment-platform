import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import authService from '../services/authService';

const Navbar = () => {
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const user = authService.getCurrentUser();

  const handleLogout = () => {
    authService.logout();
    navigate('/');
  };

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-logo">RecruitAI</Link>
        
        <div className="hamburger" onClick={() => setMenuOpen(!menuOpen)}>
          ☰
        </div>

        <div className={`nav-links ${menuOpen ? 'active' : ''}`}>
          {user ? (
            <>
              <span className="nav-user">Hello, {user.fullName || user.name || 'User'}</span>
              <button className="btn-secondary" onClick={handleLogout}>Logout</button>
            </>
          ) : (
            <>
              <Link to="/login" className="btn-secondary">Login</Link>
              <Link to="/register" className="btn-primary">Register</Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;