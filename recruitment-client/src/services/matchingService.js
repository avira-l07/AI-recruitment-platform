import api from './api';

const parseMaybeJson = (value) => {
  if (!value || typeof value !== 'string') return {};
  try {
    const parsed = JSON.parse(value);
    return parsed && typeof parsed === 'object' ? parsed : {};
  } catch {
    return {};
  }
};

const normalizeMatch = (item = {}) => {
  const insight = parseMaybeJson(item.explanation);
  return {
    ...item,
    fitLabel: item.fitLabel || insight.fit_label,
    aiSemanticAnalysis: item.aiSemanticAnalysis || insight.ai_semantic_analysis,
    hrSummary: item.hrSummary || insight.hr_summary,
    roadmap: item.roadmap || insight.roadmap || [],
    interviewQuestions: item.interviewQuestions || insight.interview_questions || [],
    riskFlags: item.riskFlags || insight.risk_flags || [],
    recommendation: item.recommendation || insight.recommendation,
    semanticMatches: item.semanticMatches || insight.semantic_matches || [],
    aiSource: item.aiSource || insight.ai_source,
    explanation: insight.short_explanation || item.explanation,
  };
};

const normalizeArray = (data) => Array.isArray(data) ? data.map(normalizeMatch) : [];

const matchingService = {
  getAllMatches: async () => {
    const response = await api.get('/matching/all');
    return normalizeArray(response.data);
  },
  getCandidateMatches: async (userId) => {
    const response = await api.get(`/matching/candidate/${userId}`);
    return normalizeArray(response.data);
  },
  getJobMatches: async (jobId) => {
    const response = await api.get(`/matching/job/${jobId}`);
    return normalizeArray(response.data);
  },
  updateMatchStatus: async (matchId, status) => {
    const response = await api.put(`/matching/${matchId}/status`, { status });
    return response.data;
  },
  applyToJob: async (userId, jobId) => {
    const response = await api.post('/matching/apply', { user_id: userId, job_id: jobId });
    return response.data;
  }
};

export default matchingService;
