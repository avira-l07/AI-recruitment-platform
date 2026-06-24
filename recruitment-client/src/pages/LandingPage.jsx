import React from 'react';
import { Link } from 'react-router-dom';

const LandingPage = () => {
  return (
    <div className="landing-page">
      <header className="hero-section">
        <div className="hero-content">
          <h1 style={{ fontSize: '3rem', marginBottom: '16px' }}>AI-Powered Recruitment Intelligence Platform</h1>
          <p style={{ fontSize: '1.2rem', marginBottom: '32px', opacity: 0.9 }}>
            Automate resume screening, job matching, and recruitment insights using AI.
          </p>
          <div style={{ display: 'flex', gap: '16px', justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link to="/login" className="btn-primary" style={{ backgroundColor: 'var(--sky)' }}>Candidate Login</Link>
            <Link to="/login" className="btn-primary" style={{ backgroundColor: 'var(--navy)' }}>HR Login</Link>
            <Link to="/register" className="btn-secondary" style={{ backgroundColor: 'transparent', color: 'white', borderColor: 'white' }}>Register</Link>
          </div>
        </div>
      </header>

      <section className="features-section page-container">
        <h2 style={{ textAlign: 'center', marginBottom: '40px', color: 'var(--navy)' }}>Why Choose RecruitAI?</h2>
        <div className="stats-grid">
          <div className="card">
            <h3>AI Resume Screening</h3>
            <p style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>Upload your resume and let AI extract your skills automatically.</p>
          </div>
          <div className="card">
            <h3>Smart Job Matching</h3>
            <p style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>Get matched with the best jobs based on your profile.</p>
          </div>
          <div className="card">
            <h3>HR Dashboard</h3>
            <p style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>Manage candidates, view rankings, and shortlist talent.</p>
          </div>
          <div className="card">
            <h3>Recruitment Analytics</h3>
            <p style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>Insights into your recruitment pipeline.</p>
          </div>
        </div>
      </section>

      <footer style={{ textAlign: 'center', padding: '40px', backgroundColor: 'var(--navy)', color: 'white', marginTop: 'auto' }}>
        <p>Built for smarter hiring. &copy; {new Date().getFullYear()} RecruitAI</p>
      </footer>
    </div>
  );
};

export default LandingPage;