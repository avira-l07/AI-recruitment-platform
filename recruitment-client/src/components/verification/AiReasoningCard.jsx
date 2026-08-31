import React from 'react';
import { Sparkles, CheckCircle2, AlertTriangle, ShieldAlert, HelpCircle, MessageSquareQuote, FileQuestion } from 'lucide-react';

const AiReasoningCard = ({ aiReasoning = {} }) => {
  const verifiedFacts = aiReasoning.verified_facts || [];
  const supportingEvidence = aiReasoning.supporting_evidence || [];
  const missingEvidence = aiReasoning.missing_evidence || [];
  const contradictions = aiReasoning.contradictions || [];
  const hrQuestions = aiReasoning.hr_followup_questions || [];
  const interviewQuestions = aiReasoning.suggested_interview_questions || [];

  return (
    <div className="verif-card verif-card-ai">
      <div className="verif-card-header">
        <div className="verif-card-title-wrap">
          <Sparkles size={18} className="verif-ai-sparkle-icon" />
          <h3>RecruitAI Grounded Reasoning & Risk Analysis</h3>
        </div>
        <span className="verif-ai-source-pill">
          {aiReasoning.ai_source === 'gemini_grounded_trust' ? 'Gemini AI' : 'Hybrid Trust Engine'}
        </span>
      </div>

      {/* Summary Box */}
      {aiReasoning.summary && (
        <div className="verif-ai-summary-box">
          <p className="verif-ai-summary-text">{aiReasoning.summary}</p>
          {aiReasoning.risk_explanation && (
            <p className="verif-ai-risk-text">
              <strong>Risk Assessment:</strong> {aiReasoning.risk_explanation}
            </p>
          )}
        </div>
      )}

      <div className="verif-ai-grid">
        {/* Verified Facts */}
        <div className="verif-ai-column">
          <h4 className="verif-col-title verif-title-verified">
            <CheckCircle2 size={15} /> Verified Facts ({verifiedFacts.length})
          </h4>
          <ul className="verif-ai-list">
            {verifiedFacts.map((fact, idx) => (
              <li key={idx} className="verif-ai-item-verified">{fact}</li>
            ))}
          </ul>
        </div>

        {/* Missing Evidence / Gaps */}
        <div className="verif-ai-column">
          <h4 className="verif-col-title verif-title-missing">
            <HelpCircle size={15} /> Evidence Gaps to Confirm ({missingEvidence.length})
          </h4>
          <ul className="verif-ai-list">
            {missingEvidence.map((item, idx) => (
              <li key={idx} className="verif-ai-item-missing">{item}</li>
            ))}
          </ul>
        </div>
      </div>

      {/* Contradictions Alert if present */}
      {contradictions.length > 0 && (
        <div className="verif-alert-box verif-alert-danger" style={{ marginTop: '16px' }}>
          <ShieldAlert size={18} />
          <div>
            <strong>Identified Contradictions / Anomaly Signals ({contradictions.length}):</strong>
            <ul>
              {contradictions.map((c, idx) => (
                <li key={idx}>{c}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Suggested Interview Questions & HR Follow-ups */}
      {(interviewQuestions.length > 0 || hrQuestions.length > 0) && (
        <div className="verif-questions-section">
          <h4 className="verif-questions-title">
            <MessageSquareQuote size={16} /> Recommended Interview & HR Verification Questions
          </h4>
          
          <div className="verif-questions-grid">
            {interviewQuestions.map((q, idx) => (
              <div key={`int_${idx}`} className="verif-question-card">
                <div className="verif-q-top">
                  <FileQuestion size={14} className="verif-q-icon" />
                  <span className="verif-q-tag">Technical Deep-Dive</span>
                </div>
                <p className="verif-q-text">{q}</p>
              </div>
            ))}

            {hrQuestions.map((q, idx) => (
              <div key={`hr_${idx}`} className="verif-question-card">
                <div className="verif-q-top">
                  <HelpCircle size={14} className="verif-q-icon" />
                  <span className="verif-q-tag">HR Confirmation Check</span>
                </div>
                <p className="verif-q-text">{q}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AiReasoningCard;
