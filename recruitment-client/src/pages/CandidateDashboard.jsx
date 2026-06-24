import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import authService from '../services/authService';
import resumeService from '../services/resumeService';
import matchingService from '../services/matchingService';
import Sidebar from '../components/Sidebar';
import LoadingSpinner from '../components/LoadingSpinner';
import ScoreBadge from '../components/ScoreBadge';

const CandidateDashboard = () => {
  const navigate = useNavigate();
  const user = authService.getCurrentUser() || {};
  const userId = user?.id ?? user?.user_id ?? user?.candidate_id;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [resumeData, setResumeData] = useState(null);
  const [matches, setMatches] = useState([]);
  
  const [sideTab, setSideTab] = useState('dashboard');
  const [careerSuggestions, setCareerSuggestions] = useState([]);
  const [careerSource, setCareerSource] = useState("");
  const [careerLoading, setCareerLoading] = useState(false);

  const normalizeList = (value) => {
    if (!value) return [];
    if (Array.isArray(value)) return value;
    if (typeof value === 'string') {
      const trimmed = value.trim();
      if (trimmed.startsWith('[')) {
        try {
          const parsed = JSON.parse(trimmed);
          if (Array.isArray(parsed)) return parsed;
        } catch (e) { /* fallback */ }
      }
      return trimmed.split(',').map(s => s.trim()).filter(Boolean);
    }
    return [];
  };

  const buildLocalCareerSuggestions = (skillsStr) => {
    const userSkills = normalizeList(skillsStr).map(s => s.toLowerCase());
    const predefined = [
      { field: "AI/ML Intern", skills: ["python", "machine learning", "artificial intelligence", "generative ai", "nlp", "pandas", "numpy", "scikit-learn"] },
      { field: "Software Developer", skills: ["c", "c++", "java", "python", "dsa", "oop", "git", "github"] },
      { field: "Data Analyst", skills: ["python", "sql", "pandas", "numpy", "data analysis", "excel", "visualization"] },
      { field: "Backend Developer", skills: ["python", "fastapi", "django", "flask", "sql", "postgresql", "mongodb", "rest api"] },
      { field: "Frontend Developer", skills: ["react", "javascript", "html", "css", "tailwind css", "bootstrap", "rest api"] }
    ];

    const suggestions = predefined.map(job => {
      const matchedSkills = job.skills.filter(req => userSkills.some(userSk => userSk.includes(req) || req.includes(userSk)));
      const recommendedSkills = job.skills.filter(req => !matchedSkills.includes(req));
      const fitScore = Math.round((matchedSkills.length / job.skills.length) * 100) || 0;

      let fitLabel = "Explore";
      if (fitScore >= 80) fitLabel = "Strong Fit";
      else if (fitScore >= 50) fitLabel = "Good Fit";

      const capitalize = (str) => str.replace(/\b\w/g, l => l.toUpperCase());

      return {
        career_field: job.field,
        fit_score: fitScore,
        fit_label: fitLabel,
        matched_skills: matchedSkills.map(capitalize),
        recommended_skills: recommendedSkills.map(capitalize),
        reason: matchedSkills.length > 0 ? `Based on your resume, you have ${matchedSkills.length} matching skills.` : `Consider learning foundational skills.`,
        description: `Explore opportunities as a ${job.field}.`
      };
    });

    return suggestions.sort((a, b) => b.fit_score - a.fit_score).slice(0, 4);
  };

  useEffect(() => {
    if (!userId) {
      setLoading(false);
      return;
    }

    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        let currentResumeData = null;

        try {
          const resumeRes = await resumeService.getResume(userId);
          setResumeData(resumeRes);
          currentResumeData = resumeRes;
        } catch (resumeErr) {
          if (resumeErr.response?.status === 404) setResumeData(null); 
          else throw resumeErr; 
        }

        const matchRes = await matchingService.getCandidateMatches(userId);
        setMatches(matchRes || []);

        if (currentResumeData) {
          setCareerLoading(true);
          try {
            const careerRes = await resumeService.getCareerSuggestions(userId);
            if (careerRes && careerRes.suggestions) {
              setCareerSuggestions(careerRes.suggestions.slice(0, 4));
              setCareerSource(careerRes.source || 'claude'); 
            } else {
              setCareerSuggestions(buildLocalCareerSuggestions(currentResumeData.skills));
              setCareerSource("local_fallback");
            }
          } catch (careerErr) {
            console.warn("Career suggestions API failed, using local fallback.", careerErr);
            setCareerSuggestions(buildLocalCareerSuggestions(currentResumeData.skills));
            setCareerSource("local_fallback");
          } finally {
            setCareerLoading(false);
          }
        }
      } catch (err) {
        console.error("API Error in Candidate Dashboard:", err);
        if (err.response?.status === 401) {
          navigate('/login');
          return;
        }
        setError(err.response?.data?.detail || 'Could not connect to the server.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [userId, navigate]);

  const handleLogout = async () => {
    try {
      if (authService?.logout) await authService.logout();
      else localStorage.clear();
    } catch {
      localStorage.clear();
    }
    navigate('/login');
  };

  const getFitBadgeClass = (score) => {
    if (score >= 80) return 'career-fit-strong';
    if (score >= 50) return 'career-fit-good';
    return 'career-fit-explore';
  };

  const getProgressColor = (score) => {
    if (score >= 80) return 'var(--candidate-green)';
    if (score >= 50) return 'var(--candidate-amber)';
    return 'var(--candidate-muted)';
  };

  const getStatusPillClass = (status) => {
    const s = (status || '').toLowerCase();
    if (s === 'shortlisted') return 'resume-status-pill shortlisted';
    if (s === 'rejected') return 'resume-status-pill rejected';
    if (s === 'pending') return 'resume-status-pill pending';
    return 'resume-status-pill default';
  };

  const matchList = matches || [];
  const shortlistedCount = matchList.filter(m => (m.status || '').toLowerCase() === 'shortlisted').length;
  const pendingCount = matchList.filter(m => (m.status || '').toLowerCase() === 'pending').length;
  const skills = normalizeList(resumeData?.skills);

  if (loading) return <LoadingSpinner message="Loading your candidate portal..." />;

  if (error) {
    return (
      <div className="candidate-shell">
        <Sidebar role="candidate" active={sideTab} onSelect={setSideTab} user={user} onLogout={handleLogout} />
        <main className="candidate-main">
          <div className="candidate-page" style={{ display: 'flex', justifyContent: 'center', paddingTop: '10vh' }}>
            <div className="candidate-empty-card" style={{ maxWidth: '500px', borderColor: '#FCA5A5', backgroundColor: '#FEECEC' }}>
              <h2 style={{ color: '#991B1B', marginBottom: '12px' }}>Connection Error</h2>
              <p style={{ color: '#B91C1C', marginBottom: '24px' }}>{error}</p>
              <button className="candidate-update-btn" onClick={() => window.location.reload()}>↻ Refresh Page</button>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="candidate-shell">
      <Sidebar role="candidate" active={sideTab} onSelect={setSideTab} user={user} onLogout={handleLogout} />
      
      <main className="candidate-main">
        <div className="candidate-page">
          
          {sideTab === 'dashboard' && (
            <>
              <header className="candidate-header">
                <div>
                  <h1 className="candidate-title">Welcome, {user.name || user.fullName || 'Candidate'}</h1>
                  <p className="candidate-subtitle">Track your job matches and explore AI career suggestions</p>
                </div>
                <button type="button" className="candidate-update-btn" onClick={() => navigate('/candidate/upload')}>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
                  Update resume
                </button>
              </header>

              <div className="candidate-stats-grid">
                <div className="candidate-stat-card">
                  <p className="candidate-stat-label">Job matches</p>
                  <p className="candidate-stat-value">{matchList.length}</p>
                </div>
                <div className="candidate-stat-card">
                  <p className="candidate-stat-label">Shortlisted</p>
                  <p className="candidate-stat-value" style={{ color: 'var(--candidate-green)' }}>{shortlistedCount}</p>
                </div>
                <div className="candidate-stat-card">
                  <p className="candidate-stat-label">Pending review</p>
                  <p className="candidate-stat-value" style={{ color: 'var(--candidate-amber)' }}>{pendingCount}</p>
                </div>
              </div>

              <div className="candidate-overview-grid">
                <div className="resume-profile-card">
                  <h2 style={{ fontSize: '1.1rem', margin: '0 0 16px 0', color: 'var(--candidate-text)' }}>Resume profile</h2>
                  
                  {resumeData ? (
                    <div>
                      <div className="resume-status-pill success" style={{ marginBottom: '24px' }}>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="20 6 9 17 4 12"></polyline></svg>
                        Resume uploaded and parsed
                      </div>

                      <div style={{ marginBottom: '20px' }}>
                        <p className="resume-section-label">SKILLS</p>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                          {skills.length > 0 ? (
                            skills.map((s, i) => <span key={i} className="candidate-skill-chip">{s}</span>)
                          ) : (
                            <span style={{ color: 'var(--candidate-muted)', fontSize: '0.9rem' }}>No skills listed</span>
                          )}
                        </div>
                      </div>

                      <div style={{ marginBottom: '20px' }}>
                        <p className="resume-section-label">EDUCATION</p>
                        <p style={{ margin: 0, fontSize: '0.95rem', lineHeight: '1.4' }}>{resumeData.education || 'Not specified'}</p>
                      </div>

                      <div style={{ marginBottom: '24px' }}>
                        <p className="resume-section-label">EXPERIENCE</p>
                        <p style={{ margin: 0, fontSize: '0.95rem', lineHeight: '1.5' }}>{resumeData.experience || 'Not specified'}</p>
                      </div>

                      <button type="button" className="candidate-update-btn" style={{ width: '100%', justifyContent: 'center', backgroundColor: 'transparent', color: 'var(--candidate-text)', border: '1px solid var(--candidate-border)' }} onClick={() => navigate('/candidate/upload')}>
                        Update resume
                      </button>
                    </div>
                  ) : (
                    <div className="candidate-empty-card">
                      <p>No resume uploaded yet. Upload your resume to unlock AI insights.</p>
                      <button className="candidate-update-btn" style={{ marginTop: '16px' }} onClick={() => navigate('/candidate/upload')}>Upload Resume</button>
                    </div>
                  )}
                </div>

                <div className="career-suggestions-card">
                  <div className="career-card-header" style={{ marginBottom: '20px' }}>
                    <h2 style={{ fontSize: '1.1rem', margin: 0, color: 'var(--candidate-text)' }}>Career field suggestions</h2>
                    <span style={{ fontSize: '0.85rem', color: 'var(--candidate-muted)' }}>
                      {careerSource === 'claude' || careerSource === 'gemini' ? 'Powered by Claude AI' : 'Based on your resume skills'}
                    </span>
                  </div>

                  {careerLoading ? (
                    <LoadingSpinner message="Analyzing career fits..." />
                  ) : careerSuggestions && careerSuggestions.length > 0 ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                      {careerSuggestions.map((sug, idx) => {
                        const score = Math.max(0, Math.min(100, sug.fit_score || sug.fitScore || 0));
                        const fitLabel = sug.fit_label || sug.fitLabel || 'Explore';
                        
                        return (
                          <div key={idx} className="career-card">
                            <div className="career-card-header">
                              <h3 className="career-title">{sug.career_field || sug.careerField}</h3>
                              <span className={`career-score-badge ${getFitBadgeClass(score)}`}>
                                {fitLabel} · {score}%
                              </span>
                            </div>
                            
                            <div className="career-progress">
                              <div className="career-progress-fill" style={{ width: `${score}%`, backgroundColor: getProgressColor(score) }} />
                            </div>
                            
                            {sug.description && <p className="career-description">{sug.description}</p>}
                            
                            <div className="career-chip-row">
                              {(sug.matched_skills || sug.matchedSkills || []).map((sk, i) => (
                                <span key={`match-${i}`} className="career-matched-chip">{sk}</span>
                              ))}
                              {(sug.recommended_skills || sug.recommendedSkills || []).map((sk, i) => (
                                <span key={`rec-${i}`} className="career-recommended-chip">{sk}</span>
                              ))}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="candidate-empty-card">
                      <p>No career suggestions available. Update your resume to explore paths.</p>
                    </div>
                  )}
                </div>
              </div>
            </>
          )}

          {sideTab === 'matches' && (
            <div className="candidate-matches-view">
              <h2 style={{ fontSize: '1.25rem', marginBottom: '24px', color: 'var(--candidate-text)' }}>My official job matches</h2>
              
              {matchList.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {matchList.map((match) => {
                    const score = Math.max(0, Math.min(100, match.matchScore ?? match.score ?? match.match_score ?? 0));
                    const missingSkills = normalizeList(match.missingSkills ?? match.missing_skills);
                    const matchedSkills = normalizeList(match.matchedSkills ?? match.matched_skills);

                    return (
                      <div key={match.id ?? `match-${match.jobTitle}`} className="candidate-match-card">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                          <div>
                            <h3 style={{ margin: '0 0 4px 0', fontSize: '1.15rem', color: 'var(--candidate-text)' }}>
                              {match.jobTitle || match.title || match.matchedJob || 'Untitled Role'}
                            </h3>
                            {match.company && <p style={{ margin: 0, color: 'var(--candidate-muted)', fontSize: '0.9rem' }}>{match.company}</p>}
                          </div>
                          <ScoreBadge score={score} />
                        </div>

                        <div className="career-progress" style={{ marginBottom: '16px' }}>
                          <div className="career-progress-fill" style={{ width: `${score}%`, backgroundColor: getProgressColor(score) }} />
                        </div>

                        {match.explanation && <p style={{ fontSize: '0.95rem', color: 'var(--candidate-muted)', marginBottom: '16px', lineHeight: '1.5' }}>{match.explanation}</p>}

                        <div className="career-chip-row" style={{ marginBottom: '16px' }}>
                           {matchedSkills.map(sk => <span key={`m-${sk}`} className="career-matched-chip">{sk}</span>)}
                           {missingSkills.map(sk => <span key={`miss-${sk}`} className="career-recommended-chip">{sk}</span>)}
                        </div>

                        <span className={getStatusPillClass(match.status)}>{match.status || 'Pending'}</span>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="candidate-empty-card">
                  <div style={{ fontSize: '2.5rem', marginBottom: '16px' }}>💼</div>
                  <p>No official job matches have been generated yet. Your career suggestions are available on the Dashboard tab.</p>
                </div>
              )}
            </div>
          )}

          {sideTab === 'notifications' && (
            <div>
              <h2 style={{ fontSize: '1.25rem', marginBottom: '24px', color: 'var(--candidate-text)' }}>Notifications</h2>
              <div className="candidate-empty-card">
                <div style={{ fontSize: '2.5rem', marginBottom: '16px' }}>🔔</div>
                <p>No notifications yet. Updates about shortlisted jobs and interview status will appear here.</p>
              </div>
            </div>
          )}

        </div>
      </main>
    </div>
  );
};

export default CandidateDashboard;