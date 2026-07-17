import React from 'react';
import { ChevronRight } from 'lucide-react';
import PipelineStage from './PipelineStage';

const Pipeline = ({ stages = [] }) => {
  return (
    <div 
      className="hr-pipeline-wrapper" 
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--space-3)',
        width: '100%',
        overflowX: 'auto',
        padding: 'var(--space-1) 0'
      }}
    >
      {stages.map((stage, idx) => (
        <React.Fragment key={stage.label}>
          <PipelineStage 
            label={stage.label} 
            count={stage.count} 
            isAlert={stage.isAlert} 
          />
          {idx < stages.length - 1 && (
            <ChevronRight 
              size={18} 
              style={{ color: 'var(--color-muted)', opacity: 0.5, flexShrink: 0 }} 
            />
          )}
        </React.Fragment>
      ))}
    </div>
  );
};

export default Pipeline;
