# Recruitment platform audit — October 12, 2026

The project was reviewed across backend access control, authentication,
recruiter ownership, resume handling, matching and prescreening, verification,
blind screening, activity streams, database migrations, frontend navigation,
and dependencies. Verified faults were repaired in the workspace.

This is a source and functional audit. It does not certify deployment security,
AI accuracy, hiring fairness, or performance under production traffic.

## Faults and applied fixes

| Priority | What was wrong | What is fixed |
| --- | --- | --- |
| High | Candidate list/profile and resume-analysis routes allowed HR access beyond their own applicants. | Shared ownership checks require an application to a job owned by that recruiter. Candidate self-access remains available. |
| High | Verification reads, forced verification, decisions, and reverification accepted any candidate/verification ID from HR. | Every operation checks recruiter access to the candidate before reading or changing evidence. |
| High | Prescreening generation, editing, and evaluation reads did not check job ownership. | Recruiters can manage and read assessments only for their own jobs. |
| High | Analytics event history and its stream exposed activity from other recruiters. AI job inspection/status also lacked scope. | Event and analysis queries now apply recruiter ownership. Events about another recruiter's job stay private even when a candidate has applied to both. |
| High | Blind screening concealed top-level contact fields while nested claims, candidate answers, summaries, history, career caches, notifications, and events could retain identity. Decision responses ignored blind mode. | Recursive redaction covers those responses, personal links are suppressed, and decision responses honor blind headers/query state. |
| High | Tokens without `token_version` bypassed password-reset/session-revocation checks. | Session version is mandatory. Inactive, missing, and revoked optional-auth sessions are rejected. Tokens must include expiration. |
| High | All Render subdomains were accepted with credentialed CORS. The JWT secret had a public fixed fallback. | CORS uses configured origins. Development uses an ephemeral random fallback; production rejects absent, known weak, or short configured keys. |
| High | Frontend dependency audit reported 10 vulnerable package entries, including Axios, Vite, React Router, and transitive packages. | Updated Axios 1.20, React Router 7.18.4, Vite 8.3.4, and the React plugin 6.1.2; refreshed the lockfile. Final npm audit reports zero. |
| High | Backend scan reported advisories in `python-jose` and `ecdsa` (three report entries, including a duplicate advisory). | Replaced the JWT dependency chain with PyJWT, kept explicit HS256 verification, and audited a complete fresh resolution of 49 packages. Final scan reports zero. |
| Medium | Rate limiting silently disabled itself when pytest was imported or the client name was `testclient`. Its per-IP state never expired globally. | Removed runtime bypasses, added expired-key cleanup, and tested real 429 responses. Workflow tests opt out through explicit dependency overrides. The limiter remains single-process. |
| Medium | URL validation allowed DNS failures, missed IPv4-mapped IPv6 addresses, and could throw on malformed ports. | Validation fails closed on unresolved hosts, rejects non-public/mixed addresses, malformed ports, credentials, local hostnames, and unsafe schemes. |
| Medium | Merely supplying a repository/demo URL generated “Verified Repository,” “Live Demo Accessible,” README quality, and recent commit activity. Credential IDs were treated as verified certificates. | Those results now describe supplied claims and links as unverified. Commit/README checks say “Not Checked.” Unsafe project and certificate links are not returned as clickable links. |
| Medium | Partial/empty company names could match famous companies; a demo company was included in the reference list. Company existence was conflated with internship authenticity. | Require exact normalized reference names, remove the demo company, and require HR confirmation of employment/internships. Static company references do not establish candidate employment. |
| Medium | Trust scoring counted every certificate as verified and could label candidate-supplied links “strong evidence.” Empty resume text was marked authentic. | Only verified certificates and independently supporting sources count toward those claims. Text checks accurately describe their scope and report insufficient text when absent. |
| Medium | Old verification results remained cached after engine changes or resume replacement. Reverification retained an old HR decision. | Engine/resume cache markers trigger refresh. Previous scores and decisions are archived, and new evidence requires a new HR decision. |
| Medium | Candidates received scoring rubrics. Answers were untyped, required questions could be skipped, and candidates could submit invented questions. | Candidate question responses omit scoring criteria and expected concepts. Answer IDs must belong to distinct active job questions, all required answers are enforced, and payload lengths/types are validated before application creation. |
| Medium | Question updates deleted previous questions and accepted invalid weights/types. | Typed question validation rejects malformed input. Previous questions are deactivated and retained for assessment history. |
| Medium | Gemini could replace the complete prescreening score and produce a label inconsistent with it. | Local scoring retains 75% weight; AI contributes at most 25%. Non-finite scores are rejected and labels are derived from the resulting score. |
| Medium | Resume upload read the entire file before checking size, left files after parse failures, reused career caches across candidates, and deleted the old file before DB commit. | Reads are bounded to the maximum plus one byte, corrupt files are rejected/cleaned, caches are scoped to the candidate, and old files are removed only after successful persistence. |
| Medium | Verification completion/decision events were flushed after the final commit and lost when the session closed. | Those events are committed and decision persistence is covered by regression tests. |
| Medium | SSE clients could replay history on reconnect, loop on clean EOF, or leave pending fetches running after unmount. Open streams did not recheck revocation. | Cursor advances on each event, reconnect backs off, AbortController cancels fetches, and server streams recheck account state, session version, and expiration. Blind mode changes restart/redact the feed. |
| Medium | Verification/prescreening tables existed in models but were absent from Alembic migrations. A historical migration queried SQLite-specific metadata. | Added migration `23f3794cc15d` for all three tables and schema alignment, used portable table inspection, and verified SQLite upgrade/rollback/model consistency. |
| Medium | Default startup created ownerless demo jobs even when seeding was disabled; production ignored schema-creation controls. | Seeding is explicitly opt-in. Automatic schema creation defaults off in production; migrations are documented. |
| Medium | Tests changed environment/DB state during collection, shared tables between modules, could import the application before selecting a test database, and used the real uploads directory. | Central test setup chooses a temporary DB/uploads directory before imports, disables live AI, isolates modules, and removes collection-time schema resets. Added development test requirements. |
| Medium | CLI HR creation warned about weak passwords but continued. Admin bootstrap had the wrong import path and did not load backend `.env`. | Shared password validation now rejects weak/overlong passwords, CLI HR accounts require an initial password change, and admin bootstrap loads the correct package/environment. Root admin entry delegates to the shared script. |
| Low | Authentication and blind preferences did not synchronize after login/password change; a transient startup request failure logged users out. Blind toggle side effects lived inside a React updater. | Auth change events synchronize state, `/auth/me` refreshes profile/flags, transient failures preserve the session, and toggle audit effects execute outside the updater. |
| Low | Assessment modal reused prior answers and submitted blank optional answers. | Answers reset per job/opening, blank optional answers are omitted, and text length is capped. |
| Low | Homepage anchors failed on auth pages; employer registration actually created candidates; footer links were placeholders. Unsupported usage, speed, and accuracy claims appeared as facts. | Navigation targets real homepage sections, employer entry goes to HR login with administrator-account guidance, footer links work, and hard-coded performance claims were replaced with supported features. The example score is labeled illustrative. |

