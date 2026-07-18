import React, { useState, useEffect, useRef } from 'react';
import { X, FileText, Download, ZoomIn, ZoomOut, ExternalLink, ShieldAlert } from 'lucide-react';
import resumeService from '../services/resumeService';
import './ResumeReviewDrawer.css';

const getInitials = (name) => {
  if (!name) return '??';
  return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
};

const ResumeReviewDrawer = ({
  isOpen,
  onClose,
  candidate,
  onStatusUpdate
}) => {
  const closeButtonRef = useRef(null);
  const abortControllerRef = useRef(null);

  // Tabs: 'original' or 'profile'
  const [activeTab, setActiveTab] = useState('original');

  // Loading & Error states
  const [fileUrl, setFileUrl] = useState(null);
  const [fileLoading, setFileLoading] = useState(false);
  const [fileError, setFileError] = useState('');
  
  const [profile, setProfile] = useState(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileError, setProfileError] = useState('');

  // Zoom level state
  const [zoom, setZoom] = useState(100);

  // Reset states and load resume data when candidate changes
  const loadResumeData = async (userId) => {
    setFileLoading(true);
    setProfileLoading(true);
    setFileError('');
    setProfileError('');
    
    // Revoke previous URL to prevent memory leaks
    if (fileUrl) {
      URL.revokeObjectURL(fileUrl);
      setFileUrl(null);
    }
    setProfile(null);
    setZoom(100);

    // Set up active abort controller
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();
    const signal = abortControllerRef.current.signal;

    // Load file and profile concurrently
    const filePromise = resumeService.getResumeFile(userId, { signal });
    const profilePromise = resumeService.getResume(userId, { signal });

    try {
      const fileRes = await filePromise;
      const url = URL.createObjectURL(fileRes.blob);
      setFileUrl(url);
      setFileLoading(false);
    } catch (err) {
      if (err.name === 'CanceledError' || err.name === 'AbortError' || err.message === 'canceled') {
        // Silently ignore aborted requests
        return;
      }
      setFileError('The original resume could not be found or loaded.');
      setFileLoading(false);
    }

    try {
      const profileRes = await profilePromise;
      setProfile(profileRes);
      setProfileLoading(false);
    } catch (err) {
      if (err.name === 'CanceledError' || err.name === 'AbortError' || err.message === 'canceled') {
        // Silently ignore aborted requests
        return;
      }
      setProfileError('Extracted profile details are temporarily unavailable.');
      setProfileLoading(false);
    }
  };

  useEffect(() => {
    if (!isOpen || !candidate) {
      // Clear all state values and clean up Blob URL on close / candidate clear
      if (fileUrl) {
        URL.revokeObjectURL(fileUrl);
        setFileUrl(null);
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }
      setProfile(null);
      setFileError('');
      setProfileError('');
      setActiveTab('original');
      setZoom(100);
      return;
    }

    const userId = candidate.user_id || candidate.userId;
    if (userId) {
      loadResumeData(userId);
    }

    return () => {
      // Abort controller cleanup on unmount
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [isOpen, candidate]);

  // Clean up Object URL on unmount
  useEffect(() => {
    return () => {
      if (fileUrl) {
        URL.revokeObjectURL(fileUrl);
      }
    };
  }, [fileUrl]);

  // Focus management
  useEffect(() => {
    if (isOpen && closeButtonRef.current) {
      closeButtonRef.current.focus();
    }
  }, [isOpen]);

  // Lock body scrolling when drawer is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  // Escape key handler
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen || !candidate) return null;

  const candidateName = candidate.name || candidate.fullName || 'Unknown Candidate';
  const email = candidate.email || profile?.email || 'No email provided';
  const phone = candidate.phone || profile?.phone || 'Not available';
  
  // Extract file properties from parsed profile
  const originalFileName = profile?.file_name || 'resume.pdf';
  const uploadDate = profile?.uploaded_at ? new Date(profile.uploaded_at).toLocaleDateString() : 'N/A';
  const fileExtension = originalFileName.substring(originalFileName.lastIndexOf('.')).toLowerCase();
  const isPdf = fileExtension === '.pdf';

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 25, 200));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 25, 50));

  const handleOpenNewTab = () => {
    if (fileUrl) {
      window.open(fileUrl, '_blank');
    }
  };

  const handleDownload = () => {
    if (!fileUrl) return;
    const link = document.createElement("a");
    link.href = fileUrl;
    link.download = originalFileName || "resume.pdf";
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  const handleRetry = () => {
    const userId = candidate.user_id || candidate.userId;
    if (userId) {
      loadResumeData(userId);
    }
  };

  return (
    <>
      <div 
        className="review-overlay" 
        onClick={onClose}
        aria-hidden="true"
      />
      <aside 
        className="review-drawer"
        role="dialog"
        aria-modal="true"
        aria-labelledby="review-drawer-title"
      >
        {/* Drawer Header */}
        <div className="review-header">
          <div className="review-header-info">
            <div className="review-avatar">
              {getInitials(candidateName)}
            </div>
            <div className="review-title">
              <h2 id="review-drawer-title">{candidateName}</h2>
              <p>
                <span>{email}</span>
                <span>{phone}</span>
              </p>
            </div>
          </div>
          <button 
            ref={closeButtonRef}
            onClick={onClose} 
            className="review-close-btn"
            aria-label="Close Resume Review drawer"
            type="button"
          >
            <X size={20} />
          </button>
        </div>

        {/* Tabs switcher */}
        <div className="review-tabs-bar" role="tablist">
          <button
            role="tab"
            aria-selected={activeTab === 'original'}
            aria-controls="panel-original"
            className={`review-tab-btn ${activeTab === 'original' ? 'active' : ''}`}
            onClick={() => setActiveTab('original')}
            type="button"
          >
            Original Resume
          </button>
          <button
            role="tab"
            aria-selected={activeTab === 'profile'}
            aria-controls="panel-profile"
            className={`review-tab-btn ${activeTab === 'profile' ? 'active' : ''}`}
            onClick={() => setActiveTab('profile')}
            type="button"
          >
            Extracted Profile
          </button>
        </div>

        {/* Drawer Body */}
        <div className="review-body">
          {activeTab === 'original' && (
            <div 
              id="panel-original" 
              role="tabpanel" 
              style={{ display: 'flex', flexDirection: 'column', gap: '16px', flex: 1 }}
            >
              {/* File Info */}
              <div className="review-metadata-card">
                <div className="review-meta-item">
                  <span className="review-meta-label">Filename</span>
                  <span className="review-meta-value">{originalFileName}</span>
                </div>
                <div className="review-meta-item">
                  <span className="review-meta-label">Uploaded At</span>
                  <span className="review-meta-value">{uploadDate}</span>
                </div>
              </div>

              {/* Document Pane */}
              <div className="review-document-pane">
                {fileLoading && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', padding: '24px', flex: 1, backgroundColor: '#FFFFFF' }}>
                    <div className="ai-skeleton-bar" style={{ height: '40px', width: '100%' }} />
                    <div className="ai-skeleton-bar" style={{ height: '320px', width: '100%', flex: 1 }} />
                  </div>
                )}

                {fileError && !fileLoading && (
                  <div className="review-preview-fallback">
                    <ShieldAlert size={36} style={{ color: '#DC2626' }} />
                    <div>
                      <h4 className="review-fallback-title">Unable to Load Preview</h4>
                      <p className="review-fallback-desc">{fileError}</p>
                    </div>
                    <button type="button" onClick={handleRetry} className="review-fallback-btn">
                      Retry Load
                    </button>
                  </div>
                )}

                {!fileLoading && !fileError && fileUrl && (
                  <>
                    {isPdf ? (
                      <>
                        <div className="pdf-viewer-toolbar">
                          <div className="pdf-viewer-controls">
                            <button 
                              onClick={handleZoomOut} 
                              className="pdf-toolbar-btn"
                              title="Zoom out"
                              type="button"
                            >
                              <ZoomOut size={14} />
                            </button>
                            <span className="pdf-zoom-label">{zoom}%</span>
                            <button 
                              onClick={handleZoomIn} 
                              className="pdf-toolbar-btn"
                              title="Zoom in"
                              type="button"
                            >
                              <ZoomIn size={14} />
                            </button>
                          </div>
                          <div style={{ display: 'flex', gap: '6px' }}>
                            <button 
                              onClick={handleDownload} 
                              className="pdf-toolbar-btn"
                              type="button"
                            >
                              <Download size={12} /> Download Original
                            </button>
                            <button 
                              onClick={handleOpenNewTab} 
                              className="pdf-toolbar-btn"
                              type="button"
                            >
                              <ExternalLink size={12} /> Open in new tab
                            </button>
                          </div>
                        </div>
                        <div style={{ flex: 1, overflow: 'auto', position: 'relative' }}>
                          <iframe 
                            src={fileUrl} 
                            title={`${candidateName} original resume`}
                            style={{ 
                              border: 'none',
                              transform: `scale(${zoom / 100})`,
                              transformOrigin: 'top left',
                              width: `${10000 / zoom}%`,
                              height: `${10000 / zoom}%`,
                              minHeight: '450px'
                            }} 
                          />
                        </div>
                      </>
                    ) : (
                      <div className="review-preview-fallback">
                        <div className="review-fallback-icon">
                          <FileText size={32} />
                        </div>
                        <div>
                          <h4 className="review-fallback-title">DOCX Document Preview</h4>
                          <p className="review-fallback-desc">Direct PDF-style embed preview is not available for Word files.</p>
                        </div>
                        <div style={{ display: 'flex', gap: '10px' }}>
                          <button 
                            type="button"
                            onClick={handleDownload} 
                            className="review-fallback-btn"
                          >
                            <Download size={14} /> Download Original Resume
                          </button>
                          <button 
                            type="button"
                            onClick={handleOpenNewTab} 
                            className="review-fallback-btn secondary"
                          >
                            <ExternalLink size={14} /> Open Original Resume
                          </button>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          )}

          {activeTab === 'profile' && (
            <div 
              id="panel-profile" 
              role="tabpanel" 
              style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}
            >
              {profileLoading && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div className="ai-skeleton-bar" style={{ height: '80px', width: '100%' }} />
                  <div className="ai-skeleton-bar" style={{ height: '100px', width: '100%' }} />
                  <div className="ai-skeleton-bar" style={{ height: '100px', width: '100%' }} />
                </div>
              )}

              {profileError && !profileLoading && (
                <div className="ai-drawer-error-state">
                  <ShieldAlert size={36} style={{ color: '#DC2626' }} />
                  <p>{profileError}</p>
                  <button type="button" onClick={handleRetry} className="ai-drawer-error-btn">
                    Retry
                  </button>
                </div>
              )}

              {!profileLoading && !profileError && profile && (
                <>
                  {/* Summary */}
                  {profile.summary && (
                    <div className="profile-section">
                      <h3>Summary</h3>
                      <p className="profile-detail-text">{profile.summary}</p>
                    </div>
                  )}

                  {/* Skills */}
                  {profile.skills && profile.skills.length > 0 && (
                    <div className="profile-section">
                      <h3>Skills</h3>
                      <div className="hr-skills-list">
                        {profile.skills.map(s => (
                          <span key={s} className="hr-skill-badge" style={{ backgroundColor: '#F1F5F9', color: '#475569' }}>
                            {s}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Education */}
                  {profile.education && (
                    <div className="profile-section">
                      <h3>Education</h3>
                      <p className="profile-detail-text">{profile.education}</p>
                    </div>
                  )}

                  {/* Experience */}
                  {profile.experience && (
                    <div className="profile-section">
                      <h3>Experience</h3>
                      <p className="profile-detail-text">{profile.experience}</p>
                    </div>
                  )}

                  {/* Projects */}
                  {profile.projects && (
                    <div className="profile-section">
                      <h3>Projects</h3>
                      <p className="profile-detail-text">{profile.projects}</p>
                    </div>
                  )}

                  {/* Certifications */}
                  {profile.certifications && (
                    <div className="profile-section">
                      <h3>Certifications</h3>
                      <p className="profile-detail-text">{profile.certifications}</p>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>

        {/* Drawer Footer */}
        <div className="review-drawer-footer">
          <button 
            onClick={() => onStatusUpdate(candidate.id, 'Shortlisted')}
            className="review-footer-btn primary"
            type="button"
          >
            Shortlist
          </button>
          <button 
            onClick={() => onStatusUpdate(candidate.id, 'Rejected')}
            className="review-footer-btn secondary"
            type="button"
          >
            Reject
          </button>
        </div>
      </aside>
    </>
  );
};

export default ResumeReviewDrawer;
