import React, { useState, useEffect } from 'react';
import { Sparkles } from 'lucide-react';
import authService from '../../services/authService';
import jobService from '../../services/jobService';

// Custom reusable components
import ActionHeader from '../../components/ActionHeader';
import JobCard from '../../components/JobCard';
import EmptyState from '../../components/EmptyState';
import LoadingSkeleton from '../../components/LoadingSkeleton';
import ErrorState from '../../components/ErrorState';
import JobQuestionsModal from '../../components/prescreening/JobQuestionsModal';

const JobManagement = () => {
  const user = authService.getCurrentUser() || {};
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [creating, setCreating] = useState(false);
  const [success, setSuccess] = useState('');
  const [closingJobId, setClosingJobId] = useState(null);
  const [closeReason, setCloseReason] = useState('');
  const [selectedJobForQuestions, setSelectedJobForQuestions] = useState(null);

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    requiredSkills: '',
    experienceLevel: 'Entry',
    educationRequirement: '',
  });

  const fetchJobs = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await jobService.getAllJobs();
      setJobs(Array.isArray(res) ? res : []);
    } catch (err) {
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

    const payload = {
      ...formData,
      requiredSkills: formData.requiredSkills.split(',').map(s => s.trim()).filter(Boolean),
    };

    try {
      await jobService.createJob(payload, user.id);
      setSuccess('Job posting created successfully!');
      await fetchJobs();
      setFormData({ title: '', description: '', requiredSkills: '', experienceLevel: 'Entry', educationRequirement: '' });
    } catch (err) {
      setError('Failed to create job posting.');
    } finally {
      setCreating(false);
    }
  };

  const handleConfirmClose = async () => {
    if (!closeReason.trim()) return;
    try {
      await jobService.closeJob(closingJobId, closeReason.trim());
      setJobs(prev => prev.map(j => j.id === closingJobId ? { ...j, status: 'Closed', closed_reason: closeReason.trim() } : j));
      setClosingJobId(null);
      setCloseReason('');
    } catch (err) {
      setError('Failed to close job.');
    }
  };

  const handleReopen = async (jobId) => {
    try {
      await jobService.reopenJob(jobId);
      setJobs(prev => prev.map(j => j.id === jobId ? { ...j, status: 'Active', closed_reason: null } : j));
    } catch (err) {
      setError('Failed to reopen job.');
    }
  };

  if (loading) {
    return (
      <div className="hr-page">
        <ActionHeader title="Job Management" subtitle="Manage openings" />
        <LoadingSkeleton type="grid" count={2} />
      </div>
    );
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchJobs} />;
  }

  return (
    <div className="hr-page">
      <ActionHeader title="Job Management" subtitle="Configure and list corporate openings" />

      {/* Creation form */}
      <div style={{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-lg)', padding: 'var(--space-6)', marginBottom: 'var(--space-6)', boxShadow: 'var(--elevation-1)' }}>
        <h3 style={{ margin: '0 0 var(--space-4) 0', fontSize: 'var(--font-lg)' }}>Create New Job Posting</h3>
        {success && <p style={{ color: 'var(--color-success)', fontSize: 'var(--font-sm)', margin: '0 0 var(--space-3) 0' }}>{success}</p>}
        <form onSubmit={handleSubmit} style={{ display: 'grid', gap: 'var(--space-4)' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }}>
            <div>
              <label style={{ display: 'block', fontSize: 'var(--font-xs)', fontWeight: 'var(--weight-semibold)', marginBottom: '4px' }}>Job Title</label>
              <input type="text" name="title" required value={formData.title} onChange={handleChange} style={{ width: '100%', padding: '8px 12px', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', outline: 'none', boxSizing: 'border-box' }} />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 'var(--font-xs)', fontWeight: 'var(--weight-semibold)', marginBottom: '4px' }}>Required Skills (comma-separated)</label>
              <input type="text" name="requiredSkills" required placeholder="e.g. React, Node.js" value={formData.requiredSkills} onChange={handleChange} style={{ width: '100%', padding: '8px 12px', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', outline: 'none', boxSizing: 'border-box' }} />
            </div>
          </div>
          <div>
            <label style={{ display: 'block', fontSize: 'var(--font-xs)', fontWeight: 'var(--weight-semibold)', marginBottom: '4px' }}>Job Description</label>
            <textarea name="description" rows="3" required value={formData.description} onChange={handleChange} style={{ width: '100%', padding: '8px 12px', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', outline: 'none', boxSizing: 'border-box', fontFamily: 'inherit' }} />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }}>
            <div>
              <label style={{ display: 'block', fontSize: 'var(--font-xs)', fontWeight: 'var(--weight-semibold)', marginBottom: '4px' }}>Experience Level</label>
              <select name="experienceLevel" value={formData.experienceLevel} onChange={handleChange} style={{ width: '100%', padding: '8px 12px', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', outline: 'none', cursor: 'pointer', boxSizing: 'border-box' }}>
                <option value="Entry">Entry</option>
                <option value="Mid">Mid</option>
                <option value="Senior">Senior</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 'var(--font-xs)', fontWeight: 'var(--weight-semibold)', marginBottom: '4px' }}>Education</label>
              <input type="text" name="educationRequirement" required placeholder="e.g. Bachelors" value={formData.educationRequirement} onChange={handleChange} style={{ width: '100%', padding: '8px 12px', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', outline: 'none', boxSizing: 'border-box' }} />
            </div>
          </div>
          <button type="submit" style={{ justifySelf: 'start', backgroundColor: 'var(--color-primary)', color: '#fff', border: 'none', padding: '10px 24px', borderRadius: 'var(--radius-md)', fontWeight: 'var(--weight-semibold)', cursor: 'pointer' }}>
            {creating ? 'Creating...' : 'Create Posting'}
          </button>
        </form>
      </div>

      {/* Jobs grid */}
      <h3 style={{ margin: '0 0 var(--space-4) 0', fontSize: 'var(--font-lg)' }}>All Openings</h3>
      {jobs.length === 0 ? (
        <EmptyState message="No job postings available." subMessage="Create one using the form above." />
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 'var(--space-4)' }}>
          {jobs.map((job) => (
            <div key={job.id} style={{ display: 'flex', flexDirection: 'column', backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-lg)', padding: 'var(--space-5)', justifyContent: 'space-between', boxShadow: 'var(--elevation-1)' }}>
              <div>
                <span style={{ fontSize: '10px', backgroundColor: job.status === 'Closed' ? 'var(--color-danger-bg)' : 'var(--color-success-bg)', color: job.status === 'Closed' ? 'var(--color-danger)' : 'var(--color-success)', padding: '2px 8px', borderRadius: 'var(--radius-pill)', fontWeight: 'var(--weight-bold)', textTransform: 'uppercase', display: 'inline-block', marginBottom: '8px' }}>
                  {job.status || 'Active'}
                </span>
                <h4 style={{ margin: '0 0 var(--space-2) 0', fontSize: 'var(--font-base)', fontWeight: 'var(--weight-semibold)' }}>{job.title}</h4>
                <p style={{ margin: '0 0 var(--space-3) 0', fontSize: 'var(--font-xs)', color: 'var(--color-muted)', lineHeight: '1.4' }}>{job.description}</p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginBottom: 'var(--space-3)' }}>
                  {job.requiredSkills && job.requiredSkills.map(s => <span key={s} style={{ backgroundColor: 'var(--color-background)', fontSize: '10px', padding: '2px 8px', borderRadius: '4px' }}>{s}</span>)}
                </div>
              </div>
              <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: 'var(--space-3)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                <span style={{ fontSize: 'var(--font-xs)', color: 'var(--color-muted)' }}>Experience: <b>{job.experienceLevel}</b></span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <button 
                    onClick={() => setSelectedJobForQuestions(job)}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      backgroundColor: '#EFF6FF',
                      color: '#2563EB',
                      border: '1px solid #BFDBFE',
                      borderRadius: 'var(--radius-md)',
                      padding: '4px 10px',
                      fontSize: 'var(--font-xs)',
                      fontWeight: '600',
                      cursor: 'pointer'
                    }}
                    title="Configure AI Pre-Screening Questions"
                  >
                    <Sparkles size={12} />
                    <span>AI Pre-Screening</span>
                  </button>
                  {job.status === 'Closed' ? (
                    <button onClick={() => handleReopen(job.id)} style={{ border: '1px solid var(--color-border)', color: 'var(--color-text)', borderRadius: 'var(--radius-md)', padding: '4px 10px', fontSize: 'var(--font-xs)', cursor: 'pointer', background: 'none' }}>Reopen</button>
                  ) : (
                    <button onClick={() => setClosingJobId(job.id)} style={{ border: '1px solid var(--color-danger)', color: 'var(--color-danger)', borderRadius: 'var(--radius-md)', padding: '4px 10px', fontSize: 'var(--font-xs)', cursor: 'pointer', background: 'none' }}>Close</button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* AI Pre-Screening Questions Modal */}
      {selectedJobForQuestions && (
        <JobQuestionsModal
          isOpen={Boolean(selectedJobForQuestions)}
          onClose={() => setSelectedJobForQuestions(null)}
          job={selectedJobForQuestions}
        />
      )}

      {/* Close Modal */}
      {closingJobId && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(15, 23, 42, 0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 'var(--z-index-modal)' }}>
          <div style={{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-lg)', padding: 'var(--space-5)', maxWidth: '400px', width: '90%' }}>
            <h3 style={{ margin: '0 0 var(--space-2) 0' }}>Close Job Posting</h3>
            <p style={{ fontSize: 'var(--font-sm)', color: 'var(--color-muted)', margin: '0 0 var(--space-4) 0' }}>This will hide the posting from candidates. You can reopen it at any time.</p>
            <textarea placeholder="Reason (e.g. position filled)" value={closeReason} onChange={(e) => setCloseReason(e.target.value)} rows="3" style={{ width: '100%', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', padding: '8px', marginBottom: 'var(--space-4)', boxSizing: 'border-box' }} />
            <div style={{ display: 'flex', gap: 'var(--space-2)', justifyContent: 'flex-end' }}>
              <button onClick={() => setClosingJobId(null)} style={{ border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', padding: '6px 12px', cursor: 'pointer', background: 'none' }}>Cancel</button>
              <button onClick={handleConfirmClose} disabled={!closeReason.trim()} style={{ backgroundColor: 'var(--color-danger)', color: '#fff', border: 'none', borderRadius: 'var(--radius-md)', padding: '6px 16px', cursor: 'pointer' }}>Confirm Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default JobManagement;
