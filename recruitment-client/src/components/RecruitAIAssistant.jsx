import React, { useState } from 'react';
import { Bot, LoaderCircle, Send, Sparkles } from 'lucide-react';

const RecruitAIAssistant = ({ onSendMessage }) => {
  const [message, setMessage] = useState('');
  const [conversationId, setConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');

  const send = async (text) => {
    const trimmed = text.trim();
    if (!trimmed || sending) return;
    setMessages((items) => [...items, { role: 'user', text: trimmed }]);
    setMessage('');
    setSending(true);
    setError('');
    try {
      const result = await onSendMessage(trimmed, conversationId);
      setConversationId(result.conversation_id || conversationId);
      setMessages((items) => [...items, {
        role: 'assistant',
        text: result.answer,
        source: result.source,
        actions: result.actions || [],
      }]);
    } catch (err) {
      setError(err.response?.data?.detail || 'RecruitAI could not answer right now.');
    } finally {
      setSending(false);
    }
  };

  const suggestions = [
    'Show the strongest candidates',
    'How many applications need review?',
    'Show active jobs',
  ];

  return (
    <section className="hr-assistant-panel">
      <div className="hr-assistant-heading">
        <Bot size={20} />
        <div>
          <h3>Ask RecruitAI</h3>
          <p>Grounded in live recruitment records</p>
        </div>
      </div>

      <div className="hr-assistant-suggestions">
        {suggestions.map((suggestion) => (
          <button key={suggestion} type="button" onClick={() => send(suggestion)} disabled={sending}>
            <Sparkles size={12} /> {suggestion}
          </button>
        ))}
      </div>

      <div className="hr-assistant-history" aria-live="polite">
        {messages.length === 0 && <p>Ask about candidates, jobs, or pipeline totals.</p>}
        {messages.slice(-5).map((item, index) => (
          <div key={`${item.role}-${index}`} className={`hr-chat-message ${item.role}`}>
            <span>{item.text}</span>
            {item.source && <small>Source: {item.source.replaceAll('_', ' ')}</small>}
          </div>
        ))}
        {sending && <div className="hr-chat-message assistant"><LoaderCircle size={15} className="spin" /> Analyzing live data…</div>}
        {error && <p className="hr-assistant-error">{error}</p>}
      </div>

      <form className="hr-assistant-input" onSubmit={(event) => { event.preventDefault(); send(message); }}>
        <input
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          maxLength={1000}
          placeholder="Ask RecruitAI…"
          aria-label="Ask RecruitAI"
        />
        <button type="submit" disabled={sending || !message.trim()} aria-label="Send message">
          <Send size={16} />
        </button>
      </form>
    </section>
  );
};

export default RecruitAIAssistant;
