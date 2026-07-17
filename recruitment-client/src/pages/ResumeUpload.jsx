import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import authService from '../services/authService';
import resumeService from '../services/resumeService';
import LoadingSpinner from '../components/LoadingSpinner';

const ResumeUpload = () => {
  const navigate = useNavigate();
  const user = authService.getCurrentUser() || {};
  const userId = user?.id ?? user?.user_id;

  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [parsedData, setParsedData] = useState(null);
  const [quality, setQuality] = useState(null);
  const [aiInsights, setAiInsights] = useState(null);

  const handleFileChange = (e) => {
    const selected = e.target.files?.[0];
    setError('');
    setSuccess('');
    setParsedData(null);
    setQuality(null);
    setAiInsights(null);

    if (!selected) return;
    const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    const validExt = selected.name.toLowerCase().endsWith('.pdf') || selected.name.toLowerCase().endsWith('.docx');
    if (!validTypes.includes(selected.type) && !validExt) {
      setFile(null);
      setError('Only PDF and DOCX resume files are allowed.');
      return;
    }
    if (selected.size > 5 * 1024 * 1024) {
      setFile(null);
      setError('File is too large. Maximum allowed size is 5 MB.');
      return;
    }
    if (selected.size < 200) {
      setFile(null);
      setError('File is too small. Upload a complete resume, not only a few words.');
      return;
    }
    setFile(selected);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!userId) {
      setError('User ID is missing. Please logout and login again.');
      return;
    }
    if (!file) {
      setError('Please select a valid resume file first.');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const data = await resumeService.uploadResume(userId, file);
      setParsedData(data.parsedResult || null);
      setQuality(data.resumeQuality || data.parsedResult?.quality || null);
      setAiInsights(data.aiInsights || data.parsedResult?.ai_insights || null);
      setSuccess('Resume uploaded, validated, and analyzed successfully.');
    } catch (err) {
      setError(err.message || 'Failed to upload resume. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <LoadingSpinner message="Validating and analyzing your resume with AI..." />;

  const errorLines = error ? error.split('\n').filter(Boolean) : [];

  return (
    <div className="page-container">
      <div className="card" style={{ maxWidth: '820px', margin: '0 auto' }}>
        <h2 style={{ marginBottom: '10px' }}>Upload Your Resume</h2>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '20px' }}>
          The platform accepts only complete professional resumes. Empty/fake PDFs like only “Java SQL” will be rejected.
        </p>

        <div style={{ background: '#F8FAFC', border: '1px solid var(--border)', borderRadius: '12px', padding: '16px', marginBottom: '20px' }}>
          <strong>Professional resume checks:</strong>
          <ul style={{ margin: '10px 0 0 18px', color: 'var(--text-secondary)', lineHeight: 1.7 }}>
            <li>Name and contact signal</li>
            <li>Enough readable text</li>
            <li>Education, projects, experience, or certification section</li>
            <li>Real skill evidence, not only random keywords</li>
          </ul>
        </div>

        <form onSubmit={handleUpload}>
          <div className="form-group">
            <label>Select Resume File</label>
            <input type="file" accept=".pdf,.docx" onChange={handleFileChange} />
            {file && <p style={{ marginTop: '8px', color: 'var(--text-secondary)' }}>Selected: {file.name}</p>}
          </div>

          {error && (
            <div style={{ backgroundColor: '#FEECEC', border: '1px solid #FCA5A5', color: '#991B1B', padding: '14px', borderRadius: '10px', marginBottom: '16px' }}>
              <strong>Resume rejected / upload failed</strong>
              <ul style={{ margin: '8px 0 0 18px', lineHeight: 1.6 }}>
                {errorLines.map((line, idx) => <li key={idx}>{line}</li>)}
              </ul>
            </div>
          )}

          {success && <div className="alert alert-success" style={{ marginBottom: '16px' }}>{success}</div>}

          <button type="submit" className="btn-primary" disabled={loading || !file} style={{ width: '100%' }}>
            Validate Resume + Generate AI Insights
          </button>
        </form>

        {quality && (
          <div className="card" style={{ marginTop: '24px', background: '#F8FAFC' }}>
            <h3>Resume Quality Check</h3>
            <p style={{ fontSize: '1.8rem', fontWeight: 700, margin: '8px 0' }}>{quality.quality_score}%</p>
            <p style={{ color: quality.accepted ? '#166534' : '#991B1B', fontWeight: 600 }}>
              {quality.accepted ? 'Accepted for matching' : 'Not accepted'}
            </p>
            {quality.reasons?.length > 0 && (
              <ul style={{ color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                {quality.reasons.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            )}
          </div>
        )}

        {aiInsights && (
          <div className="card" style={{ marginTop: '20px' }}>
            <h3>AI Resume Review</h3>
            <p style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>{aiInsights.candidateSummary}</p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px', marginTop: '16px' }}>
              <div>
                <strong>Strengths</strong>
                <ul>{(aiInsights.strengths || []).map((x, i) => <li key={i}>{x}</li>)}</ul>
              </div>
              <div>
                <strong>Improve</strong>
                <ul>{(aiInsights.resumeImprovementTips || []).map((x, i) => <li key={i}>{x}</li>)}</ul>
              </div>
            </div>
          </div>
        )}

        {parsedData && (
          <div className="card" style={{ marginTop: '20px' }}>
            <h3>Parsed Resume Data</h3>
            <p><strong>Name:</strong> {parsedData.name || 'Not found'}</p>
            <p><strong>Email:</strong> {parsedData.email || 'Not found'}</p>
            <p><strong>Phone:</strong> {parsedData.phone || 'Not found'}</p>
            <p><strong>Education:</strong> {parsedData.education || 'Not specified'}</p>
            <p><strong>Skills:</strong></p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {(parsedData.skills || []).map((skill, idx) => <span key={idx} className="skill-tag">{skill}</span>)}
            </div>
            <button type="button" className="btn-secondary" style={{ marginTop: '20px' }} onClick={() => navigate('/candidate/dashboard')}>
              Go to Dashboard
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ResumeUpload;
