import React from 'react';
import { Cpu } from 'lucide-react';
import EngineStatus from './EngineStatus';

const RecruitAIEngine = ({ mode = 'hybrid', localStatus = 'completed', geminiStatus = 'completed', hybridStatus = 'completed', lastSync }) => {
  return (
    <div 
      className="hr-recruit-engine-panel"
      style={{
        backgroundColor: '#0F172A',
        color: '#FFFFFF',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--space-6)',
        border: '1px solid #1E293B',
        boxShadow: 'var(--elevation-2)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-4)'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
        <Cpu size={20} style={{ color: 'var(--color-primary)' }} />
        <div>
          <h3 style={{ margin: 0, fontSize: 'var(--font-lg)', fontWeight: 'var(--weight-semibold)' }}>
            RecruitAI Engine
          </h3>
          <p style={{ margin: 0, fontSize: 'var(--font-xs)', color: '#94A3B8' }}>
            {mode === 'hybrid' ? 'Hybrid AI architecture active' : `${mode.toUpperCase()} engine active`}
          </p>
        </div>
      </div>

      <div 
        style={{ 
          display: 'flex', 
          gap: 'var(--space-4)', 
          flexWrap: 'wrap' 
        }}
      >
        <EngineStatus 
          title="Local AI" 
          status={localStatus} 
          capabilities={['Resume Parser', 'ATS Scoring', 'Skill Matching']} 
        />
        <EngineStatus 
          title="Gemini Engine" 
          status={geminiStatus} 
          capabilities={['Career Summary', 'Interview Gen', 'Gap Analysis']} 
        />
        <EngineStatus 
          title="Hybrid AI" 
          status={hybridStatus} 
          capabilities={['Final Recommendation', 'Roadmap Generation']} 
        />
      </div>

      {lastSync && (
        <div style={{ borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: 'var(--space-3)', display: 'flex', justifyContent: 'space-between', fontSize: 'var(--font-xs)', color: '#64748B' }}>
          <span>Average Analysis Time: 3.2s</span>
          <span>Last Sync: {lastSync}</span>
        </div>
      )}
    </div>
  );
};

export default RecruitAIEngine;
