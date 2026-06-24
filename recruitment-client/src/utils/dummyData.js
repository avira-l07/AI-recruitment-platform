export const dummyCandidates = [
  { id: 1, name: 'Alice Johnson', email: 'alice@example.com', skills: ['React', 'Node.js', 'AWS'], score: 92, status: 'Shortlisted', matchedJob: 'Frontend Developer' },
  { id: 2, name: 'Bob Smith', email: 'bob@example.com', skills: ['Python', 'TensorFlow', 'SQL'], score: 85, status: 'Pending', matchedJob: 'AI/ML Intern' },
  { id: 3, name: 'Charlie Davis', email: 'charlie@example.com', skills: ['Java', 'Spring', 'Docker'], score: 65, status: 'Pending', matchedJob: 'Backend Developer' },
  { id: 4, name: 'Diana Prince', email: 'diana@example.com', skills: ['HTML', 'CSS', 'JavaScript'], score: 45, status: 'Rejected', matchedJob: 'Frontend Developer' },
  { id: 5, name: 'Evan Wright', email: 'evan@example.com', skills: ['C++', 'Algorithms', 'Data Structures'], score: 72, status: 'Shortlisted', matchedJob: 'Backend Developer' }
];

export const dummyJobs = [
  { id: 1, title: 'Frontend Developer', description: 'Looking for a skilled frontend developer to build modern web applications using React.', requiredSkills: ['React', 'JavaScript', 'CSS'], experienceLevel: 'Mid', educationRequirement: 'Bachelors' },
  { id: 2, title: 'AI/ML Intern', description: 'Join our data science team to work on predictive models and NLP tasks.', requiredSkills: ['Python', 'Machine Learning', 'TensorFlow'], experienceLevel: 'Entry', educationRequirement: 'Masters' },
  { id: 3, title: 'Backend Developer', description: 'We need an experienced backend developer for building scalable microservices.', requiredSkills: ['Java', 'Spring Boot', 'Microservices'], experienceLevel: 'Senior', educationRequirement: 'Bachelors' }
];

export const dummyAnalytics = {
  totalCandidates: 120,
  totalJobs: 15,
  shortlisted: 35,
  rejected: 40,
  averageScore: 68,
  topSkills: ['React', 'Python', 'Java', 'SQL', 'AWS'],
  scoreDistribution: {
    strong: 45,
    moderate: 50,
    weak: 25
  }
};

export const dummyCandidateMatches = [
  { id: 101, jobTitle: 'Frontend Developer', matchScore: 92, explanation: 'Strong match on React and UI frameworks.', status: 'Shortlisted' },
  { id: 102, jobTitle: 'Fullstack Engineer', matchScore: 68, explanation: 'Missing backend experience (Node.js/Express).', status: 'Pending' }
];