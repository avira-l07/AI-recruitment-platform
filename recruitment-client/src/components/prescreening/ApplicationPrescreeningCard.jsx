import React, { useState, useEffect } from 'react';
import { 
  Sparkles, CheckCircle2, AlertTriangle, HelpCircle, MessageSquareQuote, 
  Layers, ChevronDown, ChevronUp, Loader2, Award 
} from 'lucide-react';
import prescreeningService from '../../services/prescreeningService';
import './ApplicationPrescreeningCard.css';

const getLabelBadgeClass = (label) => {
  switch (label) {
    case 'Strong':
      return 'ps-badge-strong';
    case 'Competent':
      return 'ps-badge-competent';
    case 'Developing':
      return 'ps-badge-developing';
    case 'Needs Review':
    default:
      return 'ps-badge-review';
  }
};

const ApplicationPrescreeningCard = ({ applicationId, isBlindMode = false }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expandedIndex, setExpandedIndex] = useState(null);

  useEffect(() => {
    if (applicationId) {
      loadEvaluation();
    }
  }, [applicationId, isBlindMode]);

  const loadEvaluation = async () => {
    setLoading(true);
    try {
      const res = await prescreeningService.getApplicationEvaluation(applicationId);
      setData(res);
    } catch (err) {
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="ps-card-loading">
        <Loader2 className="ps-spin" size={20} />
        <span>Loading pre-screening assessment...</span>
      </div>
    );
  }

  if (!data || !data.has_evaluation) {
    return null; // Don't display card if no pre-screening was answered
  }

  const evaluations = data.evaluations || [];
  const score = Math.round(data.overall_score || 0);

  return (
    <div className="ps-eval-card">
      <div className="ps-eval-header">
        <div className="ps-eval-title-wrap">
          <Sparkles size={18} className="ps-eval-icon" />
          <div>
            <h3 className="ps-eval-heading">Role Pre-Screening Assessment</h3>
            <span className="ps-eval-sub">AI Candidate Questionnaire Evaluation</span>
          </div>
        </div>

        <div className="ps-eval-score-pill-wrap">
          <span className={`ps-label-pill ${getLabelBadgeClass(data.overall_label)}`}>
            {data.overall_label || 'Competent'}
          </span>
          <div className="ps-score-badge">
            <span className="ps-score-val">{score}</span>
            <span className="ps-score-max">/ 100</span>
          </div>
        </div>
      </div>

      {/* Summary Box */}
      {data.summary && (
        <div className="ps-eval-summary-box">
          <p className="ps-eval-summary-text">{data.summary}</p>
          {data.strengths_summary && (
            <p className="ps-eval-strengths">
              <strong>Demonstrated Strengths:</strong> {data.strengths_summary}
            </p>
          )}
          {data.gap_summary && (
            <p className="ps-eval-gaps">
              <strong>Interview Discussion Areas:</strong> {data.gap_summary}
            </p>
          )}
        </div>
      )}

      {/* Per-Question Evaluations List */}
      <div className="ps-eval-q-list">
        <h4 className="ps-eval-section-title">Question Responses & Detailed Analysis ({evaluations.length})</h4>
        {evaluations.map((ev, idx) => {
          const isExpanded = expandedIndex === idx;

          return (
            <div key={idx} className="ps-eval-item">
              <div 
                className="ps-eval-item-top"
                onClick={() => setExpandedIndex(isExpanded ? null : idx)}
              >
                <div className="ps-eval-item-info">
                  <span className="ps-item-num">Q{idx + 1} ({ev.question_type})</span>
                  <h5 className="ps-item-title">{ev.question_text}</h5>
                </div>

                <div className="ps-eval-item-right">
                  <span className="ps-item-score" style={{ color: ev.score >= 70 ? '#10B981' : (ev.score >= 50 ? '#F59E0B' : '#EF4444') }}>
                    {Math.round(ev.score)}/100
                  </span>
                  {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </div>
              </div>

              {isExpanded && (
                <div className="ps-eval-item-body">
                  {/* Candidate Written Answer */}
                  <div className="ps-answer-box">
                    <span className="ps-answer-lbl">Candidate Response:</span>
                    <p className="ps-answer-text">"{ev.candidate_answer || 'No response provided.'}"</p>
                  </div>

                  {/* AI Feedback */}
                  {ev.feedback && (
                    <div className="ps-feedback-box">
                      <span className="ps-feedback-lbl">AI Evaluation:</span>
                      <p className="ps-feedback-text">{ev.feedback}</p>
                    </div>
                  )}

                  {/* Key Strengths & Gaps */}
                  <div className="ps-tags-grid">
                    {ev.key_strengths && ev.key_strengths.length > 0 && (
                      <div>
                        <span className="ps-tags-lbl ps-lbl-strength">Covered Concepts:</span>
                        <div className="ps-pills-row">
                          {ev.key_strengths.map((st, sIdx) => (
                            <span key={sIdx} className="ps-pill ps-pill-green">{st}</span>
                          ))}
                        </div>
                      </div>
                    )}

                    {ev.missing_concepts && ev.missing_concepts.length > 0 && (
                      <div>
                        <span className="ps-tags-lbl ps-lbl-gap">Missing / Unmentioned:</span>
                        <div className="ps-pills-row">
                          {ev.missing_concepts.map((g, gIdx) => (
                            <span key={gIdx} className="ps-pill ps-pill-amber">{g}</span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ApplicationPrescreeningCard;
