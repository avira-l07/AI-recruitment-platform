import React from 'react';
import { Cpu, TriangleAlert } from 'lucide-react';
import EngineStatus from './EngineStatus';

const RecruitAIEngine = ({ status }) => {
  const data = status || {};
  const localStatus = data.local_ai?.status || 'available';
  const geminiStatus = data.gemini?.status || 'not_configured';
  const hybridStatus = data.hybrid?.status || 'idle';
  const mode = data.mode || 'idle';
  const lastUpdated = data.last_updated ? new Date(data.last_updated).toLocaleString() : 'Not available';

  return (
    <section className="hr-recruit-engine-panel">
      <div className="hr-engine-heading">
        <Cpu size={20} />
        <div>
          <h3>RecruitAI Engine</h3>
          <p>Current mode: {mode.replaceAll('_', ' ')}</p>
        </div>
      </div>

      {data.fallback_active && (
        <div className="hr-engine-fallback">
          <TriangleAlert size={16} />
          <span>{data.fallback_reason || 'Gemini is unavailable. Local AI fallback is active.'}</span>
        </div>
      )}

      <div className="hr-engine-grid">
        <EngineStatus title="Local AI" status={localStatus} capabilities={['Resume Parser', 'ATS Scoring', 'Skill Matching']} />
        <EngineStatus title="Gemini Engine" status={geminiStatus} capabilities={['Summary Enhancement', 'Interview Wording', 'Gap Explanation']} />
        <EngineStatus title="Hybrid AI" status={hybridStatus} capabilities={['Combined Result', 'Source Transparency']} />
      </div>

      <div className="hr-engine-footer">
        <span>Average analysis: {data.average_analysis_time == null ? 'Not available' : `${data.average_analysis_time}s`}</span>
        <span>Last update: {lastUpdated}</span>
      </div>
    </section>
  );
};

export default RecruitAIEngine;
