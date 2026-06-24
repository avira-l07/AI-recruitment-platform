import React, { useState, useEffect } from 'react';
import analyticsService from '../services/analyticsService';
import LoadingSpinner from '../components/LoadingSpinner';

const Analytics = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const res = await analyticsService.getOverview();
        setData(res);
      } catch (err) {
        console.error("Failed to load analytics", err);
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, []);

  if (loading) return <LoadingSpinner message="Loading analytics..." />;

  return (
    <div className="page-container">
      <div className="dashboard-header" style={{ marginBottom: '24px' }}>
        <h2>Analytics Overview</h2>
        <p className="text-secondary">Platform-wide recruitment metrics</p>
      </div>

      <div className="stats-grid">
        <div className="card stat-card" style={{ borderTop: '4px solid var(--sky)' }}>
          <div className="stat-card-header" style={{ display: 'flex', gap: '12px', marginBottom: '12px' }}>
            <div className="stat-icon" style={{ backgroundColor: '#eff6ff', color: 'var(--sky)', width: '32px', height: '32px', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: '8px' }}>👥</div>
            <h3 style={{ fontSize: '1rem', color: 'var(--text-secondary)' }}>Total Candidates</h3>
          </div>
          {/* FIXED: Defensive checking for both camelCase and snake_case */}
          <p style={{ fontSize: '2.5rem', fontWeight: 'bold' }}>
            {data?.total_candidates ?? data?.totalCandidates ?? 0}
          </p>
        </div>

        <div className="card stat-card" style={{ borderTop: '4px solid var(--navy)' }}>
          <div className="stat-card-header" style={{ display: 'flex', gap: '12px', marginBottom: '12px' }}>
            <div className="stat-icon" style={{ backgroundColor: '#f1f5f9', color: 'var(--navy)', width: '32px', height: '32px', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: '8px' }}>💼</div>
            <h3 style={{ fontSize: '1rem', color: 'var(--text-secondary)' }}>Total Jobs</h3>
          </div>
          <p style={{ fontSize: '2.5rem', fontWeight: 'bold' }}>
             {data?.total_jobs ?? data?.totalJobs ?? 0}
          </p>
        </div>

        <div className="card stat-card" style={{ borderTop: '4px solid var(--green)' }}>
          <div className="stat-card-header" style={{ display: 'flex', gap: '12px', marginBottom: '12px' }}>
            <div className="stat-icon" style={{ backgroundColor: '#f0fdf4', color: 'var(--green)', width: '32px', height: '32px', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: '8px' }}>✓</div>
            <h3 style={{ fontSize: '1rem', color: 'var(--text-secondary)' }}>Shortlisted</h3>
          </div>
          <p style={{ fontSize: '2.5rem', fontWeight: 'bold', color: 'var(--green)' }}>
             {data?.shortlisted_candidates ?? data?.shortlisted ?? 0}
          </p>
        </div>

        <div className="card stat-card" style={{ borderTop: '4px solid var(--red)' }}>
          <div className="stat-card-header" style={{ display: 'flex', gap: '12px', marginBottom: '12px' }}>
            <div className="stat-icon" style={{ backgroundColor: '#fef2f2', color: 'var(--red)', width: '32px', height: '32px', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: '8px' }}>✕</div>
            <h3 style={{ fontSize: '1rem', color: 'var(--text-secondary)' }}>Rejected</h3>
          </div>
          <p style={{ fontSize: '2.5rem', fontWeight: 'bold', color: 'var(--red)' }}>
             {data?.rejected_candidates ?? data?.rejected ?? 0}
          </p>
        </div>
      </div>
    </div>
  );
};

export default Analytics;