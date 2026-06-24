import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import authService from '../services/authService';
import jobService from '../services/jobService';
import matchingService from '../services/matchingService';
import Sidebar from '../components/Sidebar';
import LoadingSpinner from '../components/LoadingSpinner';

const getFitLabel = (score) => {
  if (score >= 80) return 'Strong fit';
  if (score >= 65) return 'Good fit';
  return 'Possible fit';
};

const getFitClass = (score) => {
  if (score >= 80) return 'career-fit-strong';
  if (score >= 65) return 'career-fit-good';
  return 'career-fit-explore';
};

const BrowseJobs = () => {
  const navigate = useNavigate();
  const user = authService.getCurrentUser() || {};
  const userId = user?.id ?? user?.user_id ?? user?.candidate_id;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [applyingId, setApplyingId] = useState(null);
  const [appliedIds, setAppliedIds] = useState(new Set());
  const [applyError, setApplyError] = useState(null);

  const loadJobs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await jobService.getRecommendedJobs(userId);
      setJobs(Array.isArray(res) ? res : []);
    } catch (err) {
      console.error('Failed to load recommended jobs', err);
      if (err.response?.status === 401) {
        navigate('/login');
        return;
      }
      if (err.response?.status === 404) {
        // No candidate profile or no resume yet - not a server error, just nothing to show.
        setJobs([]);
      } else {
        setError(err.response?.data?.detail || 'Could not load job recommendations right now.');
      }
    } finally {
      setLoading(false);
    }
  }, [userId, navigate]);

  useEffect(() => {
    if (userId) loadJobs();
    else setLoading(false);
  }, [userId, loadJobs]);

  const handleLogout = async () => {
    try {
      if (authService?.logout) await authService.logout();
      else localStorage.clear();
    } catch {
      localStorage.clear();
    }
    navigate('/login');
  };

  const handleApply = async (jobId) => {
    setApplyingId(jobId);
    setApplyError(null);
    try {
      await matchingService.applyToJob(userId, jobId);
      setAppliedIds(prev => new Set(prev).add(jobId));
    } catch (err) {
      console.error('Failed to apply', err);
      setApplyError(err.response?.data?.detail || 'Could not submit your application. Please try again.');
    } finally {
      setApplyingId(null);
    }
  };

  if (loading) return <LoadingSpinner message="Finding jobs that fit your resume..." />;

  return (
    <div className="candidate-shell">
      <Sidebar role="candidate" active="jobs" user={user} onLogout={handleLogout} />

      <main className="candidate-main">
        <div className="candidate-page">

          <header className="candidate-header">
            <div>
              <h1 className="candidate-title">Jobs for you</h1>
              <p className="candidate-subtitle">Roles that match at least half of your resume skills</p>
            </div>
            <button type="button" className="candidate-update-btn" onClick={loadJobs}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 4 23 10 17 10"></polyline><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path></svg>
              Refresh
            </button>
          </header>

          {error && (
            <div className="candidate-empty-card" style={{ marginBottom: '20px', borderStyle: 'solid', borderColor: 'var(--candidate-red)' }}>
              <p style={{ color: 'var(--candidate-red)', margin: '0 0 12px 0' }}>{error}</p>
              <button className="candidate-update-btn" onClick={loadJobs}>Try again</button>
            </div>
          )}

          {applyError && (
            <div style={{ background: 'var(--candidate-red-bg)', color: 'var(--candidate-red)', padding: '12px 16px', borderRadius: '8px', marginBottom: '20px', fontSize: '0.9rem' }}>
              {applyError}
            </div>
          )}

          {!error && jobs.length === 0 && (
            <div className="candidate-empty-card">
              <p style={{ margin: 0 }}>
                No jobs match your resume well enough yet (we only show roles at 50% fit or higher).
                Update your resume or check back as new roles open up.
              </p>
            </div>
          )}

          {!error && jobs.length > 0 && (
            <div className="career-suggestions-card">
              <div className="career-card-header" style={{ marginBottom: '16px' }}>
                <h2 className="resume-section-title" style={{ margin: 0 }}>{jobs.length} matching role{jobs.length !== 1 ? 's' : ''}</h2>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {jobs.map((job) => {
                  const score = Math.max(0, Math.min(100, job.score || 0));
                  const hasApplied = appliedIds.has(job.job_id);
                  const isApplying = applyingId === job.job_id;

                  return (
                    <div key={job.job_id} className="career-card">
                      <div className="career-card-header">
                        <h3 className="career-title">{job.title}</h3>
                        <span className={`career-score-badge ${getFitClass(score)}`}>
                          {getFitLabel(score)} · {score}%
                        </span>
                      </div>

                      <div className="career-progress">
                        <div
                          className="career-progress-fill"
                          style={{
                            width: `${score}%`,
                            backgroundColor: score >= 80 ? 'var(--candidate-green)' : score >= 65 ? 'var(--candidate-amber)' : 'var(--candidate-muted)'
                          }}
                        />
                      </div>

                      {job.description && <p className="career-description">{job.description}</p>}

                      <div style={{ display: 'flex', gap: '16px', fontSize: '0.85rem', color: 'var(--candidate-muted)', marginBottom: '14px' }}>
                        {job.experience_level && <span>Experience: {job.experience_level}</span>}
                        {job.education_requirement && <span>Education: {job.education_requirement}</span>}
                      </div>

                      <div className="career-chip-row" style={{ marginBottom: '16px' }}>
                        {(job.matched_skills || []).map(s => (
                          <span key={`m-${s}`} className="career-matched-chip">{s}</span>
                        ))}
                        {(job.missing_skills || []).map(s => (
                          <span key={`x-${s}`} className="career-recommended-chip">{s}</span>
                        ))}
                      </div>

                      <button
                        type="button"
                        className="candidate-update-btn"
                        disabled={hasApplied || isApplying}
                        onClick={() => handleApply(job.job_id)}
                        style={hasApplied ? { background: 'var(--candidate-green)' } : undefined}
                      >
                        {hasApplied ? '✓ Applied' : isApplying ? 'Applying...' : 'Apply'}
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

        </div>
      </main>
    </div>
  );
};

export default BrowseJobs;
