import React, { useState } from 'react';
import { Send, Sparkles } from 'lucide-react';

const RecruitAIAssistant = ({ onSendMessage }) => {
  const [input, setInput] = useState('');
  
  const suggestions = [
    'Find backend candidates',
    'Compare candidates',
    'Generate interview questions',
    'Explain candidate score',
    'Find missing skills'
  ];

  const handleSend = () => {
    if (!input.trim()) return;
    if (onSendMessage) onSendMessage(input.trim());
    setInput('');
  };

  const handleSuggestClick = (suggestion) => {
    setInput(suggestion);
  };

  return (
    <div 
      className="hr-ai-assistant"
      style={{
        backgroundColor: '#1E293B',
        color: '#FFFFFF',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--space-6)',
        border: '1px solid #334155',
        boxShadow: 'var(--elevation-2)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-4)'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
        <Sparkles size={18} style={{ color: 'var(--color-secondary)' }} />
        <div>
          <h3 style={{ margin: 0, fontSize: 'var(--font-lg)', fontWeight: 'var(--weight-semibold)' }}>
            Ask RecruitAI
          </h3>
          <p style={{ margin: 0, fontSize: 'var(--font-xs)', color: '#94A3B8' }}>
            Your personal AI hiring assistant.
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
        {suggestions.map((s) => (
          <button
            key={s}
            onClick={() => handleSuggestClick(s)}
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: 'var(--radius-md)',
              padding: '10px 14px',
              color: '#E2E8F0',
              fontSize: 'var(--font-sm)',
              cursor: 'pointer',
              textAlign: 'left',
              transition: 'background var(--transition-fast)'
            }}
            onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.08)'}
            onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)'}
          >
            {s}
          </button>
        ))}
      </div>

      <div 
        style={{ 
          display: 'flex', 
          alignItems: 'center', 
          backgroundColor: 'rgba(0,0,0,0.2)', 
          border: '1px solid rgba(255,255,255,0.1)', 
          borderRadius: 'var(--radius-md)', 
          padding: '4px 12px' 
        }}
      >
        <input 
          type="text" 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask anything..."
          style={{
            border: 'none',
            background: 'transparent',
            outline: 'none',
            color: '#FFFFFF',
            fontSize: 'var(--font-sm)',
            width: '100%',
            padding: '8px 0'
          }}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
        />
        <button 
          onClick={handleSend}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--color-secondary)',
            cursor: 'pointer',
            padding: 'var(--space-1)'
          }}
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  );
};

export default RecruitAIAssistant;
