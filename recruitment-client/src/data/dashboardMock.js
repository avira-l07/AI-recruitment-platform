export const mockStats = [
  {
    label: 'Total Candidates',
    value: '245',
    iconBgClass: 'hr-icon-blue',
    helperText: 'Live database count',
    trendColor: 'green'
  },
  {
    label: 'Total Jobs',
    value: '12',
    iconBgClass: 'hr-icon-muted',
    helperText: '12 active openings'
  },
  {
    label: 'AI Reviewed',
    value: '238',
    iconBgClass: 'hr-icon-green',
    helperText: '97% of total candidates',
    trendColor: 'green'
  },
  {
    label: 'Manual Review',
    value: '7',
    iconBgClass: 'hr-icon-red',
    helperText: 'Requires HR validation',
    trendColor: 'red'
  }
];

export const mockPipeline = [
  { label: 'Applied', count: 245 },
  { label: 'AI Reviewed', count: 238 },
  { label: 'Manual Review', count: 7, isAlert: true },
  { label: 'Shortlisted', count: 58 },
  { label: 'Interview', count: 12 },
  { label: 'Offer', count: 5 }
];

export const mockCandidates = [
  {
    id: 1,
    name: 'John Doe',
    role: 'Backend Developer',
    score: 92,
    aiSource: 'hybrid',
    matchedSkills: ['Python', 'FastAPI', 'Docker'],
    missingSkills: ['AWS'],
    confidence: 'High',
    status: 'Pending'
  },
  {
    id: 2,
    name: 'Sara Smith',
    role: 'Frontend Developer',
    score: 88,
    aiSource: 'gemini',
    matchedSkills: ['React', 'JavaScript', 'CSS'],
    missingSkills: ['TypeScript'],
    confidence: 'High',
    status: 'Shortlisted'
  },
  {
    id: 3,
    name: 'Mike Johnson',
    role: 'Full Stack Engineer',
    score: 42,
    aiSource: 'local',
    matchedSkills: ['JavaScript', 'HTML'],
    missingSkills: ['Node.js', 'PostgreSQL', 'Docker'],
    confidence: 'Medium',
    status: 'Rejected'
  }
];

export const mockEngineStatus = {
  mode: 'hybrid',
  localStatus: 'completed',
  geminiStatus: 'running',
  hybridStatus: 'waiting',
  lastSync: '1 min ago'
};

export const mockInsights = [
  {
    title: "Today's Resume Analysis",
    value: "17 Resumes",
    description: "Processed through Hybrid Engine since 9:00 AM",
    alertType: "success"
  },
  {
    title: "Manual Reviews Required",
    value: "4 Matches",
    description: "Low confidence score detected in skills",
    alertType: "warning"
  },
  {
    title: "Highest Matching Score",
    value: "John Doe (92%)",
    description: "Matches Senior Python Developer requirements",
    alertType: "success"
  },
  {
    title: "Gemini Engine Failures",
    value: "0 Errors",
    description: "Local AI fallback has not been triggered today",
    alertType: "success"
  }
];
