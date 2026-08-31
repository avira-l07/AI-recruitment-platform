import React, { useCallback, useEffect, useMemo, useState, useRef } from 'react';
import { 
  Users, 
  Briefcase, 
  BrainCircuit, 
  ClipboardCheck, 
  RefreshCw, 
  ChevronLeft, 
  ChevronRight, 
  Send, 
  MessageSquare, 
  Inbox,
  Sparkles,
  ShieldCheck,
  EyeOff
} from 'lucide-react';

import CandidateCard from '../../components/CandidateCard';
import AiSummaryDrawer from '../../components/AiSummaryDrawer';
import ResumeReviewDrawer from '../../components/ResumeReviewDrawer';
import ErrorState from '../../components/ErrorState';
import LoadingSkeleton from '../../components/LoadingSkeleton';
import ReviewAlert from '../../components/ReviewAlert';
import aiService from '../../services/aiService';
import analyticsService from '../../services/analyticsService';
import authService from '../../services/authService';
import matchingService from '../../services/matchingService';
import { useBlindScreening } from '../../context/BlindScreeningContext';
import './HRDashboard.css';

const normalizeSkills = (skills) => {
  if (!skills) return [];
  if (Array.isArray(skills)) return skills;
  return String(skills).split(',').map((skill) => skill.trim()).filter(Boolean);
};

