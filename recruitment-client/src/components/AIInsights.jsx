import React from 'react';
import InsightCard from './InsightCard';

const AIInsights = ({ insights = [] }) => {
  return (
    <div 
      className="hr-insights-grid"
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
        gap: 'var(--space-4)',
        width: '100%'
      }}
    >
      {insights.map((insight) => (
        <InsightCard 
          key={insight.title}
          title={insight.title}
          value={insight.value}
          description={insight.description}
          icon={insight.icon}
          alertType={insight.alertType}
        />
      ))}
    </div>
  );
};

export default AIInsights;
