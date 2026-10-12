import React, { useState, useEffect } from 'react';
import { X, Send, Sparkles, AlertCircle, HelpCircle, CheckCircle2, Loader2, Layers } from 'lucide-react';
import './CandidatePrescreeningModal.css';

const CandidatePrescreeningModal = ({ isOpen, onClose, job, questions = [], onSubmit, isSubmitting = false }) => {
  const [answers, setAnswers] = useState({});
  const [error, setError] = useState('');
  useEffect(() => {
    setAnswers({});
    setError('');
  }, [job?.id, isOpen]);

  if (!isOpen || !job) return null;

  const handleAnswerChange = (questionId, text) => {
    setAnswers(prev => ({ ...prev, [questionId]: text }));
    if (error) setError('');
  };

  const handleFormSubmit = (e) => {
    e.preventDefault();
    
    // Validate required questions
    for (const q of questions) {
      if (q.is_required && (!answers[q.id] || !answers[q.id].trim())) {
        setError(`Please answer Question ${q.order_index + 1}: "${q.question_text.substring(0, 50)}..."`);
        return;
      }
    }

    const payloadAnswers = questions.filter(q => answers[q.id]?.trim()).map(q => ({
      question_id: q.id,
      question_text: q.question_text,
      answer_text: answers[q.id] || ''
    }));

    onSubmit(payloadAnswers);
  };

  return (
    <div className="cand-ps-overlay" onClick={onClose}>
      <div className="cand-ps-content" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="cand-ps-header">
          <div className="cand-ps-header-left">
            <div className="cand-ps-icon-wrap">
              <Sparkles size={20} className="cand-ps-icon" />
            </div>
            <div>
              <h3 className="cand-ps-title">Role Pre-Screening Assessment</h3>
              <span className="cand-ps-sub">Applying for: <strong>{job.title}</strong></span>
            </div>
          </div>

          <button className="cand-ps-close-btn" onClick={onClose} disabled={isSubmitting}>
            <X size={20} />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleFormSubmit} className="cand-ps-form">
          <div className="cand-ps-body">
            <div className="cand-ps-intro">
              <p>
                Please provide concise, practical answers to the following role-specific questions. Your responses will be evaluated alongside your resume qualifications.
              </p>
            </div>

            {error && (
              <div className="cand-ps-alert">
                <AlertCircle size={16} />
                <span>{error}</span>
              </div>
            )}

            <div className="cand-ps-q-list">
              {questions.map((q, idx) => {
                const currentAnswer = answers[q.id] || '';
                const wordCount = currentAnswer.trim() ? currentAnswer.trim().split(/\s+/).length : 0;

                return (
                  <div key={q.id || idx} className="cand-ps-q-item">
                    <div className="cand-ps-q-top">
                      <div className="cand-ps-q-title-wrap">
                        <span className="cand-ps-q-num">Question {idx + 1}</span>
                        <span className="cand-ps-type-pill">{q.question_type || 'technical'}</span>
                      </div>
                      {q.is_required && <span className="cand-ps-req-tag">* Required</span>}
                    </div>

                    <h4 className="cand-ps-q-prompt">{q.question_text}</h4>

                    <textarea
                      className="cand-ps-textarea"
                      rows="4"
                      maxLength={10000}
                      required={q.is_required}
                      disabled={isSubmitting}
                      placeholder="Type your structured explanation and practical approach here..."
                      value={currentAnswer}
                      onChange={(e) => handleAnswerChange(q.id, e.target.value)}
                    />

                    <div className="cand-ps-q-footer">
                      <span className="cand-ps-word-count">{wordCount} words</span>
                      {wordCount >= 30 && (
                        <span className="cand-ps-good-length">
                          <CheckCircle2 size={12} /> Good response depth
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Footer Actions */}
          <div className="cand-ps-footer">
            <button 
              type="button" 
              className="cand-ps-btn-cancel" 
              onClick={onClose}
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button 
              type="submit" 
              className="cand-ps-btn-submit"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="cand-ps-spin" size={15} />
                  <span>Submitting & Evaluating...</span>
                </>
              ) : (
                <>
                  <Send size={15} />
                  <span>Submit Application</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CandidatePrescreeningModal;