const HRDashboard = () => {
  const currentUser = authService.getCurrentUser() || {};
  const displayName = currentUser.name || currentUser.fullName || currentUser.email || 'HR Manager';
  const { isBlindMode, toggleBlindMode } = useBlindScreening();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [warning, setWarning] = useState('');
  const [feedback, setFeedback] = useState('');

  // Datasets from API
  const [stats, setStats] = useState({});
  const [pipeline, setPipeline] = useState({});
  const [matches, setMatches] = useState([]);
  const [aiStatus, setAiStatus] = useState(null);

  // Selection & Details states
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [activeDrawer, setActiveDrawer] = useState(null); // 'ai-summary', 'resume-review', null
  const [drawerDetail, setDrawerDetail] = useState([]);
  const [drawerLoading, setDrawerLoading] = useState(false);
  const [drawerError, setDrawerError] = useState('');

  // Carousel & UI states
  const [currentCandidateIdx, setCurrentCandidateIdx] = useState(0);
  const [actionLoading, setActionLoading] = useState(false);

  // Ask RecruitAI chat states
  const [chatHistory, setChatHistory] = useState([
    {
      id: 'greeting',
      sender: 'assistant',
      text: "Hello! I'm your RecruitAI assistant. I can help you analyze candidates, compare skill sets, or optimize your job descriptions."
    }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);

  const chatEndRef = useRef(null);
  const refreshTimerRef = useRef(null);

  // Core data load utilizing Promise.allSettled
  const loadData = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    setError(null);
    setWarning('');

    const results = await Promise.allSettled([
      analyticsService.getOverview(),
      analyticsService.getPipeline(),
      matchingService.getAllMatches(),
      aiService.getStatus()
    ]);

    if (results[0].status === 'fulfilled') setStats(results[0].value || {});
    if (results[1].status === 'fulfilled') setPipeline(results[1].value || {});
    if (results[2].status === 'fulfilled') setMatches(Array.isArray(results[2].value) ? results[2].value : []);
    if (results[3].status === 'fulfilled') setAiStatus(results[3].value || {});

    const failed = results
      .map((result, index) => result.status === 'rejected' ? ['overview analytics', 'pipeline counts', 'candidate evaluations', 'AI engine status'][index] : null)
      .filter(Boolean);

    if (failed.length === results.length) {
      setError('The HR dashboard could not connect to the backend.');
    } else if (failed.length) {
      setWarning(`Dashboard warning: Some metrics are temporarily unavailable (${failed.join(', ')}).`);
    }

    if (!silent) setLoading(false);
  }, []);

  // optimistic status updates for candidates
  const updateStatus = async (id, status) => {
    setActionLoading(true);
    const previousMatches = matches;
    const previousPipeline = pipeline;

    // Optimistic UI updates
    setMatches((items) => items.map((item) => item.id === id ? { ...item, status } : item));
    setSelectedCandidate((item) => item?.id === id ? { ...item, status } : item);

    try {
      await matchingService.updateMatchStatus(id, status);
      setFeedback(`Application moved to ${status}.`);
      window.setTimeout(() => setFeedback(''), 3500);
      
      // Reload stats and pipeline counts in the background
      const [nextOverview, nextPipeline] = await Promise.all([
        analyticsService.getOverview(),
        analyticsService.getPipeline()
      ]);
      setStats(nextOverview);
      setPipeline(nextPipeline);
    } catch (err) {
      // Revert states on failure
      setMatches(previousMatches);
      setPipeline(previousPipeline);
      setSelectedCandidate((item) => item?.id === id ? { ...item, status: previousMatches.find(m => m.id === id)?.status } : item);
      setFeedback(err.response?.data?.detail || 'Status update failed. Previous state was restored.');
      window.setTimeout(() => setFeedback(''), 5000);
    } finally {
      setActionLoading(false);
    }
  };

  // Open details drawer
  const openAiSummary = async (candidate) => {
    setSelectedCandidate(candidate);
    setActiveDrawer('ai-summary');
    setDrawerDetail([]);
    setDrawerError('');
    setDrawerLoading(true);

    const userId = candidate.user_id || candidate.userId;
    if (!userId) {
      setDrawerError('Candidate profile mismatch.');
      setDrawerLoading(false);
      return;
    }

    try {
      const details = await matchingService.getCandidateMatches(userId);
      setDrawerDetail(details);
    } catch {
      setDrawerError('Detailed candidate evaluation is temporarily unavailable.');
    } finally {
      setDrawerLoading(false);
    }
  };

  const openResumeReview = (candidate) => {
    setSelectedCandidate(candidate);
    setActiveDrawer('resume-review');
  };

  const closeDrawer = () => {
    setSelectedCandidate(null);
    setActiveDrawer(null);
    setDrawerDetail([]);
    setDrawerError('');
    setDrawerLoading(false);
  };

  // Keyboard navigation for carousel
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (matches.length <= 1) return;
      if (e.key === 'ArrowLeft') {
        handlePrevCandidate();
      } else if (e.key === 'ArrowRight') {
        handleNextCandidate();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [matches.length]);

  // Debounced real-time SSE stream refresh
  const triggerDebouncedRefresh = useCallback(() => {
    if (refreshTimerRef.current) {
      clearTimeout(refreshTimerRef.current);
    }
    refreshTimerRef.current = setTimeout(() => {
      loadData(true);
    }, 500); // 500ms debounce window
  }, [loadData]);

  // Listen to window-level SSE realtime updates from layout
  useEffect(() => {
    loadData();

    const handleRealtimeBroadcast = (e) => {
      console.log("Dashboard SSE listener received event:", e.detail.event_type);
      triggerDebouncedRefresh();
    };

    const handleBlindToggle = () => {
      loadData(false);
    };

    window.addEventListener('hr-realtime-event', handleRealtimeBroadcast);
    window.addEventListener('blind-screening-toggled', handleBlindToggle);
    return () => {
      window.removeEventListener('hr-realtime-event', handleRealtimeBroadcast);
      window.removeEventListener('blind-screening-toggled', handleBlindToggle);
      if (refreshTimerRef.current) {
        clearTimeout(refreshTimerRef.current);
      }
    };
  }, [loadData, triggerDebouncedRefresh]);

  // Scroll chat widget to bottom
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatHistory]);

  const handleNextCandidate = () => {
    setCurrentCandidateIdx((prev) => (prev === matches.length - 1 ? 0 : prev + 1));
  };

  const handlePrevCandidate = () => {
    setCurrentCandidateIdx((prev) => (prev === 0 ? matches.length - 1 : prev - 1));
  };

  // Chat panel logic for Ask RecruitAI
  const sendAssistantMessage = async (messageText) => {
    if (!messageText.trim() || chatLoading) return;
    
    const userMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: messageText
    };

    setChatHistory(prev => [...prev, userMessage]);
    setChatInput('');
    setChatLoading(true);

    try {
      const response = await aiService.askRecruiter(messageText, conversationId);
      if (response) {
        if (response.conversation_id && !conversationId) {
          setConversationId(response.conversation_id);
        }
        
        let displaySource = 'LOCAL AI';
        if (response.source === 'hybrid') {
          displaySource = 'HYBRID';
        } else if (response.source === 'local_fallback') {
          displaySource = 'LOCAL FALLBACK';
        }

        const assistantMessage = {
          id: (Date.now() + 1).toString(),
          sender: 'assistant',
          text: response.answer,
          source: displaySource
        };
        setChatHistory(prev => [...prev, assistantMessage]);
      }
    } catch (err) {
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: 'The RecruitAI assistant is temporarily unavailable. Please try again shortly.'
      };
      setChatHistory(prev => [...prev, errorMessage]);
    } finally {
      setChatLoading(false);
    }
  };

  // Filter candidates waiting for manual review
  const manualReviewCandidates = useMemo(() => {
    return matches.filter(c => c.status === 'Manual Review');
  }, [matches]);

  const activeCandidateForCarousel = matches[currentCandidateIdx];

  if (loading) {
    return (
      <div className="hr-dashboard-container">
        <div className="hr-dashboard-header">
          <div className="hr-dashboard-welcome">
            <h1 style={{ width: '200px', height: '24px', backgroundColor: '#E2E5EC', borderRadius: '4px' }} className="animate-pulse"></h1>
          </div>
        </div>
        <LoadingSkeleton type="grid" count={3} />
      </div>
    );
  }

  if (error) {
    return <ErrorState message={error} onRetry={() => loadData()} />;
  }

  return (
    <div className="hr-dashboard-container">
      <div className="hr-dashboard-inner">
        {/* Welcome Section */}
      <div className="hr-dashboard-header">
        <div className="hr-dashboard-welcome">
          <h1>Welcome back, {displayName}</h1>
          <p>Live recruitment data and transparent AI status</p>
        </div>
        <button 
          onClick={() => loadData(false)} 
          className="hr-dashboard-refresh-btn"
          type="button"
        >
          <RefreshCw size={14} /> Refresh dashboard
        </button>
      </div>

      {/* Fair Review Active Mode Banner */}
      {isBlindMode && (
        <div className="hr-fair-review-banner">
          <div className="hr-fair-review-banner-left">
            <span className="hr-fair-review-banner-badge">
              <ShieldCheck size={13} /> Fair Review Mode Active
            </span>
            <p className="hr-fair-review-banner-desc">
              <b>Candidate identifying information is concealed.</b> Review candidates using skills, experience, projects, and job-fit analysis.
            </p>
          </div>
          <button type="button" onClick={toggleBlindMode} className="hr-fair-review-banner-btn">
            Exit Fair Review
          </button>
        </div>
      )}

      {/* Partial Data Warnings / Updates */}
      <div className="hr-dashboard-alerts">
        {warning && <ReviewAlert title="Partial data alert" message={warning} type="warning" />}
        {feedback && <ReviewAlert title="Update Status" message={feedback} type={feedback.includes('failed') ? 'warning' : 'success'} />}
        <ReviewAlert 
          title="AI safety notice" 
          message="AI recommendations are for decision support only. Final decisions require standard HR review." 
          type="warning" 
        />
      </div>

      {/* Top KPIs Metric Cards */}
      <div className="hr-dashboard-kpis">
        <div className="hr-kpi-card">
          <span className="hr-kpi-label">Job matches</span>
          <div className="hr-kpi-value blue">{matches.length}</div>
          <span className="hr-kpi-desc">Based on active database roles</span>
        </div>
        
        <div className="hr-kpi-card">
          <span className="hr-kpi-label">Shortlisted</span>
          <div className="hr-kpi-value green">{pipeline.shortlisted || 0}</div>
          <span className="hr-kpi-desc">Recruiter-approved fits</span>
        </div>

        <div className="hr-kpi-card">
          <span className="hr-kpi-label">Manual review</span>
          <div className="hr-kpi-value warning">{pipeline.manual_review || 0}</div>
          <span className="hr-kpi-desc">Awaiting recruiter feedback</span>
        </div>
      </div>

      {/* Top Matches & Evaluations Carousel */}
      <div className="hr-carousel-section">
        <div className="hr-carousel-header">
          <h3>Top matches & evaluations</h3>
          {matches.length > 0 && (
            <div className="hr-carousel-controls">
              <span className="hr-carousel-page-indicator">
                {currentCandidateIdx + 1} of {matches.length}
              </span>
              <div className="hr-carousel-nav-buttons">
                <button 
                  onClick={handlePrevCandidate} 
                  className="hr-carousel-nav-btn"
                  aria-label="Previous candidate"
                  type="button"
                >
                  <ChevronLeft size={16} />
                </button>
                <button 
                  onClick={handleNextCandidate} 
                  className="hr-carousel-nav-btn"
                  aria-label="Next candidate"
                  type="button"
                >
                  <ChevronRight size={16} />
                </button>
              </div>
            </div>
          )}
        </div>

        {matches.length === 0 ? (
          <p style={{ textAlign: 'center', color: '#74809A', padding: '24px 0', fontSize: '13px', margin: 0 }}>
            No evaluated candidates are available yet.
          </p>
        ) : (
          <CandidateCard 
            name={activeCandidateForCarousel.name}
            role={activeCandidateForCarousel.jobTitle}
            score={activeCandidateForCarousel.matchScore || 0}
            aiSource={activeCandidateForCarousel.aiSource}
            matchedSkills={normalizeSkills(activeCandidateForCarousel.matchedSkills)}
            missingSkills={normalizeSkills(activeCandidateForCarousel.missingSkills)}
            confidence={activeCandidateForCarousel.confidenceLabel}
            status={activeCandidateForCarousel.status}
            isBlindMode={isBlindMode}
            onAiSummary={() => openAiSummary(activeCandidateForCarousel)}
            onReview={() => openResumeReview(activeCandidateForCarousel)}
            onShortlist={() => updateStatus(activeCandidateForCarousel.id, 'Shortlisted')}
          />
        )}
      </div>

      {/* Ask AI & Manual Review Panel Grid */}
      <div className="hr-dashboard-bottom-grid">
        
        {/* Ask RecruitAI panel */}
        <div className="hr-ask-ai-panel">
          <div className="hr-ask-ai-header">
            <span className="hr-ask-ai-title">
              <MessageSquare size={16} style={{ color: '#00A83B' }} /> Ask RecruitAI
            </span>
            <span className="hr-ask-ai-status">Online</span>
          </div>

          <div className="hr-chat-history">
            {chatHistory.map((msg) => (
              <div key={msg.id} className={`hr-chat-message ${msg.sender}`}>
                {msg.text}
                {msg.source && (
                  <span className="hr-chat-source-badge">
                    <Sparkles size={8} style={{ display: 'inline', marginRight: '2px' }} /> {msg.source}
                  </span>
                )}
              </div>
            ))}
            {chatLoading && (
              <div className="hr-chat-message assistant">
                <span className="animate-pulse">Assistant is typing...</span>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Quick chips suggested prompts */}
          <div className="hr-chat-suggestions">
            <button 
              onClick={() => sendAssistantMessage("Analyze top candidate")} 
              className="hr-chat-suggested-btn"
              disabled={chatLoading}
              type="button"
            >
              Analyze top candidate
            </button>
            <button 
              onClick={() => sendAssistantMessage("Compare skills gap")} 
              className="hr-chat-suggested-btn"
              disabled={chatLoading}
              type="button"
            >
              Compare skills gap
            </button>
          </div>

          <div className="hr-chat-input-wrapper">
            <input 
              type="text" 
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') sendAssistantMessage(chatInput);
              }}
              placeholder="Ask anything about recruitment..."
              className="hr-chat-input"
              disabled={chatLoading}
            />
            <button 
              onClick={() => sendAssistantMessage(chatInput)} 
              className="hr-chat-send-btn"
              disabled={chatLoading || !chatInput.trim()}
              type="button"
            >
              <Send size={12} />
            </button>
          </div>
        </div>

        {/* Manual Review panel */}
        <div className="hr-manual-review-panel">
          <div className="hr-manual-review-header">
            <span className="hr-manual-review-title">
              <ClipboardCheck size={16} style={{ color: '#B96900' }} /> Manual review
            </span>
            <span className="hr-manual-review-count">
              {manualReviewCandidates.length}
            </span>
          </div>

          <div className="hr-manual-review-list">
            {manualReviewCandidates.length === 0 ? (
              <div className="hr-manual-review-empty">
                <div className="hr-manual-review-empty-icon">
                  <Inbox size={20} />
                </div>
                <p>No candidates awaiting review</p>
                <span>Awaiting an HR decision</span>
              </div>
            ) : (
              manualReviewCandidates.map(cand => (
                <div key={cand.id} className="hr-manual-review-item">
                  <div className="hr-manual-review-info">
                    <span className="hr-manual-review-cand-name">{cand.name}</span>
                    <span className="hr-manual-review-cand-job">{cand.jobTitle}</span>
                  </div>
                  <div className="hr-manual-review-right">
                    <span className="hr-manual-review-cand-score">{cand.matchScore}%</span>
                    <button 
                      onClick={() => openResumeReview(cand)} 
                      className="hr-manual-review-btn"
                      type="button"
                    >
                      Review
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="hr-manual-review-footer">
            Candidates appear here after AI analysis requires human review.
          </div>
        </div>

      </div>
      </div>

      {/* AI Summary Drawer */}
      <AiSummaryDrawer
        isOpen={activeDrawer === 'ai-summary'}
        onClose={closeDrawer}
        candidate={selectedCandidate}
        detail={drawerDetail}
        loading={drawerLoading}
        error={drawerError}
        isBlindMode={isBlindMode}
        onStatusUpdate={updateStatus}
        onRetry={() => selectedCandidate && openAiSummary(selectedCandidate)}
      />

      {/* Resume Review Drawer */}
      <ResumeReviewDrawer
        isOpen={activeDrawer === 'resume-review'}
        onClose={closeDrawer}
        applicationId={selectedCandidate?.application_id || selectedCandidate?.id}
        candidate={selectedCandidate}
        isBlindMode={isBlindMode}
        onStatusUpdate={updateStatus}
      />
    </div>
  );
};

export default HRDashboard;