## Validation evidence

| Check | Result |
| --- | --- |
| Backend suite | Final run: 179 tests passed in 26.46 seconds, including JWT replacement and verification-cache updates. |
| Added backend coverage | 39 regression cases cover ownership, nested privacy, invalid answers, real rate limiting, URL validation, cache refresh, audit persistence, corrupt uploads, and stream revocation. |
| Frontend tests | 2 tests passed: pending-fetch cancellation; reconnect cursor and blind header. |
| Production frontend build | Passed with Vite 8.3.4. |
| npm vulnerability scan | 0 known vulnerabilities, reduced from 10 package entries. |
| Backend dependency scan | 0 known vulnerabilities in the complete 49-package resolution captured in `recruitment-api/dependency-snapshot.txt`; machine-readable results are in `recruitment-api/dependency-audit.json`. |
| SQLite migrations | Upgrade to head, downgrade to previous head, re-upgrade, and Alembic model consistency checks passed on a separate audit database. |
| Browser smoke check | Homepage, login, registration, fixed homepage navigation, and signed-out HR/password-route redirects verified. No captured browser console errors. |
| Admin command | `python scripts/create_admin.py --help` succeeded after repair. |

Tests use local fallbacks, mocked external responses, and deterministic DNS.
Live Gemini calls and real repository/issuer verification were not tested.
One non-failing Starlette/httpx deprecation warning remains in the test runtime.

## Remaining limitations and deployment work

1. Apply updated requirements and rebuild/restart the application to use these
   changes. No production deployment, existing application database migration,
   or real account changes were performed during the audit.
2. Back up the deployment database and check its Alembic revision before applying
   migrations. Databases previously initialized by `create_all` need a baseline
   reconciliation because migration-created tables may already exist. Migration
   tests covered SQLite; PostgreSQL has not been exercised.
3. Set `APP_ENV=production`, a persistent random `SECRET_KEY` of at least 32
   characters, and exact `CORS_ORIGINS` before deployment. Blank development
   keys invalidate sessions on process restart and cannot support multiple
   workers consistently. Existing versionless tokens now require login again.
4. Verification still analyzes resume text and supplied references. It does not
   fetch repositories, commits, live demos, offer letters, or issuer records.
   Missing public evidence is not proof of fraud. A future fetcher needs IP
   pinning and redirect validation in addition to the URL validator.
5. Matching and prescreening remain heuristic/AI-assisted. Scores have not been
   calibrated against validated hiring outcomes or independently assessed for
   fairness. Keyword presence and answer length can still influence scoring.
6. Rate limits and generation locks are in memory. Multiple workers/instances
   need shared coordination. Synchronous analysis and polling also need load
   tests, request timeouts, and a background-job strategy before scaling.
7. Blind screening is a review preference, not an irreversible permission
   boundary. An authorized recruiter can choose normal review. Regex redaction
   cannot guarantee removal of every indirect identifier or sensitive detail
   in arbitrary prose.
8. Candidate profiles/resumes and verification records are shared across a
   candidate's legitimate recruiters. Per-job application snapshots and
   per-recruiter verification decisions would require a data-model change.
9. Backend requirements mostly use open version ranges. The saved audit
   snapshot records this Windows/Python 3.14 resolution; it is not a portable
   production lockfile. Re-audit deployments after dependency resolution changes.
10. This browser check covered public routing. Complete signed-in browser
    journeys, mobile layouts, assistive-technology testing, recovery-email
    delivery, backup restoration, and production monitoring were not validated.
    Forgot-password still depends on administrator assistance; no email service
    is configured by this code.

Package migration references: [Vite migration guide](https://vite.dev/guide/migration)
and [PyJWT usage documentation](https://pyjwt.readthedocs.io/en/stable/usage.html).
