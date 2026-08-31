import React from 'react';
import { Calendar, CheckCircle2, AlertTriangle, GraduationCap, Briefcase, FolderGit2, Award } from 'lucide-react';

const getEventIcon = (type) => {
  switch (type) {
    case 'Education':
      return <GraduationCap size={15} />;
    case 'Internship':
    case 'Work Experience':
      return <Briefcase size={15} />;
    case 'Project':
      return <FolderGit2 size={15} />;
    case 'Certification':
    default:
      return <Award size={15} />;
  }
};

const TimelineVisualization = ({ timelineData = {} }) => {
  const events = timelineData.events || [];
  const overlaps = timelineData.overlaps || [];
  const anomalies = timelineData.anomalies || [];

  if (events.length === 0) {
    return null;
  }

  return (
    <div className="verif-card">
      <div className="verif-card-header">
        <div className="verif-card-title-wrap">
          <Calendar size={18} className="verif-card-icon" />
          <h3>Timeline Intelligence & Chronology Analysis</h3>
        </div>
        <span className="verif-status-tag verif-tag-verified">
          <CheckCircle2 size={13} /> {timelineData.status || 'Consistent'}
        </span>
      </div>

      {/* Overlaps / Concurrent Notices */}
      {overlaps.length > 0 && (
        <div className="verif-alert-box verif-alert-warning">
          <AlertTriangle size={16} />
          <div>
            <strong>Concurrent Experiences Detected:</strong>
            <ul>
              {overlaps.map((o, idx) => (
                <li key={idx}>{o}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Anomaly Alerts */}
      {anomalies.length > 0 && (
        <div className="verif-alert-box verif-alert-danger">
          <AlertTriangle size={16} />
          <div>
            <strong>Chronology Alerts:</strong>
            <ul>
              {anomalies.map((a, idx) => (
                <li key={idx}>{a}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Visual Timeline Track */}
      <div className="verif-timeline-track">
        {events.map((evt, idx) => (
          <div key={idx} className="verif-timeline-node">
            <div className="verif-node-bullet">
              {getEventIcon(evt.type)}
            </div>
            <div className="verif-node-card">
              <div className="verif-node-top">
                <span className="verif-node-type">{evt.type}</span>
                <span className="verif-node-dates">{evt.display_dates}</span>
              </div>
              <h5 className="verif-node-title">{evt.title}</h5>
              {evt.subtitle && <p className="verif-node-sub">{evt.subtitle}</p>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TimelineVisualization;
