import React, { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  ScanLine,
  Sparkles,
  LayoutDashboard,
  BarChart3,
  ArrowRight,
  CheckCircle2,
  Upload,
  Users,
  Target,
  Send,
  ClipboardList,
  Filter,
  Trophy,
} from "lucide-react";

import "./LandingPage.css";

/**
 * RecruitAI — Recruitment Intelligence Platform homepage
 *
 * Design tokens
 * -------------
 * Color:
 *   --ink        #0B1220  (base dark / hero, nav)
 *   --ink-soft   #121A2C  (elevated dark surfaces)
 *   --paper      #F5F3EE  (light section background)
 *   --surface    #FFFFFF  (cards on light)
 *   --line       #E5E1D6  (hairline on light)
 *   --line-dark  rgba(255,255,255,0.10) (hairline on dark)
 *   --indigo     #3654E0  (primary action / candidate)
 *   --amber      #F0A63B  (signature / match signal / employer)
 *   --mint       #2FAE79  (success / verified)
 *   --text-muted #7C8598
 *
 * Type: Space Grotesk (display), Inter (body), IBM Plex Mono (data/labels)
 * Signature element: the "Live Match" card in the hero — a resume being
 *   scanned against a job, with a moving scan-line and a score that ticks
 *   up as skill tags resolve. It makes "AI matching" a visible mechanism
 *   instead of an abstract claim.
 */

const SKILLS = ["React", "TypeScript", "SQL", "Team Leadership", "REST APIs", "Figma"];

function useCountUp(target, running, duration = 1400) {
  const [value, setValue] = useState(0);
  const startRef = useRef(null);
  const frameRef = useRef(null);

  useEffect(() => {
    if (!running) return;
    startRef.current = null;
    const step = (ts) => {
      if (startRef.current === null) startRef.current = ts;
      const progress = Math.min((ts - startRef.current) / duration, 1);
      setValue(Math.round(progress * target));
      if (progress < 1) frameRef.current = requestAnimationFrame(step);
    };
    frameRef.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(frameRef.current);
  }, [running, target, duration]);

  return value;
}

function MatchCard() {
  const [visibleSkills, setVisibleSkills] = useState(0);
  const [scoring, setScoring] = useState(false);
  const score = useCountUp(94, scoring);

  useEffect(() => {
    const reveal = setInterval(() => {
      setVisibleSkills((n) => (n < SKILLS.length ? n + 1 : n));
    }, 260);
    const scoreTimer = setTimeout(() => setScoring(true), 700);
    return () => {
      clearInterval(reveal);
      clearTimeout(scoreTimer);
    };
  }, []);

  return (
    <div className="ra-match-card">
      <div className="ra-match-scanline" aria-hidden="true" />
      <div className="ra-match-head">
        <div className="ra-match-avatar">MK</div>
        <div>
          <div className="ra-match-name">Maya Kapoor</div>
          <div className="ra-match-role">Senior Product Engineer</div>
        </div>
        <div className="ra-match-badge">
          <ScanLine size={13} />
          demo
        </div>
      </div>

      <div className="ra-match-body">
        <div className="ra-match-label">matched against</div>
        <div className="ra-match-job">Frontend Lead — Aurora Health</div>

        <div className="ra-match-tags">
          {SKILLS.map((s, i) => (
            <span
              key={s}
              className="ra-tag"
              style={{ opacity: i < visibleSkills ? 1 : 0, transitionDelay: `${i * 40}ms` }}
            >
              <CheckCircle2 size={12} /> {s}
            </span>
          ))}
        </div>
      </div>

      <div className="ra-match-footer">
        <div>
          <div className="ra-match-label">illustrative match score</div>
          <div className="ra-match-score">
            {score}
            <span>%</span>
          </div>
        </div>
        <div className="ra-match-ring" style={{ "--pct": score }}>
          <span>{score >= 90 ? "strong" : "reviewing"}</span>
        </div>
      </div>
    </div>
  );
}

function Feature({ icon, title, copy, id }) {
  return (
    <div className="ra-feature" id={id}>
      <div className="ra-feature-icon">{icon}</div>
      <h3>{title}</h3>
      <p>{copy}</p>
    </div>
  );
}

function TrackStep({ icon, title, copy, last }) {
  return (
    <div className="ra-step">
      <div className="ra-step-marker">
        <span className="ra-step-icon">{icon}</span>
        {!last && <span className="ra-step-line" />}
      </div>
      <div className="ra-step-copy">
        <h4>{title}</h4>
        <p>{copy}</p>
      </div>
    </div>
  );
}

