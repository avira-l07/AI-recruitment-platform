import React, { useState, useEffect, useCallback } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  FileUp,
  Briefcase,
  Star,
  Bell,
  LogOut,
  Sparkles,
  UploadCloud,
  CheckCircle2,
  RefreshCw,
  Search,
  SlidersHorizontal,
  X,
  Clock,
  ThumbsUp,
  Eye,
  CalendarCheck,
  Ban,
  ChevronRight,
  BadgeCheck,
} from "lucide-react";
import authService from "../../services/authService";
import resumeService from "../../services/resumeService";
import matchingService from "../../services/matchingService";
import jobService from "../../services/jobService";
import prescreeningService from "../../services/prescreeningService";
import LoadingSpinner from "../../components/LoadingSpinner";
import CandidatePrescreeningModal from "../../components/prescreening/CandidatePrescreeningModal";
import "./CandidateDashboard.css";

// Helper to normalize lists
const normalizeList = (value) => {
  if (!value) return [];
  if (Array.isArray(value)) return value;
  if (typeof value === "string") {
    const trimmed = value.trim();
    if (trimmed.startsWith("[")) {
      try {
        const parsed = JSON.parse(trimmed);
        if (Array.isArray(parsed)) return parsed;
      } catch (e) {
        /* fallback */
      }
    }
    return trimmed.split(",").map((s) => s.trim()).filter(Boolean);
  }
  return [];
};

// Fallback logic for Career Suggestions
const buildLocalCareerSuggestions = (skillsStr) => {
  const userSkills = normalizeList(skillsStr).map((s) => s.toLowerCase());
  const predefined = [
    {
      field: "AI/ML Intern",
      skills: ["python", "machine learning", "artificial intelligence", "generative ai", "nlp", "pandas", "numpy", "scikit-learn"],
    },
    {
      field: "Software Developer",
      skills: ["c", "c++", "java", "python", "dsa", "oop", "git", "github"],
    },
    {
      field: "Data Analyst",
      skills: ["python", "sql", "pandas", "numpy", "data analysis", "excel", "visualization"],
    },
    {
      field: "Backend Developer",
      skills: ["python", "fastapi", "django", "flask", "sql", "postgresql", "mongodb", "rest api"],
    },
    {
      field: "Frontend Developer",
      skills: ["react", "javascript", "html", "css", "tailwind css", "bootstrap", "rest api"],
    },
  ];

  const suggestions = predefined.map((job) => {
    const matchedSkills = job.skills.filter((req) =>
      userSkills.some((userSk) => userSk.includes(req) || req.includes(userSk))
    );
    const recommendedSkills = job.skills.filter((req) => !matchedSkills.includes(req));
    const fitScore = Math.round((matchedSkills.length / job.skills.length) * 100) || 0;

    let fitLabel = "Explore";
    if (fitScore >= 80) fitLabel = "Strong Fit";
    else if (fitScore >= 50) fitLabel = "Good Fit";

    const capitalize = (str) => str.replace(/\b\w/g, (l) => l.toUpperCase());

    return {
      career_field: job.field,
      fit_score: fitScore,
      fit_label: fitLabel,
      matched_skills: matchedSkills.map(capitalize),
      recommended_skills: recommendedSkills.map(capitalize),
      reason:
        matchedSkills.length > 0
          ? `Based on your resume, you have ${matchedSkills.length} matching skills.`
          : `Consider learning foundational skills.`,
      description: `Explore opportunities as a ${job.field}.`,
      roadmap: [
        `Practice and build 2-3 projects matching core ${job.field} technologies.`,
        `Upload and highlight your certification in these skills.`,
      ],
    };
  });

  return suggestions.sort((a, b) => b.fit_score - a.fit_score).slice(0, 4);
};

// Mock notifications (using user's structures + real updates can be injected!)
const MOCK_NOTIFICATIONS = [];

const NOTIF_META = {
  shortlist: { icon: <ThumbsUp size={15} />, tone: "mint" },
  interview: { icon: <CalendarCheck size={15} />, tone: "indigo" },
  view: { icon: <Eye size={15} />, tone: "amber" },
  reject: { icon: <Ban size={15} />, tone: "muted" },
};

// Sub-components

function FitPill({ fit, score }) {
  const tone = score >= 80 ? "mint" : score >= 60 ? "amber" : "muted";
  return (
    <span className={`ra2-pill ra2-pill-${tone}`}>
      {fit} · {score}%
    </span>
  );
}

function ScoreBar({ score }) {
  const tone = score >= 80 ? "mint" : score >= 60 ? "amber" : "indigo";
  return (
    <div className="ra2-bar">
      <div className={`ra2-bar-fill ra2-bar-${tone}`} style={{ width: `${score}%` }} />
    </div>
  );
}

function EmptyState({ icon, title, copy, actionLabel, onAction }) {
  return (
    <div className="ra2-empty">
      <div className="ra2-empty-icon">{icon}</div>
      <p>{copy}</p>
      {actionLabel && (
        <button className="ra2-btn ra2-btn-indigo" onClick={onAction}>
          {actionLabel} <ChevronRight size={15} />
        </button>
      )}
    </div>
  );
}

