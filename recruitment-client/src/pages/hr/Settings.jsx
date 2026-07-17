import React from 'react';

const Settings = () => {
  return (
    <div className="hr-page">
      <header className="hr-header">
        <div>
          <h1 className="hr-title">Settings</h1>
          <p className="hr-subtitle">RecruitAI System Configurations</p>
        </div>
      </header>

      <div className="hr-rankings-card" style={{ padding: '24px', textAlign: 'center' }}>
        <p style={{ fontSize: '1.1rem', fontWeight: '500', color: 'var(--hr-text)', marginBottom: '8px' }}>
          Settings functionality will be added in a future phase.
        </p>
        <p style={{ color: 'var(--hr-muted)', fontSize: '0.95rem' }}>
          Configuring active engines, models, and scoring preferences is currently disabled.
        </p>
      </div>
    </div>
  );
};

export default Settings;
