# Security Policy & Secure Vibe Coding Framework

This repository strictly enforces the **Secure Vibe Coding Risk Management** guidelines. All developers and AI coding assistants must adhere to the core security principles outlined below.

---

## 🛡️ Core Security Principles

### 1. Zero Secrets in Source Code
* **No Hardcoded Keys**: API keys, passwords, and private tokens must **NEVER** be committed to Git or stored in plaintext configuration files inside the repository.
* **Environment Variables Only**: All credentials must be loaded dynamically from system environment variables or local `.env` files (which are strictly excluded via `.gitignore`).

### 2. Input Sanitization & OWASP Compliance
* All user inputs and multimodal API responses are passed through context-aware sanitization filters (`vla_validator.py`).
* UI rendering widgets escape all inputs to prevent Cross-Site Scripting (XSS) and injection vulnerabilities.

### 3. Supply Chain & Dependency Hygiene
* Only verified, industry-standard Python libraries with established provenance (`google-genai`, `pillow`, `pyperclip`, `pynput`, `customtkinter`, `python-dotenv`) are used.
* All package versions are pinned in `requirements.txt`.

### 4. Sandboxing & Runtime Lockdown
* Production and testing containerization configs (`Dockerfile`, `docker-compose.yml`) enforce execution under a non-root, low-privilege user (`appuser`).

---

## 🔐 Reporting Vulnerabilities

If you discover a security flaw or credential exposure in this repository, please do not create a public issue. Contact the maintainers directly or rotate any impacted API keys immediately.
