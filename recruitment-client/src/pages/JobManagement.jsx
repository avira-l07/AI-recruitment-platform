import React, { useState, useEffect } from 'react';
import authService from '../services/authService';
import jobService from '../services/jobService';
import JobCard from '../components/JobCard';
import LoadingSpinner from '../components/LoadingSpinner';

const JobManagement = () => {
  const user = authService.getCurrentUser() || {};

  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [creating, setCreating] = useState(false);
  const [success, setSuccess] = useState('');

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    requiredSkills: '',
    experienceLevel: 'Entry',
    educationRequirement: '',
  });

  const [closingJobId, setClosingJobId] = useState(null);
  const [closeReason, setCloseReason] = useState('');
  const [closeSubmitting, setCloseSubmitting] = useState(false);

  const fetchJobs = async () => {
    setLoading(true);
    setError(null);

    try {
      const res = await jobService.getAllJobs();
      setJobs(Array.isArray(res) ? res : []);
    } catch (err) {
      console.error('Failed to load jobs', err);
      setError(err.response?.data?.detail || 'Failed to load jobs from the server.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setCreating(true);
    setSuccess('');
    setError(null);

    if (!user.id) {
      setError('User ID not found. Please logout and login again.');
      setCreating(false);
      return;
    }

    const payload = {
      ...formData,
      requiredSkills: formData.requiredSkills
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean),
    };

    try {
      await jobService.createJob(payload, user.id);

      setSuccess('Job created successfully!');
      await fetchJobs();

      setFormData({
        title: '',
        description: '',
        requiredSkills: '',
        experienceLevel: 'Entry',
        educationRequirement: '',
      });
    } catch (err) {
      console.error('Failed to create job', err);
      setError(err.response?.data?.detail || 'Failed to create job. Please try again.');
    } finally {
      setCreating(false);
    }
  };

  const openCloseModal = (jobId) => {
    setClosingJobId(jobId);
    setCloseReason('');
  };

  const cancelCloseModal = () => {
    setClosingJobId(null);
    setCloseReason('');
  };

  const handleConfirmClose = async () => {
    if (!closeReason.trim()) return;

    setCloseSubmitting(true);
    setError(null);

    try {
      await jobService.closeJob(closingJobId, closeReason.trim());

      setJobs((prev) =>
        prev.map((j) =>
          j.id === closingJobId
            ? {
                ...j,
                status: 'Closed',
                closed_reason: closeReason.trim(),
                closed_at: new Date().toISOString(),
              }
            : j
        )
      );

      setClosingJobId(null);
      setCloseReason('');
    } catch (err) {
      console.error('Failed to close job', err);
      setError(err.response?.data?.detail || 'Failed to close job. Please try again.');
    } finally {
      setCloseSubmitting(false);
    }
  };

  const handleReopen = async (jobId) => {
    setError(null);

    try {
      await jobService.reopenJob(jobId);

      setJobs((prev) =>
        prev.map((j) =>
          j.id === jobId
            ? {
                ...j,
                status: 'Active',
                closed_reason: null,
                closed_at: null,
              }
            : j
        )
      );
    } catch (err) {
      console.error('Failed to reopen job', err);
      setError(err.response?.data?.detail || 'Failed to reopen job. Please try again.');
    }
  };

  return (
    <div className="page-container">
      <h1 style={{ marginBottom: '24px', color: 'var(--navy)' }}>
        Job Management
      </h1>

      <div className="card" style={{ marginBottom: '32px' }}>
        <h2 style={{ marginBottom: '16px' }}>Create New Job</h2>

        {success && (
          <p style={{ color: 'var(--green)', marginBottom: '16px' }}>
            {success}
          </p>
        )}

        {error && (
          <p style={{ color: 'var(--red)', marginBottom: '16px' }}>
            {error}
          </p>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'grid', gap: '16px' }}>
          <div>
            <label className="form-label">Job Title</label>
            <input
              type="text"
              name="title"
              className="form-input"
              required
              value={formData.title}
              onChange={handleChange}
            />
          </div>

          <div>
            <label className="form-label">Job Description</label>
            <textarea
              name="description"
              className="form-input"
              rows="4"
              required
              value={formData.description}
              onChange={handleChange}
            />
          </div>

          <div>
            <label className="form-label">Required Skills comma-separated</label>
            <input
              type="text"
              name="requiredSkills"
              className="form-input"
              required
              placeholder="e.g. React, Node.js, Python"
              value={formData.requiredSkills}
              onChange={handleChange}
            />
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '16px',
            }}
          >
            <div>
              <label className="form-label">Experience Level</label>
              <select
                name="experienceLevel"
                className="form-input"
                value={formData.experienceLevel}
                onChange={handleChange}
              >
                <option value="Entry">Entry</option>
                <option value="Mid">Mid</option>
                <option value="Senior">Senior</option>
              </select>
            </div>

            <div>
              <label className="form-label">Education Requirement</label>
              <input
                type="text"
                name="educationRequirement"
                className="form-input"
                required
                placeholder="e.g. Bachelors"
                value={formData.educationRequirement}
                onChange={handleChange}
              />
            </div>
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={creating}
            style={{ justifySelf: 'start' }}
          >
            {creating ? 'Creating...' : 'Create Job'}
          </button>
        </form>
      </div>

      <h2 style={{ marginBottom: '16px' }}>All Jobs</h2>

      {loading ? (
        <LoadingSpinner />
      ) : error ? (
        <div className="card" style={{ textAlign: 'center', padding: '32px' }}>
          <p style={{ color: 'var(--red)', marginBottom: '16px' }}>{error}</p>
          <button className="btn-secondary" onClick={fetchJobs}>
            ↻ Try Again
          </button>
        </div>
      ) : jobs.length === 0 ? (
        <div
          className="card"
          style={{
            textAlign: 'center',
            padding: '32px',
            color: 'var(--text-secondary)',
          }}
        >
          No jobs created yet.
        </div>
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
            gap: '16px',
          }}
        >
          {jobs.map((job) => (
            <div key={job.id} style={{ position: 'relative' }}>
              <JobCard job={job} />

              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginTop: '8px',
                  padding: '0 4px',
                }}
              >
                <span
                  style={{
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    color: job.status === 'Closed' ? 'var(--red)' : 'var(--green)',
                  }}
                >
                  {job.status === 'Closed'
                    ? `Closed${job.closed_reason ? `: ${job.closed_reason}` : ''}`
                    : 'Active'}
                </span>

                {job.status === 'Closed' ? (
                  <button
                    className="btn-secondary"
                    style={{ padding: '4px 10px', fontSize: '0.8rem' }}
                    onClick={() => handleReopen(job.id)}
                  >
                    Reopen
                  </button>
                ) : (
                  <button
                    className="btn-secondary"
                    style={{ padding: '4px 10px', fontSize: '0.8rem' }}
                    onClick={() => openCloseModal(job.id)}
                  >
                    Close
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {closingJobId && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 500,
          }}
        >
          <div className="card" style={{ maxWidth: '420px', width: '90%' }}>
            <h3 style={{ marginBottom: '12px' }}>Close this job?</h3>

            <p
              style={{
                color: 'var(--text-secondary)',
                marginBottom: '12px',
                fontSize: '0.9rem',
              }}
            >
              This hides the job from candidates. You can reopen it later.
            </p>

            <label className="form-label">Reason</label>

            <textarea
              className="form-input"
              rows="3"
              placeholder="e.g. Position filled"
              value={closeReason}
              onChange={(e) => setCloseReason(e.target.value)}
              style={{ marginBottom: '16px' }}
            />

            <div
              style={{
                display: 'flex',
                gap: '12px',
                justifyContent: 'flex-end',
              }}
            >
              <button
                className="btn-secondary"
                onClick={cancelCloseModal}
                disabled={closeSubmitting}
              >
                Cancel
              </button>

              <button
                className="btn-primary"
                onClick={handleConfirmClose}
                disabled={closeSubmitting || !closeReason.trim()}
              >
                {closeSubmitting ? 'Closing...' : 'Confirm Close'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default JobManagement;