export default function LandingPage() {
  return (
    <div className="ra-root">
      {/* HERO */}
      <header className="ra-hero">
        <div>
          <span className="ra-eyebrow">Recruitment Intelligence Platform</span>
          <h1 className="ra-display">
            Match the right person <em>to the right role</em>.
          </h1>
          <p className="ra-lede">
            RecruitAI reads every resume, scores every candidate against your open roles,
            and gives hiring teams a ranked shortlist backed by evidence — not guesswork.
          </p>
          <div className="ra-hero-actions">
            <Link to="/login?role=candidate" className="ra-btn ra-btn-lg ra-btn-solid-indigo">
              Candidate Portal <ArrowRight size={16} />
            </Link>
            <Link to="/login?role=hr" className="ra-btn ra-btn-lg ra-btn-outline-dark">
              Employer / HR Login
            </Link>
            <Link to="/register" className="ra-btn ra-btn-lg ra-btn-ghost-dark">Register</Link>
          </div>
          <div className="ra-trust">
            <CheckCircle2 size={15} color="#2FAE79" />
            Explainable matching with <b>human review</b> for hiring decisions
          </div>
        </div>
        <MatchCard />
      </header>

      {/* STATS */}
      <section className="ra-stats">
        <div className="ra-stat">
          <div className="ra-stat-num"><span>PDF</span></div>
          <div className="ra-stat-label">supported resume format</div>
        </div>
        <div className="ra-stat">
          <div className="ra-stat-num"><span>DOCX</span></div>
          <div className="ra-stat-label">supported resume format</div>
        </div>
        <div className="ra-stat">
          <div className="ra-stat-num"><span>0–100</span></div>
          <div className="ra-stat-label">explained match scores</div>
        </div>
        <div className="ra-stat">
          <div className="ra-stat-num"><span>HR</span></div>
          <div className="ra-stat-label">reviews every hiring decision</div>
        </div>
      </section>

      {/* FEATURES */}
      <section className="ra-section" id="product">
        <div className="ra-section-head">
          <span className="ra-kicker">Why choose RecruitAI</span>
          <h2 className="ra-display">One platform, every step of hiring</h2>
          <p>From the first resume upload to the final offer, both sides of the table get clarity instead of noise.</p>
        </div>
        <div className="ra-features">
          <Feature
            icon={<Upload size={19} />}
            title="AI Resume Screening"
            copy="Upload a resume and RecruitAI extracts skills, experience, and seniority automatically — no manual tagging."
          />
          <Feature
            icon={<Target size={19} />}
            title="Smart Job Matching"
            copy="Candidates get matched to roles based on real fit, not just keyword overlap, and see why a role was suggested."
          />
          <Feature
            icon={<LayoutDashboard size={19} />}
            title="HR Dashboard"
            copy="Manage every candidate, compare rankings side by side, and move shortlists forward from one screen."
          />
          <Feature
            icon={<BarChart3 size={19} />}
            title="Recruitment Analytics"
            id="analytics"
            copy="See application counts, pipeline stages, skill distribution, and match scores for your roles."
          />
        </div>
      </section>

      {/* HOW IT WORKS — two tracks */}
      <section className="ra-section ra-tracks">
        <div className="ra-section-head">
          <span className="ra-kicker">How it works</span>
          <h2 className="ra-display">Built for both sides of the hire</h2>
          <p>Candidates and hiring teams move through different steps — RecruitAI keeps both moving in parallel.</p>
        </div>
        <div className="ra-tracks-grid">
          <div className="ra-track-candidate" id="candidates">
            <div className="ra-track-head">
              <h3>For Candidates</h3>
              <span className="ra-track-tag">candidate track</span>
            </div>
            <TrackStep icon={<Upload size={15} />} title="Upload your resume" copy="One upload — RecruitAI extracts your skills and experience for you." />
            <TrackStep icon={<Target size={15} />} title="Get matched" copy="See roles ranked by real fit, with a plain-language reason for each match." />
            <TrackStep icon={<Users size={15} />} title="Follow your application" copy="Apply directly and see when the hiring team moves your application to interview." />
            <TrackStep icon={<Trophy size={15} />} title="Get an offer" copy="Track every application's status in one place, right through to the offer." last />
          </div>
          <div className="ra-track-employer" id="employers">
            <div className="ra-track-head">
              <h3>For Employers</h3>
              <span className="ra-track-tag">employer track</span>
            </div>
            <TrackStep icon={<Send size={15} />} title="Post a role" copy="Describe the role once — RecruitAI turns it into a scoring model." />
            <TrackStep icon={<Filter size={15} />} title="Auto-screen applicants" copy="Every applicant is scored and ranked the moment they apply." />
            <TrackStep icon={<ClipboardList size={15} />} title="Shortlist with evidence" copy="Compare candidates side by side with the data behind each score." />
            <TrackStep icon={<Trophy size={15} />} title="Hire with confidence" copy="Move your top pick to offer and see the impact in your analytics." last />
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="ra-cta">
        <h2 className="ra-display">Ready to hire smarter — or get discovered faster?</h2>
        <p>Register as a candidate, or sign in with the HR account provided by your administrator.</p>
        <div className="ra-cta-actions">
          <Link to="/register?role=candidate" className="ra-btn ra-btn-lg ra-btn-solid-indigo">Register as Candidate</Link>
          <Link to="/login?role=hr" className="ra-btn ra-btn-lg ra-btn-solid-amber">Employer / HR Login</Link>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="ra-footer">
        <div className="ra-footer-top">
          <div className="ra-footer-col" style={{ maxWidth: 260 }}>
            <div className="ra-logo" style={{ marginBottom: 12 }}>
              <span className="ra-logo-mark"><Sparkles size={13} color="#fff" /></span>
              <span className="ra-display" style={{ fontSize: 17 }}>RecruitAI</span>
            </div>
            <p style={{ color: "#7C8598", fontSize: 13, lineHeight: 1.6, margin: 0 }}>
              Recruitment intelligence for teams who'd rather look at evidence than guess.
            </p>
          </div>
          <div className="ra-footer-col">
            <h5>Product</h5>
            <a href="#product">Resume Screening</a>
            <a href="#candidates">Job Matching</a>
            <a href="#employers">HR Dashboard</a>
            <a href="#analytics">Analytics</a>
          </div>
          <div className="ra-footer-col">
            <h5>Candidates</h5>
            <Link to="/register">Create Candidate Account</Link>
            <Link to="/login?role=candidate">Candidate Login</Link>
          </div>
          <div className="ra-footer-col">
            <h5>Hiring Teams</h5>
            <Link to="/login?role=hr">HR Login</Link>
          </div>
        </div>
        <div className="ra-footer-bottom">
          <span>© {new Date().getFullYear()} RecruitAI. All rights reserved.</span>
          <span>Made for hiring teams and candidates alike.</span>
        </div>
      </footer>
    </div>
  );
}
