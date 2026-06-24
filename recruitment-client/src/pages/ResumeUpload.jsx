import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import authService from '../services/authService';
import resumeService from '../services/resumeService';
import LoadingSpinner from '../components/LoadingSpinner';

const ResumeUpload = () => {
  const navigate = useNavigate();
  const user = authService.getCurrentUser() || {};
  
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [parsedData, setParsedData] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a file first.');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const data = await resumeService.uploadResume(user.id, file);
      setParsedData(data.parsedResult);
      setSuccess('Resume uploaded and processed successfully!');
    } catch (err) {
      console.error('Upload failed:', err);
      setError(err.message || 'Failed to upload resume. Please try again.');
      // FIXED: Removed the early return here.
    } finally {
      // FIXED: Loading state is guaranteed to reset now.
      setLoading(false);
    }
  };

  if (loading) return <LoadingSpinner message="Parsing your resume..." />;

  return (
    <div className="page-container">
      <div className="card" style={{ maxWidth: '600px', margin: '0 auto' }}>
        <h2 style={{ marginBottom: '16px' }}>Upload Your Resume</h2>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>
          Our AI will analyze your resume to find the best job matches for you.
        </p>

        {error && <div style={{ color: 'var(--red)', marginBottom: '16px', padding: '12px', backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: '6px' }}>{error}</div>}
        {success && <div style={{ color: 'var(--green)', marginBottom: '16px', padding: '12px', backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '6px' }}>{success}</div>}

        <form onSubmit={handleUpload}>
          <div style={{ marginBottom: '24px' }}>
            <input 
              type="file" 
              accept=".pdf,.doc,.docx" 
              onChange={handleFileChange} 
              className="form-input"
            />
          </div>
          <div style={{ display: 'flex', gap: '12px' }}>
            <button type="submit" className="btn-primary">Upload & Parse</button>
            <button type="button" className="btn-secondary" onClick={() => navigate('/candidate/dashboard')}>Back to Dashboard</button>
          </div>
        </form>

        {parsedData && (
          <div style={{ marginTop: '32px', paddingTop: '24px', borderTop: '1px solid var(--border)' }}>
            <h3>Successfully Extracted Skills</h3>
            <div style={{ marginTop: '12px', display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {parsedData.skills?.map(skill => (
                <span key={skill} className="skill-tag">{skill}</span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ResumeUpload;