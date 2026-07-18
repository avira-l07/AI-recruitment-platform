import api from './api';
import authService from './authService';

const parseMaybeJson = (value) => {
  if (!value || typeof value !== 'string') return {};
  try {
    const parsed = JSON.parse(value);
    return parsed && typeof parsed === 'object' ? parsed : {};
  } catch {
    return {};
  }
};

export const normalizeMatch = (item = {}) => {
  const insight = parseMaybeJson(item.explanation);
  return {
    ...item,
    applicationId: item.application_id ?? item.id,
    matchId: item.match_id,
    candidateId: item.candidate_id,
    userId: item.user_id,
    name: item.name || item.full_name || 'Unknown Candidate',
    jobTitle: item.jobTitle || item.job_title || item.matchedJob || 'Unknown Role',
    matchScore: item.match_score ?? item.score ?? 0,
    fitLabel: item.fitLabel || item.fit_label || insight.fit_label,
    confidenceScore: item.confidenceScore ?? item.confidence_score ?? null,
    confidenceLabel: item.confidenceLabel || item.confidence_label || null,
    aiSemanticAnalysis: item.aiSemanticAnalysis || item.ai_semantic_analysis || insight.ai_semantic_analysis,
    hrSummary: item.hrSummary || item.hr_summary || insight.hr_summary,
    roadmap: item.roadmap || insight.roadmap || [],
    interviewQuestions: item.interviewQuestions || item.interview_questions || insight.interview_questions || [],
    riskFlags: item.riskFlags || item.risk_flags || insight.risk_flags || [],
    recommendation: item.recommendation || insight.recommendation,
    semanticMatches: item.semanticMatches || item.semantic_matches || insight.semantic_matches || [],
    aiSource: item.aiSource || item.ai_source || insight.ai_source || 'local_ai',
    fallbackActive: item.fallbackActive ?? item.fallback_active ?? false,
    fallbackReason: item.fallbackReason || item.fallback_reason || null,
    matchedSkills: item.matchedSkills || item.matched_skills || [],
    missingSkills: item.missingSkills || item.missing_skills || [],
    explanation: insight.short_explanation || item.explanation,
  };
};

const normalizeArray = (data) => (Array.isArray(data) ? data.map(normalizeMatch) : []);

const matchingService = {
  getAllMatches: async () => {
    const response = await api.get('/applications/hr/me');
    return normalizeArray(response.data);
  },
  getCandidateMatches: async (userId) => {
    const user = authService.getCurrentUser();
    const path = user?.role === 'hr' && userId ? `/matching/candidate/${userId}` : '/matching/me';
    const response = await api.get(path);
    return normalizeArray(response.data);
  },
  getMyMatches: async () => {
    const response = await api.get('/matching/me');
    return normalizeArray(response.data);
  },
  getJobMatches: async (jobId) => {
    const response = await api.get(`/matching/job/${jobId}`);
    return normalizeArray(response.data);
  },
  updateMatchStatus: async (applicationId, status, reason = null) => {
    const response = await api.put(`/matching/${applicationId}/status`, { status, reason });
    return response.data;
  },
  applyToJob: async (_userId, jobId) => {
    const response = await api.post('/applications', { job_id: jobId });
    return response.data;
  },
};

export default matchingService;