// ----------------------------------------------------------------------
// Page: Dashboard
// ----------------------------------------------------------------------
function DashboardTab({ 
  name, 
  resumeData, 
  careerSuggestions, 
  careerSource, 
  careerLoading, 
  shortlistedCount, 
  pendingCount, 
  matchCount, 
  onGo, 
  onGenerateGemini, 
  retryingGemini,
  careerStatus,
  careerError,
  aiInsights,
  generationCooldown
}) {
  const skills = normalizeList(resumeData?.skills);

  const getStatusBadge = () => {
    if (careerStatus === "generating") {
      return (
        <span className="ra2-badge-ai" style={{ backgroundColor: "var(--color-indigo-100)", color: "var(--indigo)" }}>
          <RefreshCw size={12} className="ra2-spin" style={{ marginRight: "4px" }} /> Generating AI Suggestions...
        </span>
      );
    }
    if (careerStatus === "completed" || careerSource === "hybrid") {
      return (
        <span className="ra2-badge-ai" style={{ backgroundColor: "#ecfdf5", color: "#047857" }}>
          <Sparkles size={12} style={{ marginRight: "4px" }} /> Hybrid AI Analysis (Enhanced)
        </span>
      );
    }
    if (careerStatus === "failed") {
      return (
        <span className="ra2-badge-ai" style={{ backgroundColor: "#fef2f2", color: "#b91c1c" }}>
          <Ban size={12} style={{ marginRight: "4px" }} /> AI Quota Exhausted / Failed
        </span>
      );
    }
    return (
      <span className="ra2-badge-ai" style={{ backgroundColor: "#f1f5f9", color: "#475569" }}>
        Local Analysis Active
      </span>
    );
  };

  return (
    <div className="ra2-page">
      <div className="ra2-page-head">
        <div>
          <h1 className="ra2-display">Welcome, {name}</h1>
          <p className="ra2-sub">Track your job matches and explore AI career suggestions</p>
        </div>
        <button className="ra2-btn ra2-btn-indigo" onClick={() => onGo("upload")}>
          <UploadCloud size={16} /> Update resume
        </button>
      </div>

      {/* Top Stats Row */}
      <div className="ra2-stat-row">
        <div className="ra2-stat-card">
          <span className="ra2-stat-label">Job matches</span>
          <span className="ra2-stat-num ra2-num-indigo">{matchCount}</span>
          <span className="ra2-stat-trend">Based on active database roles</span>
        </div>
        <div className="ra2-stat-card">
          <span className="ra2-stat-label">Shortlisted</span>
          <span className="ra2-stat-num ra2-num-mint">{shortlistedCount}</span>
          <span className="ra2-stat-trend">Recruiter-approved fits</span>
        </div>
        <div className="ra2-stat-card">
          <span className="ra2-stat-label">Pending review</span>
          <span className="ra2-stat-num ra2-num-amber">{pendingCount}</span>
          <span className="ra2-stat-trend">Awaiting recruiter feedback</span>
        </div>
      </div>

      {/* Explicit Generation Banner */}
      {resumeData && (careerStatus === "local_ready" || careerStatus === "failed" || careerStatus === "not_generated") && (
        <div style={{ backgroundColor: "#f8fafc", border: "1px solid #e2e8f0", padding: "20px", borderRadius: "12px", marginBottom: "24px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "16px" }}>
            <div style={{ flex: 1, minWidth: "280px" }}>
              <strong style={{ display: "block", fontSize: "15px", color: "#0f172a", marginBottom: "4px" }}>
                {careerStatus === "failed" ? "AI Suggestions Failed / Quota Exhausted" : "Enhance Suggestions with Gemini AI"}
              </strong>
              <span style={{ fontSize: "13.5px", color: "#64748b", lineHeight: "1.5" }}>
                {careerError || "Generate deeply personalized Gemini descriptions, roadmap milestones, and semantic analysis matched to your background."}
              </span>
            </div>
            <button
              onClick={() => onGenerateGemini(true)}
              disabled={retryingGemini || generationCooldown > 0}
              className="ra2-btn ra2-btn-indigo"
              style={{ minWidth: "160px", padding: "10px 20px" }}
            >
              {retryingGemini ? (
                <>
                  <RefreshCw size={14} className="ra2-spin" style={{ marginRight: "6px" }} /> Generating...
                </>
              ) : generationCooldown > 0 ? (
                `Retry in ${generationCooldown}s`
              ) : (
                "Generate AI Suggs"
              )}
            </button>
          </div>
        </div>
      )}

      {/* Two Column Grid: Skills & AI Suggestion */}
      <div className="ra2-two-col">
        <div className="ra2-card">
          <h3>Resume profile</h3>
          {resumeData ? (
            <>
              <div className="ra2-uploaded-chip">
                <CheckCircle2 size={15} /> Resume uploaded and parsed
              </div>
              <div className="ra2-label-eyebrow">Skills</div>
              <div className="ra2-skill-wrap" style={{ marginBottom: "20px" }}>
                {skills.length > 0 ? (
                  skills.map((s, i) => (
                    <span key={i} className="ra2-skill">
                      {s}
                    </span>
                  ))
                ) : (
                  <span style={{ color: "var(--muted)" }}>No skills listed</span>
                )}
              </div>
              {resumeData.education && (
                <div style={{ marginBottom: "16px" }}>
                  <div className="ra2-label-eyebrow">Education</div>
                  <p style={{ margin: 0, fontSize: "13.5px" }}>{resumeData.education}</p>
                </div>
              )}
              {resumeData.experience && (
                <div>
                  <div className="ra2-label-eyebrow">Experience</div>
                  <p style={{ margin: 0, fontSize: "13.5px", lineHeight: "1.4" }}>{resumeData.experience}</p>
                </div>
              )}
            </>
          ) : (
            <div className="ra2-empty" style={{ padding: "20px 0" }}>
              <p>No resume uploaded yet. Upload your resume to unlock AI insights.</p>
              <button className="ra2-btn ra2-btn-indigo" onClick={() => onGo("upload")}>
                Upload Resume
              </button>
            </div>
          )}
        </div>

        <div className="ra2-card">
          <div className="ra2-card-head-row" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
            <h3 style={{ margin: 0 }}>Career field suggestions</h3>
            {getStatusBadge()}
          </div>

          {careerLoading ? (
            <div style={{ textAlign: "center", padding: "40px" }}>
              <RefreshCw size={24} className="ra2-spin" style={{ color: "var(--indigo)" }} />
              <p style={{ marginTop: "12px", color: "var(--muted)", fontSize: "14px" }}>Analyzing career fits...</p>
            </div>
          ) : careerSuggestions && careerSuggestions.length > 0 ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
              {careerSuggestions.map((sug, idx) => {
                const score = Math.max(0, Math.min(100, sug.fit_score || sug.fitScore || 0));
                const fitLabel = sug.fit_label || sug.fitLabel || "Explore";
                const matchedSkills = sug.matched_skills || sug.matchedSkills || [];
                const recommendedSkills = sug.recommended_skills || sug.recommendedSkills || [];
                const roadmap = sug.roadmap || [];

                return (
                  <div key={idx} className="ra2-suggestion" style={{ borderBottom: idx < careerSuggestions.length - 1 ? "1px solid var(--line)" : "none", paddingBottom: idx < careerSuggestions.length - 1 ? "20px" : "0" }}>
                    <div className="ra2-suggestion-top">
                      <h4>{sug.career_field || sug.careerField}</h4>
                      <FitPill fit={fitLabel} score={score} />
                    </div>
                    <ScoreBar score={score} />
                    {sug.description && <p className="ra2-suggestion-copy">{sug.description}</p>}
                    {sug.reason && (
                      <p className="ra2-suggestion-copy">
                        <b>Why:</b> {sug.reason}
                      </p>
                    )}
                    {sug.ai_analysis && (
                      <p className="ra2-suggestion-copy">
                        <b>AI Analysis:</b> {sug.ai_analysis}
                      </p>
                    )}
                    
                    {Array.isArray(roadmap) && roadmap.length > 0 && (
                      <div className="ra2-roadmap">
                        <div className="ra2-roadmap-head">
                          <BadgeCheck size={15} /> AI Roadmap
                        </div>
                        <ul>
                          {roadmap.slice(0, 4).map((step, i) => (
                            <li key={i}>{step}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    <div className="ra2-skill-wrap" style={{ marginTop: "12px" }}>
                      {matchedSkills.map((sk, i) => (
                        <span key={`match-${i}`} className="ra2-skill" style={{ background: "var(--mint-soft)", color: "#1F7A54" }}>
                          {sk}
                        </span>
                      ))}
                      {recommendedSkills.map((sk, i) => (
                        <span key={`rec-${i}`} className="ra2-skill ra2-skill-missing">
                          {sk}
                        </span>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="ra2-empty" style={{ padding: "20px 0" }}>
              <p>No career suggestions available. Update your resume to explore paths.</p>
            </div>
          )}
        </div>
      </div>

      {/* AI Resume Intelligence Tips */}
      {aiInsights && (
        <div className="ra2-card" style={{ marginTop: "24px" }}>
          <h3 style={{ display: "flex", alignItems: "center", gap: "8px", margin: "0 0 16px 0" }}>
            <Sparkles size={16} style={{ color: "var(--amber)" }} /> AI Resume Intelligence & Tips
          </h3>
          <p style={{ color: "#334155", fontSize: "14px", lineHeight: "1.6", margin: "0 0 16px 0" }}>
            {aiInsights.candidateSummary}
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
            <div>
              <strong style={{ fontSize: "13.5px", color: "#0f172a" }}>Resume Strengths</strong>
              <ul style={{ paddingLeft: "18px", fontSize: "13px", color: "#475569", lineHeight: "1.6", margin: "8px 0 0 0" }}>
                {(aiInsights.strengths || []).map((x, i) => (
                  <li key={i}>{x}</li>
                ))}
              </ul>
            </div>
            <div>
              <strong style={{ fontSize: "13.5px", color: "#0f172a" }}>Improvement Tips</strong>
              <ul style={{ paddingLeft: "18px", fontSize: "13px", color: "#475569", lineHeight: "1.6", margin: "8px 0 0 0" }}>
                {(aiInsights.resumeImprovementTips || aiInsights.weaknesses || []).map((x, i) => (
                  <li key={i}>{x}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ----------------------------------------------------------------------
// Page: Upload Resume
// ----------------------------------------------------------------------
function UploadResumeTab({ userId, onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [status, setStatus] = useState("idle"); // idle | validating | done
  const [error, setError] = useState("");
  const [parsedInfo, setParsedInfo] = useState(null);
  const [quality, setQuality] = useState(null);
  const [aiInsights, setAiInsights] = useState(null);

  const onFiles = (files) => {
    const selected = files?.[0];
    setError("");
    setParsedInfo(null);
    setQuality(null);
    setAiInsights(null);

    if (!selected) return;
    const validExt = selected.name.toLowerCase().endsWith(".pdf") || selected.name.toLowerCase().endsWith(".docx");
    if (!validExt) {
      setFile(null);
      setError("Only PDF and DOCX resume files are allowed.");
      return;
    }
    if (selected.size > 5 * 1024 * 1024) {
      setFile(null);
      setError("File is too large. Maximum allowed size is 5 MB.");
      return;
    }
    if (selected.size < 200) {
      setFile(null);
      setError("File is too small. Upload a complete resume, not only a few words.");
      return;
    }
    setFile(selected);
    setStatus("idle");
  };

  const handleValidate = async () => {
    if (!file || !userId) return;
    setStatus("validating");
    setError("");

    try {
      const data = await resumeService.uploadResume(userId, file);
      setStatus("done");
      setParsedInfo(data.parsedResult || null);
      setQuality(data.resumeQuality || data.parsedResult?.quality || null);
      setAiInsights(data.aiInsights || data.parsedResult?.ai_insights || null);
      if (onUploadSuccess) {
        onUploadSuccess();
      }
    } catch (err) {
      setStatus("idle");
      setError(err.message || "Failed to upload and validate resume. Please try again.");
    }
  };

  const errorLines = error ? error.split("\n").filter(Boolean) : [];

  return (
    <div className="ra2-page">
      <div className="ra2-page-head">
        <div>
          <h1 className="ra2-display">Upload your resume</h1>
          <p className="ra2-sub">
            The platform accepts only complete professional resumes. Empty or keyword-stuffed
            PDFs will be rejected.
          </p>
        </div>
      </div>

      <div className="ra2-card" style={{ maxWidth: 640 }}>
        <div className="ra2-checklist">
          <div className="ra2-label-eyebrow">Professional resume checks</div>
          <ul>
            <li>
              <CheckCircle2 size={14} /> Name and contact signal
            </li>
            <li>
              <CheckCircle2 size={14} /> Enough readable text
            </li>
            <li>
              <CheckCircle2 size={14} /> Education, projects, experience, or certification section
            </li>
            <li>
              <CheckCircle2 size={14} /> Real skill evidence, not only random keywords
            </li>
          </ul>
        </div>

        <label
          className={`ra2-dropzone ${dragOver ? "ra2-dropzone-active" : ""}`}
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            onFiles(e.dataTransfer.files);
          }}
        >
          <UploadCloud size={26} />
          <div>
            <strong>{file ? file.name : "Drag & drop your resume here"}</strong>
            <span>{file ? "Ready to validate" : "PDF or DOCX — or click to browse"}</span>
          </div>
          <input
            type="file"
            accept=".pdf,.docx"
            style={{ display: "none" }}
            onChange={(e) => onFiles(e.target.files)}
          />
        </label>

        {error && (
          <div style={{ backgroundColor: "#FEECEC", border: "1px solid #FCA5A5", color: "#991B1B", padding: "14px", borderRadius: "10px", marginTop: "16px" }}>
            <strong>Resume rejected / upload failed:</strong>
            <ul style={{ margin: "8px 0 0 18px", paddingLeft: "10px", lineHeight: "1.6", listStyle: "disc" }}>
              {errorLines.map((line, idx) => (
                <li key={idx} style={{ fontSize: "13px" }}>{line}</li>
              ))}
            </ul>
          </div>
        )}

        <button
          className="ra2-btn ra2-btn-indigo ra2-btn-block"
          onClick={handleValidate}
          disabled={!file || status === "validating"}
        >
          {status === "validating" ? (
            <>
              <RefreshCw size={16} className="ra2-spin" /> Validating & generating insights…
            </>
          ) : (
            "Validate resume + generate AI insights"
          )}
        </button>

        {status === "done" && (
          <div className="ra2-inline-success">
            <CheckCircle2 size={15} /> Resume parsed successfully. {parsedInfo?.skills?.length ? `${parsedInfo.skills.length} skills detected.` : ""} Head to the Dashboard to see your suggestions.
          </div>
        )}

        {/* Quality results card */}
        {quality && (
          <div className="ra2-card" style={{ marginTop: "24px", background: "#FDFDFD" }}>
            <div className="ra2-label-eyebrow">Resume Quality Score</div>
            <p style={{ fontSize: "2rem", fontWeight: 700, margin: "4px 0", fontFamily: "Space Grotesk, sans-serif" }}>
              {quality.quality_score}%
            </p>
            <span className={`ra2-pill ${quality.accepted ? "ra2-pill-mint" : "ra2-pill-muted"}`}>
              {quality.accepted ? "Accepted for matching" : "Not accepted"}
            </span>
            {quality.reasons?.length > 0 && (
              <ul style={{ color: "var(--muted)", margin: "14px 0 0 18px", fontSize: "13px", paddingLeft: "0", lineHeight: "1.6" }}>
                {quality.reasons.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            )}
          </div>
        )}

        {/* AI resume review suggestions */}
        {aiInsights && (
          <div className="ra2-card" style={{ marginTop: "20px" }}>
            <div className="ra2-roadmap-head" style={{ justifyContent: "space-between", width: "100%", display: "flex", alignItems: "center" }}>
              <span style={{ display: "flex", alignItems: "center", gap: "6px" }}><Sparkles size={15} style={{ color: "var(--amber)" }} /> AI Resume Review</span>
              <span className="ra2-badge-ai" style={{ fontSize: "11px", padding: "2px 8px" }}>
                {aiInsights?.source === "gemini_text_enhanced" ? "Gemini Summary" : "Local AI Result — Gemini Unavailable"}
              </span>
            </div>
            <p style={{ color: "var(--muted)", fontSize: "13.5px", lineHeight: "1.6" }}>{aiInsights.candidateSummary}</p>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginTop: "16px" }}>
              <div>
                <strong>Strengths</strong>
                <ul style={{ paddingLeft: "18px", fontSize: "12.5px", color: "#334", lineHeight: "1.6", margin: "8px 0 0 0" }}>
                  {(aiInsights.strengths || []).map((x, i) => (
                    <li key={i}>{x}</li>
                  ))}
                </ul>
              </div>
              <div>
                <strong>Improvement Tips</strong>
                <ul style={{ paddingLeft: "18px", fontSize: "12.5px", color: "#334", lineHeight: "1.6", margin: "8px 0 0 0" }}>
                  {(aiInsights.resumeImprovementTips || []).map((x, i) => (
                    <li key={i}>{x}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ----------------------------------------------------------------------
// Component: Job Card in Browse Jobs
// ----------------------------------------------------------------------
function BrowseJobCard({ job, onApply, isApplying, hasApplied }) {
  const [open, setOpen] = useState(false);
  const score = Math.max(0, Math.min(100, job.score || 0));
  const missing = job.missing_skills || job.missingSkills || [];
  const matched = job.matched_skills || job.matchedSkills || [];

  let fitLabel = "Possible fit";
  if (score >= 80) fitLabel = "Strong fit";
  else if (score >= 65) fitLabel = "Good fit";

  return (
    <div className="ra2-card ra2-job-card">
      <div className="ra2-job-top">
        <div>
          <h3>{job.title}</h3>
          {job.company && <p className="ra2-job-blurb" style={{ fontWeight: 600 }}>{job.company}</p>}
          {job.description && <p className="ra2-job-blurb" style={{ marginTop: "4px" }}>{job.description.slice(0, 160)}{job.description.length > 160 ? "..." : ""}</p>}
        </div>
        <FitPill fit={fitLabel} score={score} />
      </div>
      <ScoreBar score={score} />

      {job.aiSemanticAnalysis && (
        <>
          <button className="ra2-ai-toggle" onClick={() => setOpen((o) => !o)}>
            <Sparkles size={13} /> AI match understanding
            <ChevronRight size={14} className={open ? "ra2-chevron-open" : ""} style={{ marginLeft: "4px" }} />
          </button>
          
          {open && (
            <div className="ra2-ai-note">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid rgba(0,0,0,0.06)", paddingBottom: "6px", marginBottom: "8px", fontSize: "11px", color: "var(--muted)" }}>
                <span>AI Match Explanation</span>
                <span style={{ fontWeight: 600 }}>{job.aiSource === "gemini_text_enhanced" ? "Hybrid AI Recommendation" : "Local AI Result — Gemini Unavailable"}</span>
              </div>
              {job.aiSemanticAnalysis}
            </div>
          )}
        </>
      )}

      <div className="ra2-job-meta">
        {job.experience_level && (
          <span>
            <b>Experience:</b> {job.experience_level}
          </span>
        )}
        {job.education_requirement && (
          <span>
            <b>Education:</b> {job.education_requirement}
          </span>
        )}
      </div>

      <div className="ra2-skill-wrap">
        {matched.map((s) => (
          <span key={s} className="ra2-skill">
            {s}
          </span>
        ))}
        {missing.map((s) => (
          <span key={s} className="ra2-skill ra2-skill-missing">
            {s}
          </span>
        ))}
      </div>

      <button
        className="ra2-btn ra2-btn-indigo"
        disabled={hasApplied || isApplying}
        onClick={() => onApply(job.job_id)}
        style={hasApplied ? { background: "var(--mint)", border: "none" } : undefined}
      >
        {hasApplied ? "✓ Applied" : isApplying ? "Applying..." : "Apply"}
      </button>
    </div>
  );
}

// ----------------------------------------------------------------------
// Page: Browse Jobs
// ----------------------------------------------------------------------
function BrowseJobsTab({ jobs, loading, error, onRefresh, onApply, applyingId, appliedIds }) {
  const [query, setQuery] = useState("");
  const filtered = jobs.filter((j) => (j.title || "").toLowerCase().includes(query.toLowerCase()));

  return (
    <div className="ra2-page">
      <div className="ra2-page-head">
        <div>
          <h1 className="ra2-display">Jobs for you</h1>
          <p className="ra2-sub">AI-ranked roles based on direct skills, semantic fit, and resume evidence</p>
        </div>
        <button className="ra2-btn ra2-btn-indigo" onClick={onRefresh}>
          <RefreshCw size={15} /> Refresh
        </button>
      </div>

      <div className="ra2-search-row">
        <div className="ra2-search-box">
          <Search size={15} />
          <input
            placeholder="Search roles…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          {query && <X size={14} className="ra2-search-clear" onClick={() => setQuery("")} />}
        </div>
        <button className="ra2-btn ra2-btn-ghost">
          <SlidersHorizontal size={15} /> Filters
        </button>
      </div>

      {error && (
        <div style={{ background: "#FEECEC", border: "1px solid #FCA5A5", color: "#991B1B", padding: "12px 16px", borderRadius: "8px", marginBottom: "20px", fontSize: "14px" }}>
          {error}
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: "center", padding: "60px" }}>
          <RefreshCw size={28} className="ra2-spin" style={{ color: "var(--indigo)" }} />
          <p style={{ marginTop: "12px", color: "var(--muted)" }}>Finding jobs that fit your resume...</p>
        </div>
      ) : (
        <>
          <p className="ra2-result-count">{filtered.length} matching roles</p>

          {filtered.length === 0 ? (
            <div className="ra2-card">
              <EmptyState
                icon={<Briefcase size={22} />}
                copy="No matching jobs found. Consider updating your resume to match more opportunities."
              />
            </div>
          ) : (
            <div className="ra2-job-list">
              {filtered.map((j) => (
                <BrowseJobCard
                  key={j.job_id}
                  job={j}
                  onApply={onApply}
                  isApplying={applyingId === j.job_id}
                  hasApplied={appliedIds.has(j.job_id)}
                />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ----------------------------------------------------------------------
// Page: My Matches
// ----------------------------------------------------------------------
function MyMatchesTab({ matches, onGo }) {
  // Filter matches that are shortlisted
  const shortlisted = matches.filter((m) => (m.status || "").toLowerCase() === "shortlisted");

  return (
    <div className="ra2-page">
      <div className="ra2-page-head">
        <div>
          <h1 className="ra2-display">My official job matches</h1>
          <p className="ra2-sub">Roles a recruiter has formally shortlisted you for.</p>
        </div>
      </div>

      {shortlisted.length === 0 ? (
        <div className="ra2-card">
          <EmptyState
            icon={<Briefcase size={22} />}
            copy="No official job matches have been generated yet. Your career suggestions are available on the Dashboard tab."
            actionLabel="See suggestions"
            onAction={() => onGo("dashboard")}
          />
        </div>
      ) : (
        <div className="ra2-matches-table">
          {shortlisted.map((m) => {
            const score = Math.max(0, Math.min(100, m.matchScore ?? m.score ?? m.match_score ?? 0));
            let fitLabel = "Possible fit";
            if (score >= 80) fitLabel = "Strong fit";
            else if (score >= 65) fitLabel = "Good fit";

            return (
              <div key={m.id || m.jobTitle} className="ra2-match-row">
                <div className="ra2-match-row-main">
                  <span className="ra2-match-row-title">{m.jobTitle || m.matchedJob || "Untitled Role"}</span>
                  {m.explanation && <span className="ra2-match-row-sub">{m.explanation}</span>}
                </div>
                <FitPill fit={fitLabel} score={score} />
                <span className="ra2-status-badge ra2-status-shortlisted">Shortlisted</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ----------------------------------------------------------------------
// Page: Notifications
// ----------------------------------------------------------------------
function NotificationsTab({ notifications, onMarkAllRead }) {
  const hasAny = notifications.length > 0;

  return (
    <div className="ra2-page">
      <div className="ra2-page-head">
        <div>
          <h1 className="ra2-display">Notifications</h1>
          <p className="ra2-sub">Updates about shortlisted jobs and interview status appear here.</p>
        </div>
        {hasAny && (
          <button className="ra2-btn ra2-btn-ghost" onClick={onMarkAllRead}>
            Mark all read
          </button>
        )}
      </div>

      {!hasAny ? (
        <div className="ra2-card">
          <EmptyState
            icon={<Bell size={22} />}
            copy="No notifications yet. Updates about shortlisted jobs and interview status will appear here."
          />
        </div>
      ) : (
        <div className="ra2-card ra2-notif-list">
          {notifications.map((n) => {
            const meta = NOTIF_META[n.type] || NOTIF_META["shortlist"];
            return (
              <div key={n.id} className={`ra2-notif-row ${n.read ? "" : "ra2-notif-unread"}`}>
                <span className={`ra2-notif-icon ra2-tone-${meta.tone}`}>{meta.icon}</span>
                <div className="ra2-notif-body">
                  <span className="ra2-notif-title">{n.title}</span>
                  <span className="ra2-notif-time">
                    <Clock size={11} /> {n.time}
                  </span>
                </div>
                {!n.read && <span className="ra2-notif-dot" />}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ----------------------------------------------------------------------
// Main Portal Component
// ----------------------------------------------------------------------
export default function CandidateDashboard() {
  const navigate = useNavigate();
  const location = useLocation();
  const user = authService.getCurrentUser() || {};
  const userId = user?.id ?? user?.user_id ?? user?.candidate_id;

  const getInitialTab = useCallback(() => {
    if (location.pathname === "/candidate/upload") return "upload";
    if (location.pathname === "/candidate/jobs") return "browse";
    return "dashboard";
  }, [location.pathname]);

  const [page, setPage] = useState(getInitialTab());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [resumeData, setResumeData] = useState(null);
  const [matches, setMatches] = useState([]);
  const [careerSuggestions, setCareerSuggestions] = useState([]);
  const [careerSource, setCareerSource] = useState("");
  const [careerLoading, setCareerLoading] = useState(false);
  const [retryingGemini, setRetryingGemini] = useState(false);

  const [careerStatus, setCareerStatus] = useState("local_ready");
  const [careerError, setCareerError] = useState(null);
  const [dashboardAiInsights, setDashboardAiInsights] = useState(null);
  const [generationCooldown, setGenerationCooldown] = useState(0);

  // Recommended jobs and apply states
  const [jobs, setJobs] = useState([]);
  const [jobsLoading, setJobsLoading] = useState(false);
  const [jobsError, setJobsError] = useState(null);
  const [applyingId, setApplyingId] = useState(null);
  const [appliedIds, setAppliedIds] = useState(new Set());
  const [activePrescreeningJob, setActivePrescreeningJob] = useState(null);
  const [prescreeningQuestions, setPrescreeningQuestions] = useState([]);
  const [isSubmittingPrescreening, setIsSubmittingPrescreening] = useState(false);

  const [notifications, setNotifications] = useState([]);
  const unreadNotifCount = notifications.filter((n) => !n.read).length;

  useEffect(() => {
    if (generationCooldown > 0) {
      const timer = setTimeout(() => setGenerationCooldown((prev) => prev - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [generationCooldown]);

  useEffect(() => {
    const activeShortlists = matches.filter((m) => (m.status || "").toLowerCase() === "shortlisted");
    setNotifications((prev) => {
      const readSet = new Set(prev.filter((n) => n.read).map((n) => n.id));
      return activeShortlists.map((m, idx) => {
        const id = 100 + idx;
        return {
          id,
          type: "shortlist",
          title: `You were shortlisted for ${m.jobTitle || m.matchedJob}`,
          time: "Just now",
          read: readSet.has(id),
        };
      });
    });
  }, [matches]);

  const handleMarkAllRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  const handleGenerateGemini = async (force = false) => {
    if (!userId || generationCooldown > 0) return;
    setRetryingGemini(true);
    setCareerError(null);
    setCareerStatus("generating");
    try {
      const res = await resumeService.generateCareerSuggestions(userId, force);
      if (res) {
        setCareerSuggestions((res.suggestions || []).slice(0, 4));
        setCareerSource(res.source || "hybrid");
        setCareerStatus(res.status || "completed");
        setCareerError(res.safe_error_message || null);
        setDashboardAiInsights(res.aiInsights || null);
        if (res.status === "failed") {
          setGenerationCooldown(60);
        }
      }
    } catch (err) {
      console.error("AI suggestions generation failed:", err);
      setCareerError(err.response?.data?.detail || "AI suggestions generation failed. Please try again.");
      setCareerStatus("failed");
      setGenerationCooldown(60);
    } finally {
      setRetryingGemini(false);
    }
  };

  const handleLogout = () => {
    authService.logout();
    navigate("/login");
  };

  const handlePageChange = (newPage) => {
    setPage(newPage);
    if (newPage === "dashboard") navigate("/candidate/dashboard");
    else if (newPage === "upload") navigate("/candidate/upload");
    else if (newPage === "browse") navigate("/candidate/jobs");
    else navigate("/candidate/dashboard");
  };

  const fetchDashboardData = useCallback(async (showLoader = true) => {
    if (!userId) {
      setLoading(false);
      return;
    }
    if (showLoader) setLoading(true);
    setError(null);

    try {
      // 1. Fetch Resume Data
      let currentResumeData = null;
      try {
        const resumeRes = await resumeService.getResume(userId);
        setResumeData(resumeRes);
        currentResumeData = resumeRes;
      } catch (resumeErr) {
        if (resumeErr.response?.status === 404) setResumeData(null);
        else throw resumeErr;
      }

      // 2. Fetch Matches Data
      const matchRes = await matchingService.getCandidateMatches(userId);
      setMatches(matchRes || []);

      // 3. Fetch Career Suggestions
      if (currentResumeData) {
        setCareerLoading(true);
        try {
          const careerRes = await resumeService.getCareerSuggestions(userId);
          if (careerRes) {
            setCareerSuggestions((careerRes.suggestions || []).slice(0, 4));
            setCareerSource(careerRes.source || "local");
            setCareerStatus(careerRes.status || "local_ready");
            setCareerError(careerRes.safe_error_message || null);
            setDashboardAiInsights(careerRes.aiInsights || null);
          } else {
            setCareerSuggestions(buildLocalCareerSuggestions(currentResumeData.skills));
            setCareerSource("local_fallback");
            setCareerStatus("local_ready");
          }
        } catch (careerErr) {
          console.warn("Career suggestions API failed, using local fallback.", careerErr);
          setCareerSuggestions(buildLocalCareerSuggestions(currentResumeData.skills));
          setCareerSource("local_fallback");
          setCareerStatus("local_ready");
        } finally {
          setCareerLoading(false);
        }
      }
    } catch (err) {
      console.error("API Error in Candidate Portal:", err);
      if (err.response?.status === 401) {
        navigate("/login");
        return;
      }
      setError(err.response?.data?.detail || "Could not connect to the server.");
    } finally {
      if (showLoader) setLoading(false);
    }
  }, [userId, navigate]);

  const loadRecommendedJobs = useCallback(async () => {
    if (!userId) return;
    setJobsLoading(true);
    setJobsError(null);
    try {
      const res = await jobService.getRecommendedJobs(userId);
      setJobs(Array.isArray(res) ? res : []);
    } catch (err) {
      console.error("Failed to load recommended jobs", err);
      if (err.response?.status === 404) {
        setJobs([]);
      } else {
        setJobsError(err.response?.data?.detail || "Could not load job recommendations right now.");
      }
    } finally {
      setJobsLoading(false);
    }
  }, [userId]);

  const handleApply = async (jobId) => {
    if (!userId) return;
    setApplyingId(jobId);
    try {
      // Check if job has pre-screening questions
      try {
        const questions = await prescreeningService.getJobQuestions(jobId);
        if (Array.isArray(questions) && questions.length > 0) {
          const targetJob = jobs.find(j => (j.job_id || j.id) === jobId) || { id: jobId, title: "Job Posting" };
          setActivePrescreeningJob({ id: jobId, title: targetJob.title || "Job Posting" });
          setPrescreeningQuestions(questions);
          setApplyingId(null);
          return;
        }
      } catch (qErr) {
        // If error fetching questions, fallback to normal apply
      }

      await matchingService.applyToJob(userId, jobId);
      setAppliedIds((prev) => new Set(prev).add(jobId));
      // Refresh matches in background
      const matchRes = await matchingService.getCandidateMatches(userId);
      setMatches(matchRes || []);
    } catch (err) {
      console.error("Failed to apply to job", err);
      alert(err.response?.data?.detail || "Could not submit your application. Please try again.");
    } finally {
      setApplyingId(null);
    }
  };

  const handlePrescreeningSubmit = async (answers) => {
    if (!activePrescreeningJob || !userId) return;
    setIsSubmittingPrescreening(true);
    try {
      await matchingService.applyToJob(userId, activePrescreeningJob.id, answers);
      setAppliedIds((prev) => new Set(prev).add(activePrescreeningJob.id));
      const matchRes = await matchingService.getCandidateMatches(userId);
      setMatches(matchRes || []);
      setActivePrescreeningJob(null);
      setPrescreeningQuestions([]);
    } catch (err) {
      console.error("Failed to submit pre-screening application", err);
      alert(err.response?.data?.detail || "Could not submit your application. Please try again.");
    } finally {
      setIsSubmittingPrescreening(false);
    }
  };

  useEffect(() => {
    setPage(getInitialTab());
  }, [location.pathname, getInitialTab]);

  useEffect(() => {
    fetchDashboardData(true);
  }, [fetchDashboardData]);

  useEffect(() => {
    if (page === "browse") {
      loadRecommendedJobs();
    }
  }, [page, loadRecommendedJobs]);

  const onResumeUploaded = () => {
    // Reload dashboard data in background
    fetchDashboardData(false);
  };

  const NAV_ITEMS = [
    { key: "dashboard", label: "Dashboard", icon: <LayoutDashboard size={17} /> },
    { key: "upload", label: "Upload resume", icon: <FileUp size={17} /> },
    { key: "browse", label: "Browse jobs", icon: <Briefcase size={17} /> },
    { key: "matches", label: "My matches", icon: <Star size={17} /> },
    { key: "notifications", label: "Notifications", icon: <Bell size={17} /> },
  ];

  if (loading) return <LoadingSpinner message="Loading your candidate portal..." />;

  const shortlistedCount = matches.filter((m) => (m.status || "").toLowerCase() === "shortlisted").length;
  const pendingCount = matches.filter((m) => (m.status || "").toLowerCase() === "pending").length;

  return (
    <div className="ra2-root">
      {/* --- SIDEBAR NAVIGATION --- */}
      <aside className="ra2-sidebar">
        <div className="ra2-logo">
          <span className="ra2-logo-mark">
            <Sparkles size={13} color="#fff" />
          </span>
          <span className="ra2-display">RecruitAI</span>
        </div>

        <nav className="ra2-nav">
          {NAV_ITEMS.map((n) => (
            <button
              key={n.key}
              className={`ra2-nav-item ${page === n.key ? "active" : ""}`}
              onClick={() => handlePageChange(n.key)}
            >
              {n.icon} {n.label}
              {n.key === "notifications" && unreadNotifCount > 0 && (
                <span className="ra2-nav-badge">{unreadNotifCount}</span>
              )}
            </button>
          ))}
        </nav>

        <div className="ra2-profile">
          <span className="ra2-avatar">
            {(user.name || user.fullName || "C").charAt(0).toUpperCase()}
          </span>
          <div>
            <div className="ra2-profile-name" style={{ maxWidth: "110px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {user.name || user.fullName || "Candidate"}
            </div>
            <div className="ra2-profile-role">Candidate Portal</div>
          </div>
          <button className="ra2-logout" onClick={handleLogout} title="Log Out">
            <LogOut size={16} />
          </button>
        </div>
      </aside>

      {/* --- MAIN CONTENT RENDERER --- */}
      <main className="ra2-main">
        {error ? (
          <div className="ra2-page">
            <div className="ra2-card" style={{ maxWidth: "500px", margin: "40px auto", borderColor: "#FCA5A5", backgroundColor: "#FEECEC", textAlign: "center" }}>
              <h2 style={{ color: "#991B1B", marginBottom: "12px" }}>Connection Error</h2>
              <p style={{ color: "#B91C1C", marginBottom: "24px" }}>{error}</p>
              <button className="ra2-btn ra2-btn-indigo" onClick={() => fetchDashboardData(true)}>
                ↻ Refresh Page
              </button>
            </div>
          </div>
        ) : (
          <>
            {page === "dashboard" && (
              <DashboardTab
                name={user.name || user.fullName || "Candidate"}
                resumeData={resumeData}
                careerSuggestions={careerSuggestions}
                careerSource={careerSource}
                careerLoading={careerLoading}
                shortlistedCount={shortlistedCount}
                pendingCount={pendingCount}
                matchCount={jobs.length || matches.length}
                onGo={handlePageChange}
                onGenerateGemini={handleGenerateGemini}
                retryingGemini={retryingGemini}
                careerStatus={careerStatus}
                careerError={careerError}
                aiInsights={dashboardAiInsights}
                generationCooldown={generationCooldown}
              />
            )}
            {page === "upload" && (
              <UploadResumeTab
                userId={userId}
                onUploadSuccess={onResumeUploaded}
              />
            )}
            {page === "browse" && (
              <BrowseJobsTab
                jobs={jobs}
                loading={jobsLoading}
                error={jobsError}
                onRefresh={loadRecommendedJobs}
                onApply={handleApply}
                applyingId={applyingId}
                appliedIds={appliedIds}
              />
            )}
            {page === "matches" && (
              <MyMatchesTab
                matches={matches}
                onGo={handlePageChange}
              />
            )}
            {page === "notifications" && (
              <NotificationsTab
                notifications={notifications}
                onMarkAllRead={handleMarkAllRead}
              />
            )}
          </>
        )}
      </main>

      {/* Candidate Pre-Screening Questionnaire Modal */}
      {activePrescreeningJob && (
        <CandidatePrescreeningModal
          isOpen={Boolean(activePrescreeningJob)}
          onClose={() => {
            setActivePrescreeningJob(null);
            setPrescreeningQuestions([]);
          }}
          job={activePrescreeningJob}
          questions={prescreeningQuestions}
          onSubmit={handlePrescreeningSubmit}
          isSubmitting={isSubmittingPrescreening}
        />
      )}
    </div>
  );
}
