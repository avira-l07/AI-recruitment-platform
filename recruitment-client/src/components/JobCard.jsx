import React from 'react';

const JobCard = ({ job }) => {
  const { title, description, requiredSkills, experienceLevel, educationRequirement } = job;
  
  const truncatedDesc = description.length > 100 ? description.substring(0, 100) + '...' : description;

  return (
    <div className="card job-card" style={{ marginBottom: '16px' }}>
      <h3 style={{ color: 'var(--navy)', marginBottom: '8px' }}>{title}</h3>
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', marginBottom: '12px' }}>{truncatedDesc}</p>
      
      <div style={{ marginBottom: '12px' }}>
        {requiredSkills && requiredSkills.map((skill, i) => (
          <span key={i} className="skill-tag">{skill}</span>
        ))}
      </div>
      
      <div style={{ display: 'flex', gap: '16px', fontSize: '0.85rem', color: 'var(--text-secondary)', borderTop: '1px solid var(--border)', paddingTop: '12px' }}>
        <span><strong>Experience:</strong> {experienceLevel}</span>
        <span><strong>Education:</strong> {educationRequirement}</span>
      </div>
    </div>
  );
};

export default JobCard;