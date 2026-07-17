import React from 'react';
import { CheckCircle2, CircleOff, Clock, Loader2, TriangleAlert, XCircle } from 'lucide-react';

const statusMeta = (status = 'waiting') => {
  const normalized = String(status).toLowerCase();
  if (['completed', 'available'].includes(normalized)) return { label: normalized === 'available' ? 'Available' : 'Completed', tone: 'success', icon: CheckCircle2 };
  if (['running', 'local_running', 'gemini_running', 'combining'].includes(normalized)) return { label: 'Running', tone: 'primary', icon: Loader2, spinning: true };
  if (['rate_limited', 'temporarily_unavailable', 'timeout', 'local_fallback'].includes(normalized)) return { label: normalized.replaceAll('_', ' '), tone: 'warning', icon: TriangleAlert };
  if (['failed', 'authentication_failed', 'request_failed', 'invalid_response'].includes(normalized)) return { label: normalized.replaceAll('_', ' '), tone: 'danger', icon: XCircle };
  if (['not_configured', 'skipped', 'unavailable'].includes(normalized)) return { label: normalized.replaceAll('_', ' '), tone: 'muted', icon: CircleOff };
  return { label: normalized.replaceAll('_', ' ') || 'Waiting', tone: 'muted', icon: Clock };
};

const EngineStatus = ({ title, status, capabilities = [] }) => {
  const meta = statusMeta(status);
  const Icon = meta.icon;
  return (
    <div className="hr-engine-status-card">
      <div className="hr-engine-status-header">
        <h4>{title}</h4>
        <div className={`hr-engine-state ${meta.tone}`}>
          <Icon size={16} className={meta.spinning ? 'spin' : ''} />
          <span>{meta.label}</span>
        </div>
      </div>
      <div className="hr-engine-capabilities">
        {capabilities.map((capability) => (
          <div key={capability}><span />{capability}</div>
        ))}
      </div>
    </div>
  );
};

export default EngineStatus;
