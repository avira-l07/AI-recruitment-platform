import React from 'react';
import { Sparkles } from 'lucide-react';

const RecruitAILogo = () => {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
      <div style={{
        width: '32px',
        height: '32px',
        borderRadius: '10px',
        background: 'linear-gradient(135deg, #3654E0 0%, #8B7CF0 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: '0 4px 12px rgba(84, 110, 244, 0.3)',
      }}>
        <Sparkles size={16} color="#FFFFFF" fill="#FFFFFF" style={{ opacity: 0.95 }} />
      </div>
      <span style={{
        color: '#FFFFFF',
        fontSize: '15px',
        fontWeight: '600',
        letterSpacing: '0.2px',
        fontFamily: "'Space Grotesk', 'Inter', sans-serif",
      }}>
        RecruitAI
      </span>
    </div>
  );
};

export default RecruitAILogo;
