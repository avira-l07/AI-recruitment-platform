import React from 'react';
import { FolderGit2, GitBranch, PlayCircle, ExternalLink, CheckCircle2, AlertCircle, Code2 } from 'lucide-react';

const ProjectVerificationTable = ({ projects = [] }) => {
  if (!projects || projects.length === 0) {
    return (
      <div className="verif-card">
        <div className="verif-card-header">
          <div className="verif-card-title-wrap">
            <FolderGit2 size={18} className="verif-card-icon" />
            <h3>Project & Repository Verification</h3>
          </div>
        </div>
        <p className="verif-empty-text">No technical projects extracted from resume.</p>
      </div>
    );
  }

  return (
    <div className="verif-card">
      <div className="verif-card-header">
        <div className="verif-card-title-wrap">
          <FolderGit2 size={18} className="verif-card-icon" />
          <h3>Project & Repository Verification</h3>
        </div>
        <span className="verif-count-pill">{projects.length} Project{projects.length > 1 ? 's' : ''}</span>
      </div>

      <div className="verif-projects-grid">
        {projects.map((p, idx) => {
          const hasRepo = Boolean(p.repository_url);
          const hasDemo = Boolean(p.demo_url);

          return (
            <div key={idx} className="verif-project-item">
              <div className="verif-project-top">
                <div className="verif-project-title-area">
                  <h4 className="verif-project-name">{p.project_name}</h4>
                  <p className="verif-project-desc">{p.description}</p>
                </div>
                
                <span className="verif-match-badge verif-match-high">
                  <CheckCircle2 size={13} /> {p.technology_match || 'High Match'}
                </span>
              </div>

              {/* Technologies */}
              {p.detected_technologies && p.detected_technologies.length > 0 && (
                <div className="verif-tech-row">
                  <span className="verif-tech-lbl"><Code2 size={13} /> Technologies:</span>
                  <div className="verif-tech-tags">
                    {p.detected_technologies.map((t, tIdx) => (
                      <span key={tIdx} className="verif-tech-pill">{t}</span>
                    ))}
                  </div>
                </div>
              )}

              {/* Verification Signals Row */}
              <div className="verif-signals-row">
                <div className="verif-signal-chip">
                  <GitBranch size={13} />
                  <span>Repo: <strong>{p.repository_status}</strong></span>
                </div>
                <div className="verif-signal-chip">
                  <PlayCircle size={13} />
                  <span>Demo: <strong>{p.demo_status}</strong></span>
                </div>
                <div className="verif-signal-chip">
                  <span>Activity: <strong>{p.commit_activity || 'Detected'}</strong></span>
                </div>
              </div>

              {/* Action Links */}
              <div className="verif-project-links">
                {hasRepo ? (
                  <a href={p.repository_url} target="_blank" rel="noopener noreferrer" className="verif-btn-link verif-btn-repo">
                    <GitBranch size={14} />
                    <span>View Repository ({p.repository_url.replace('https://github.com/', '')})</span>
                    <ExternalLink size={12} />
                  </a>
                ) : (
                  <span className="verif-no-link-text">No public repository link on resume</span>
                )}

                {hasDemo && (
                  <a href={p.demo_url} target="_blank" rel="noopener noreferrer" className="verif-btn-link verif-btn-demo">
                    <PlayCircle size={14} />
                    <span>Live Demo</span>
                    <ExternalLink size={12} />
                  </a>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ProjectVerificationTable;
