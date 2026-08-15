# Security Policy & Secure Vibe Coding Risk Management Standard

This repository strictly enforces the **Secure Vibe Coding Risk Management Framework**. All developers, AI coding assistants, and automated tools working on this codebase **MUST** strictly adhere to the operational principles and security guardrails outlined below.

---

## 🛡️ Core Operational & Security Guardrails

### 1. SRR (Small, Reversible, and Reviewable) Slicing & Line-Count Limits
To eliminate junk code, accidental bugs, and bloated rewrites:
* **The "One-Thing Rule"**: Every code modification prompt or task must be broken down into a short, simple, modular piece that performs **a single specific function**. Never write or request large multi-feature code dumps at once.
* **Strict Line-Count Constraint (30–50 Lines Max)**: Baseline code generation per iteration must stay strictly within **30 to 50 lines of code**.
* **Single-Task Exception**: If a single atomic task (e.g., an immutable data schema, UI layout shell, or self-contained algorithm) inherently requires more lines to maintain functional integrity, it is permitted to exceed 50 lines as an explicit exception. Otherwise, all code additions must strictly remain within the 30–50 line cap.
* **Inspect, Test, & Advance Workflow**: After completing a micro-segment, the code must be visually inspected (`git diff`), tested, and confirmed working before advancing to the next segment.

---

### 2. Parameterization & Data Security
* **Strict Code/Data Separation**: All inputs, parameters, and query targets must use parameterized placeholders or prepared statements.
* **Zero Concatenation**: Direct string concatenation or literal interpolation for data interaction layers is strictly forbidden.

---

### 3. System Constraints & OWASP Top 10 Compliance
* **OWASP Top 10 by Default**: Enforce context-aware input validation, output encoding, and HTML escaping (`vla_validator.py`) to neutralize Cross-Site Scripting (XSS) and injection vulnerabilities.
* **System Instructions Harness**: All AI interactions must inherit master security constraints requiring DevSecOps compliance across all generated snippets.

---

### 4. Zero Secrets & Environment Variable Hygiene
* **Never Hardcode Secrets**: API keys, private tokens, passwords, or encryption credentials must **NEVER** appear in source code or committed config files.
* **Strict Environment Isolation**: Secrets must be loaded exclusively via environment variables (`os.getenv("GEMINI_API_KEY")`) or local `.env` files.
* **Git Exclusion**: `.env` and `config.json` must remain explicitly listed in `.gitignore`.

---

### 5. Ecosystem & Dependency Hygiene (Anti-Slopsquatting)
* **Zero Hallucinated Packages**: Never suggest, install, or reference unverified or extrapolated third-party package names.
* **Standard Library Priority**: Prioritize native standard language libraries. External libraries must be industry-standard, highly popular packages with verified provenance and pinned versions (`requirements.txt`).

---

### 6. Repository Scanning & Pre-Commit Tripwires
* **Secret Scanning**: Maintain automated local pre-commit checks and repository scanning to intercept and block high-entropy strings or exposed keys before they reach remote repositories.

---

### 7. Runtime Lockdown & Containerization (Sandboxing)
* **Non-Root Execution**: Applications running in containerized environments (`Dockerfile`, `docker-compose.yml`) must execute under a low-privilege non-root user (`USER appuser` / UID `10001`) with `no-new-privileges:true`.

---

## 📋 Developer & AI Agent Compliance Checklist

- [x] Code changes are sliced into single-task micro-chunks (30–50 lines baseline).
- [x] No API keys or credentials are hardcoded or written to disk.
- [x] User inputs and outputs are sanitized against XSS / injection attacks.
- [x] Dependencies are pinned and verified.
- [x] Container executes under a non-root user.
- [x] `git diff` reviewed and unit tests passed (`python test_vla.py`) before committing.

---

## 🔐 Reporting Vulnerabilities

If you discover a security vulnerability or exposed credential, do not open a public issue. Contact the repository maintainers directly and immediately rotate any affected API keys.
