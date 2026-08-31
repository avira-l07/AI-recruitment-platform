import React, { useState, useEffect } from 'react';
import { 
  X, Sparkles, Plus, Trash2, HelpCircle, Save, CheckCircle2, 
  AlertCircle, Eye, EyeOff, Loader2, BookOpen, Layers, CheckSquare 
} from 'lucide-react';
import prescreeningService from '../../services/prescreeningService';
import './JobQuestionsModal.css';

const QUESTION_TYPES = [
  { value: 'technical', label: 'Technical Concept / Architecture' },
  { value: 'scenario', label: 'Production Scenario / Scaling' },
  { value: 'practical', label: 'Practical Project Experience' },
  { value: 'problem_solving', label: 'Problem Solving & Debugging' }
];

const JobQuestionsModal = ({ isOpen, onClose, job }) => {
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [previewMode, setPreviewMode] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    if (isOpen && job?.id) {
      loadQuestions();
    }
  }, [isOpen, job?.id]);

  const loadQuestions = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await prescreeningService.getJobQuestions(job.id);
      setQuestions(Array.isArray(data) ? data : []);
    } catch (err) {
      setError('Failed to load pre-screening questions.');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    setGenerating(true);
    setError('');
    try {
      const generated = await prescreeningService.generateQuestions(job.id, false);
      setQuestions(generated);
      setSuccess('AI generated role-specific questions successfully. Review and save below.');
      setTimeout(() => setSuccess(''), 4000);
    } catch (err) {
      setError('Failed to generate questions using AI.');
    } finally {
      setGenerating(false);
    }
  };

  const handleAddQuestion = () => {
    const newQ = {
      id: Date.now(),
      question_text: '',
      question_type: 'technical',
      category: 'Technical Skills',
      scoring_criteria: '',
      expected_concepts: [],
      weight: 1.0,
      is_required: true,
      order_index: questions.length
    };
    setQuestions([...questions, newQ]);
  };

  const handleUpdateField = (index, field, value) => {
    const updated = [...questions];
    updated[index] = { ...updated[index], [field]: value };
    setQuestions(updated);
  };

  const handleDelete = (index) => {
    const updated = questions.filter((_, idx) => idx !== index);
    setQuestions(updated);
  };

  const handleSave = async () => {
    setSaving(true);
    setError('');
    try {
      await prescreeningService.updateJobQuestions(job.id, questions);
      setSuccess('Pre-screening questionnaire saved and activated for applicants!');
      setTimeout(() => {
        setSuccess('');
        onClose();
      }, 1500);
    } catch (err) {
      setError('Failed to save questions.');
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen || !job) return null;

  return (
    <div className="ps-modal-overlay" onClick={onClose}>
      <div className="ps-modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="ps-modal-header">
          <div className="ps-header-left">
            <div className="ps-icon-wrap">
              <Sparkles size={20} className="ps-sparkle-icon" />
            </div>
            <div>
              <h3 className="ps-modal-title">AI Dynamic Pre-Screening Questionnaire</h3>
              <span className="ps-modal-sub">Job: <strong>{job.title}</strong></span>
            </div>
          </div>

          <div className="ps-header-actions">
            <button 
              className={`ps-preview-btn ${previewMode ? 'active' : ''}`}
              onClick={() => setPreviewMode(!previewMode)}
              title="Preview candidate applicant view"
            >
              {previewMode ? <EyeOff size={14} /> : <Eye size={14} />}
              <span>{previewMode ? 'Exit Preview' : 'Candidate Preview'}</span>
            </button>
            <button className="ps-close-btn" onClick={onClose}>
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="ps-modal-body">
          {error && (
            <div className="ps-alert-banner ps-alert-danger">
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="ps-alert-banner ps-alert-success">
              <CheckCircle2 size={16} />
              <span>{success}</span>
            </div>
          )}

          {/* Action Toolbar */}
          {!previewMode && (
            <div className="ps-toolbar">
              <div className="ps-toolbar-info">
                <span className="ps-count-badge">{questions.length} Active Question{questions.length !== 1 ? 's' : ''}</span>
                <span className="ps-help-text">Candidates will answer these questions when submitting their application.</span>
              </div>

              <div className="ps-toolbar-buttons">
                <button 
                  className="ps-btn-ai"
                  onClick={handleGenerate}
                  disabled={generating}
                >
                  {generating ? <Loader2 className="ps-spin" size={14} /> : <Sparkles size={14} />}
                  <span>{generating ? 'Generating Questions...' : 'Generate AI Questions'}</span>
                </button>

                <button 
                  className="ps-btn-secondary"
                  onClick={handleAddQuestion}
                >
                  <Plus size={14} />
                  <span>Add Question</span>
                </button>
              </div>
            </div>
          )}

          {loading ? (
            <div className="ps-loading-wrap">
              <Loader2 className="ps-spin" size={28} />
              <p>Loading questions...</p>
            </div>
          ) : previewMode ? (
            /* Candidate Experience Preview */
            <div className="ps-preview-container">
              <div className="ps-preview-banner">
                <Eye size={16} />
                <div>
                  <strong>Candidate Experience Preview Mode</strong>
                  <p>This is exactly how questions appear to candidates during the application submission.</p>
                </div>
              </div>

              {questions.length === 0 ? (
                <p className="ps-empty-text">No active pre-screening questions configured for this job.</p>
              ) : (
                <div className="ps-preview-list">
                  {questions.map((q, idx) => (
                    <div key={idx} className="ps-preview-item">
                      <div className="ps-preview-q-top">
                        <span className="ps-q-num">Question {idx + 1}</span>
                        <span className="ps-q-type-badge">{q.question_type}</span>
                        {q.is_required && <span className="ps-required-badge">* Required</span>}
                      </div>
                      <h4 className="ps-preview-q-text">{q.question_text || 'Untitled question'}</h4>
                      <textarea 
                        className="ps-preview-input" 
                        rows="3" 
                        disabled 
                        placeholder="Candidate will provide written response here..." 
                      />
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            /* Editor Mode */
            <div className="ps-questions-list">
              {questions.length === 0 ? (
                <div className="ps-empty-state">
                  <BookOpen size={36} className="ps-empty-icon" />
                  <h4>No Pre-Screening Questions Yet</h4>
                  <p>Click "Generate AI Questions" to automatically create tailored technical and scenario questions from this job description.</p>
                  <button className="ps-btn-ai" onClick={handleGenerate} disabled={generating}>
                    <Sparkles size={14} />
                    <span>Generate Role Questions</span>
                  </button>
                </div>
              ) : (
                questions.map((q, idx) => (
                  <div key={idx} className="ps-q-card">
                    <div className="ps-q-card-header">
                      <div className="ps-q-num-pill">
                        <Layers size={13} />
                        <span>Question {idx + 1}</span>
                      </div>

                      <div className="ps-q-header-controls">
                        <select 
                          className="ps-select-type"
                          value={q.question_type || 'technical'}
                          onChange={(e) => handleUpdateField(idx, 'question_type', e.target.value)}
                        >
                          {QUESTION_TYPES.map(t => (
                            <option key={t.value} value={t.value}>{t.label}</option>
                          ))}
                        </select>

                        <label className="ps-checkbox-label">
                          <input 
                            type="checkbox"
                            checked={Boolean(q.is_required)}
                            onChange={(e) => handleUpdateField(idx, 'is_required', e.target.checked)}
                          />
                          <span>Required</span>
                        </label>

                        <button 
                          className="ps-delete-btn"
                          onClick={() => handleDelete(idx)}
                          title="Delete question"
                        >
                          <Trash2 size={15} />
                        </button>
                      </div>
                    </div>

                    {/* Question Text */}
                    <div className="ps-field-group">
                      <label className="ps-field-lbl">Question Prompt:</label>
                      <textarea
                        className="ps-textarea"
                        rows="2"
                        value={q.question_text || ''}
                        placeholder="e.g. Explain how you would design a REST API using FastAPI for user records..."
                        onChange={(e) => handleUpdateField(idx, 'question_text', e.target.value)}
                      />
                    </div>

                    {/* Scoring Guidelines & Criteria */}
                    <div className="ps-criteria-row">
                      <div className="ps-field-group" style={{ flex: 1 }}>
                        <label className="ps-field-lbl">Evaluation Rubric / Key Answer Elements:</label>
                        <input
                          type="text"
                          className="ps-input"
                          value={q.scoring_criteria || ''}
                          placeholder="e.g. Evaluates understanding of schemas, error handling, and latency mitigation"
                          onChange={(e) => handleUpdateField(idx, 'scoring_criteria', e.target.value)}
                        />
                      </div>

                      <div className="ps-field-group" style={{ width: '100px' }}>
                        <label className="ps-field-lbl">Weight:</label>
                        <input
                          type="number"
                          step="0.25"
                          min="0.5"
                          max="3.0"
                          className="ps-input"
                          value={q.weight || 1.0}
                          onChange={(e) => handleUpdateField(idx, 'weight', parseFloat(e.target.value) || 1.0)}
                        />
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="ps-modal-footer">
          <button className="ps-btn-secondary" onClick={onClose}>
            Cancel
          </button>
          {!previewMode && (
            <button 
              className="ps-btn-primary"
              onClick={handleSave}
              disabled={saving || questions.length === 0}
            >
              {saving ? <Loader2 className="ps-spin" size={14} /> : <Save size={14} />}
              <span>{saving ? 'Saving...' : 'Save & Activate Questions'}</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default JobQuestionsModal;
