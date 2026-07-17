import React, { useState, useEffect } from 'react';
import analyticsService from '../../services/analyticsService';

// Custom reusable components
import ActionHeader from '../../components/ActionHeader';
import StatisticsCard from '../../components/StatisticsCard';
import LoadingSkeleton from '../../components/LoadingSkeleton';
import ErrorState from '../../components/ErrorState';

const Analytics = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await analyticsService.getOverview();
      setData(res);
    } catch (err) {
      setError('Failed to load recruitment metrics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="hr-page">
        <ActionHeader title="Analytics Overview" subtitle="Platform-wide recruitment metrics" />
        <LoadingSkeleton type="grid" count={4} />
      </div>
    );
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchAnalytics} />;
  }

  const totalCandidates = data?.total_candidates ?? data?.totalCandidates ?? 0;
  const totalJobs = data?.total_jobs ?? data?.totalJobs ?? 0;
  const shortlisted = data?.shortlisted_candidates ?? data?.shortlisted ?? 0;
  const rejected = data?.rejected_candidates ?? data?.rejected ?? 0;

  return (
    <div className="hr-page">
      <ActionHeader title="Analytics Overview" subtitle="Platform-wide recruitment metrics" />

      <div 
        style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', 
          gap: 'var(--space-4)', 
          marginTop: 'var(--space-4)' 
        }}
      >
        <StatisticsCard 
          label="Total Candidates" 
          value={totalCandidates} 
          iconBgClass="hr-icon-blue" 
          helperText="Total applicants in database"
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle></svg>}
        />
        <StatisticsCard 
          label="Total Jobs" 
          value={totalJobs} 
          iconBgClass="hr-icon-muted" 
          helperText="Active job postings"
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>}
        />
        <StatisticsCard 
          label="Shortlisted" 
          value={shortlisted} 
          iconBgClass="hr-icon-green" 
          trendColor="green"
          helperText={`${totalCandidates > 0 ? Math.round((shortlisted / totalCandidates) * 100) : 0}% shortlisting rate`}
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>}
        />
        <StatisticsCard 
          label="Rejected" 
          value={rejected} 
          iconBgClass="hr-icon-red" 
          trendColor="red"
          helperText="Unmatched skills/experience"
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>}
        />
      </div>
    </div>
  );
};

export default Analytics;
