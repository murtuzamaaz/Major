# 🛡️ ThreatForge AI

<div align="center">

![ThreatForge AI](https://img.shields.io/badge/ThreatForge-AI%20DevSecOps-blueviolet?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-14-black?style=for-the-badge&logo=next.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?style=for-the-badge&logo=fastapi)
![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?style=for-the-badge&logo=supabase)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker)

**AI-Powered DevSecOps Platform for Security Analysis, Intrusion Testing, Performance Engineering & Intelligent Remediation**

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Why ThreatForge AI](#-why-threatforge-ai)
- [Core Services](#-core-services)
- [Architecture](#-architecture)
- [End-to-End Data Flow](#-end-to-end-data-flow)
- [Technology Stack](#-technology-stack)
- [Database Architecture](#-database-architecture)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Configuration](#-configuration)
- [Using ThreatForge AI](#-using-threatforge-ai)
- [Reporting](#-reporting)
- [Security & Responsible Testing](#-security--responsible-testing)
- [Deployment & CI/CD](#-deployment--cicd)
- [API Documentation](#-api-documentation)
- [Key Strengths](#-key-strengths)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌟 Overview

**ThreatForge AI** is a full-stack DevSecOps platform that brings security analysis, dynamic intrusion simulation, performance testing, and AI-assisted remediation into a single workflow.

The platform is designed to help developers identify security weaknesses and performance bottlenecks, understand their impact, and receive actionable remediation guidance before applications reach production.

ThreatForge combines:

- 🔍 **SAST** — Static code-level vulnerability detection
- 🎯 **DAST** — Controlled dynamic intrusion testing against live systems
- ⚡ **Performance Engineering** — Load, stress and spike testing using k6
- 🤖 **AI Code Assistant** — Context-aware code analysis and remediation using Gemini and Ollama
- 📊 **Security Dashboard** — Unified visibility into security, performance and testing results
- 📄 **Report Generation** — Structured reports for findings, metrics and recommendations

The backend is built around **FastAPI**, the frontend uses **Next.js/TypeScript**, persistent application data is stored in **Supabase PostgreSQL**, and semantic code retrieval is powered by **FAISS**.

---

## 🎯 Why ThreatForge AI

ThreatForge is designed around a simple idea:

> **Security testing should not be separated from performance analysis and remediation.**

Instead of using isolated tools for different stages of application security, ThreatForge provides one workflow:

**Repository / URL → Analysis → Findings → AI Reasoning → Remediation → Storage → Dashboard → Report**

### Key Benefits

- 🛡️ Detect vulnerabilities before deployment
- 🔎 Analyze complete GitHub repositories
- 🌐 Test real applications through controlled dynamic analysis
- ⚡ Measure scalability and response-time behavior
- 🤖 Understand vulnerabilities using AI
- 🧠 Retrieve relevant code through semantic indexing
- 🗃️ Persist scan history and analytics in PostgreSQL
- 📊 Monitor all results from one dashboard
- 📄 Generate reports for documentation, audits and team sharing

---

# ✨ Core Services

ThreatForge AI is organized around **six major functional services**.

## 1. 🔍 Vulnerability Scanner — SAST

The Vulnerability Scanner performs static analysis on GitHub repositories.

### Workflow

1. Accept a repository URL
2. Download the repository as a ZIP
3. Extract and parse the codebase
4. Analyze source files using pattern-based and rule-based checks
5. Identify vulnerable files and security findings
6. Store findings and affected-file information in Supabase

### Detects

- SQL Injection
- Cross-Site Scripting (XSS)
- Hardcoded API keys and credentials
- Exposed secrets and environment configuration
- Insecure coding practices
- Security misconfigurations
- Outdated or expired dependencies

### Output

Each finding can contain:

- Severity
- CVSS information
- CVE/CWE references where available
- Description
- Evidence
- Recommendation
- Affected URL/file information

ThreatForge therefore acts as a **custom lightweight SAST engine** focused on actionable security findings.

---

## 2. 🎯 Intrusion Tester — DAST

The Intrusion Tester performs controlled security testing against a live application.

**User consent is required before an intrusion test is executed.**

### Areas Tested

- CORS misconfigurations
- Open ports and exposed services
- Weak security headers
- SSL/TLS configuration weaknesses
- SQL Injection
- XSS
- Payment gateway weaknesses
- Sensitive-data exposure
- Other controlled attack-surface checks

### Objective

The service attempts to identify:

- Potential entry points
- Exploitable weaknesses
- Security misconfigurations
- Attack-surface exposure

Results are stored as intrusion simulation runs and surfaced through the dashboard and reporting workflow.

---

## 3. ⚡ Load Tester — Performance Engineering

The Performance Testing service evaluates application scalability and reliability under controlled traffic.

### Tools

- **k6** — Load generation and performance testing
- **httpx** — HTTP request handling

### Test Types

- Load testing
- Stress testing
- Spike testing

### Metrics

- Maximum concurrent users
- Average/maximum virtual users
- Total requests
- Successful requests
- Failed requests
- Average response time
- Minimum response time
- Maximum response time
- p50 latency
- p95 latency
- p99 latency
- Throughput
- Failure rate

Performance results are persisted in the `performance_runs` table for historical analysis and reporting.

---

## 4. 🤖 AI Code Assistant — Remediation Engine

The AI Code Assistant provides context-aware analysis of the repository and helps developers understand and fix issues.

### Code Intelligence Pipeline

```text
GitHub Repository
       │
       ▼
Repository Download
       │
       ▼
Code Parsing
       │
       ▼
Semantic Code Indexing
       │
       ▼
FAISS Vector Search
       │
       ▼
Relevant Code Context
       │
       ├──────────────► Google Gemini
       │
       └──────────────► Ollama Local Inference
                              │
                              ▼
                    Explanation / Fix / Guidance
```

### Capabilities

- Explain vulnerabilities in plain language
- Identify affected files
- Understand project structure
- Retrieve relevant code semantically
- Suggest remediation strategies
- Provide context-aware code assistance
- Reduce repeated AI computation by storing generated insights

The system uses **FAISS** as the vector database/index for semantic retrieval and supports both **Google Gemini** and **Ollama** for AI reasoning.

---

## 5. 📊 Security Dashboard

The dashboard acts as the central control center for ThreatForge.

### Provides Visibility Into

- Vulnerability findings
- Severity distribution
- Performance metrics
- Intrusion-test results
- Scan history
- Scan status
- AI-generated insights
- Affected files
- Recent analysis activity

The frontend communicates with the FastAPI backend through REST APIs and fetches user-specific analysis data.

---

## 6. 📄 Downloadable Reports

ThreatForge provides structured reports from completed analyses.

### Reports Can Include

- Vulnerability findings
- Severity information
- CVE/CWE references
- Evidence and affected files
- Performance statistics
- Intrusion-test results
- AI-generated recommendations
- Scan metadata

Reports can be used for:

- Security documentation
- Internal reviews
- Audits
- Team communication
- Project records

---

# 🏗️ Architecture

The current system follows a layered architecture consisting of the **Frontend & Authentication Layer**, **FastAPI Backend Service Layer**, and **Supabase Data & Persistence Layer**. The backend contains the core SAST, DAST, performance-testing and AI-assisted analysis services, while Gemini, Ollama and FAISS provide the AI and semantic-analysis capabilities.

### System Architecture Diagram

![ThreatForge AI System Architecture](docs/system-architecture.jpg)

> **Architecture diagram:** The diagram above represents the current service boundaries, request flow, AI analysis components and Supabase persistence model.

### Architectural Layers

| Layer | Responsibility | Main Technologies |
|---|---|---|
| Frontend & Authentication | Dashboard, reports, authentication and user interaction | Next.js, TypeScript, Auth0 |
| API Gateway | Request routing, validation and service orchestration | FastAPI, Pydantic |
| Core Analysis Services | SAST, DAST and performance testing | Python, k6, httpx |
| AI & Analysis Engine | AI reasoning, local inference and semantic retrieval | Gemini, Ollama, FAISS |
| Data & Persistence | Scan workflow, findings, metrics, simulations and AI insights | Supabase, PostgreSQL |
| Deployment | Containerization, CI/CD and hosting | Docker, Jenkins, AWS EC2, Vercel, Nginx |

---

# 🔄 End-to-End Data Flow

```text
                    ┌─────────────────────┐
                    │       User          │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Next.js + Auth0     │
                    └──────────┬──────────┘
                               │
                    Authenticated Request
                               │
                               ▼
                    ┌─────────────────────┐
                    │   FastAPI Gateway   │
                    └──────────┬──────────┘
                               │
             ┌─────────────────┼──────────────────┐
             │                 │                  │
             ▼                 ▼                  ▼
        ┌─────────┐       ┌─────────┐        ┌─────────┐
        │  SAST   │       │  DAST   │        │   k6    │
        │ Scanner │       │ Tester  │        │  Load   │
        └────┬────┘       └────┬────┘        └────┬────┘
             │                 │                  │
             └─────────────────┼──────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ AI Analysis Engine  │
                    │ Gemini / Ollama     │
                    │ FAISS Retrieval     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Supabase PostgreSQL │
                    └──────────┬──────────┘
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
        ┌──────────────┐              ┌──────────────┐
        │   Dashboard  │              │    Reports   │
        └──────────────┘              └──────────────┘
```

### Flow Summary

1. User authenticates through Auth0.
2. User submits a repository or live application URL.
3. FastAPI receives and validates the request.
4. A scan/run record is created.
5. The selected analysis service executes.
6. Security findings, performance metrics or intrusion results are generated.
7. Relevant code can be indexed and retrieved through FAISS.
8. Gemini and/or Ollama provides AI reasoning and remediation guidance.
9. Results are persisted in Supabase PostgreSQL.
10. The dashboard retrieves the linked results.
11. Reports can be generated from the stored analysis data.

---

# 🛠️ Technology Stack

## Frontend

| Technology | Purpose |
|---|---|
| Next.js | Web application framework |
| React | UI components |
| TypeScript | Type-safe frontend development |
| Auth0 | Authentication and session management |
| Fetch / Axios | REST API communication |

## Backend

| Technology | Purpose |
|---|---|
| FastAPI | REST API and service layer |
| Python 3.11+ | Backend implementation |
| Pydantic | Request/data validation |
| Uvicorn | ASGI server |
| httpx | HTTP requests and testing |
| requests | External HTTP communication |

## Security & Testing

| Technology | Purpose |
|---|---|
| Custom SAST engine | Static vulnerability detection |
| DAST modules | Controlled live-system testing |
| k6 | Load, stress and spike testing |
| GitHub | Repository source |
| CVE/CWE references | Security finding classification |

## AI & Retrieval

| Technology | Purpose |
|---|---|
| Google Gemini API | AI reasoning and remediation |
| Ollama | Local LLM inference |
| FAISS | Vector indexing and semantic retrieval |
| NumPy | Vector/data processing |

## Data & Infrastructure

| Technology | Purpose |
|---|---|
| Supabase | Backend database platform |
| PostgreSQL | Persistent relational storage |
| Docker | Containerization |
| Jenkins | CI/CD automation |
| AWS EC2 | Backend deployment |
| Vercel | Frontend deployment |
| Nginx | Reverse proxy / HTTPS routing |

---

# 🗄️ Database Architecture

ThreatForge uses **Supabase PostgreSQL** as its unified persistence layer.

## 1. `vulnscan_scans`

Root table for scan/workflow requests.

Stores information such as:

- Target repository or URL
- Scan type
- Requested modules
- Status
- Consent flag
- Timestamps
- Run metadata

---

## 2. `vulnscan_findings`

Stores detected security vulnerabilities.

Typical information includes:

- Severity
- CVSS score
- CVE/CWE references
- Description
- Evidence
- Recommendation
- Affected URL

---

## 3. `affected_files`

Maps security findings to affected repository files.

Stores:

- File path
- Severity
- Repository/run reference
- Finding relationship

This enables precise debugging and remediation.

---

## 4. `performance_runs`

Stores performance-testing results.

Includes:

- Virtual-user statistics
- Request counts
- Success/failure counts
- Response-time statistics
- p50/p95/p99 percentiles
- Throughput
- Failure rates
- Test metadata

---

## 5. `simulation_runs`

Stores intrusion-testing summaries and execution metadata.

Includes:

- Run metadata
- Overall severity
- Dynamic testing results

---

## 6. `ai_insights`

Stores AI-generated analysis.

Includes:

- Vulnerability explanations
- Remediation recommendations
- AI-generated insights
- Related analysis metadata

Persisting AI results avoids unnecessary recomputation.

---

# 📁 Project Structure

A representative high-level structure is:

```text
ThreatForge/
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── services/
│   ├── public/
│   ├── package.json
│   └── ...
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routes/
│   │   ├── services/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── data/
│   │   └── ...
│   ├── requirements.txt
│   └── ...
│
├── docs/
│   └── system-architecture.png
│
├── Dockerfile
├── docker-compose.yml
├── Jenkinsfile
└── README.md
```

> The exact directory structure may vary depending on the current repository implementation. The architecture above describes the logical organization of the platform.

---

# 🚀 Getting Started

## Prerequisites

Install:

- **Python 3.11+**
- **Node.js 18+**
- **npm**
- **Git**
- **Docker** (recommended for containerized deployment)
- **k6** (required for performance testing)
- **Ollama** (optional if local inference is enabled)

You will also need credentials/configuration for:

- Auth0
- Supabase
- Google Gemini API
- GitHub API/token if required by repository access

---

## 1. Clone the Repository

```bash
git clone https://github.com/murtuzamaaz/Major.git
cd Major
```

---

## 2. Backend Setup

```bash
cd backend

python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
```

### macOS/Linux

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create the backend environment file:

```bash
cp .env.example .env
```

On Windows PowerShell, if needed:

```powershell
Copy-Item .env.example .env
```

---

## 3. Frontend Setup

From the project root:

```bash
cd frontend
npm install
```

Create the local environment file:

```bash
cp .env.local.example .env.local
```

---

## 4. Start the Backend

From the backend directory:

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

If the repository's current module path differs, use the module path defined by the backend entry point.

Backend:

```text
http://127.0.0.1:8000
```

Swagger/OpenAPI:

```text
http://127.0.0.1:8000/docs
```

---

## 5. Start the Frontend

From the frontend directory:

```bash
npm run dev
```

Frontend:

```text
http://localhost:3000
```

---

# ⚙️ Configuration

## Environment Configuration

The current environment configuration uses the following variables for the frontend, Auth0 authentication, backend communication, API access, database connectivity and security.

> **Important:** Keep secrets and credentials out of Git. Use `.env.local` / `.env` files locally and configure the same variables through the deployment platform for production.

```env
# ThreatForge AI Environment Configuration

# Backend API Configuration (Frontend)
NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8000

# Auth0 Configuration
AUTH0_DOMAIN=
AUTH0_CLIENT_ID=
AUTH0_CLIENT_SECRET=
AUTH0_AUDIENCE=

# Frontend URLs
NEXT_PUBLIC_AUTH0_DOMAIN=
NEXT_PUBLIC_AUTH0_CLIENT_ID=
NEXT_PUBLIC_AUTH0_AUDIENCE=
NEXT_PUBLIC_BASE_URL=

# Backend Configuration (Server-side)
BACKEND_URL=
JWT_SECRET=

# API Keys
GEMINI_API_KEY=

# Database (if using)
DATABASE_URL=your-database-url

# Security
SESSION_SECRET=
ENCRYPTION_KEY=
```

### Configuration Groups

| Variable | Purpose |
|---|---|
| `NEXT_PUBLIC_BACKEND_URL` | Backend API URL used by the frontend |
| `AUTH0_DOMAIN` | Auth0 domain |
| `AUTH0_CLIENT_ID` | Auth0 application client ID |
| `AUTH0_CLIENT_SECRET` | Auth0 application client secret |
| `AUTH0_AUDIENCE` | Auth0 API audience |
| `NEXT_PUBLIC_AUTH0_DOMAIN` | Auth0 domain exposed to the frontend |
| `NEXT_PUBLIC_AUTH0_CLIENT_ID` | Auth0 client ID exposed to the frontend |
| `NEXT_PUBLIC_AUTH0_AUDIENCE` | Auth0 audience exposed to the frontend |
| `NEXT_PUBLIC_BASE_URL` | Frontend base URL |
| `BACKEND_URL` | Server-side backend URL |
| `JWT_SECRET` | Server-side JWT signing/validation secret |
| `GEMINI_API_KEY` | Google Gemini API credential |
| `DATABASE_URL` | Database connection URL |
| `SESSION_SECRET` | Session security secret |
| `ENCRYPTION_KEY` | Application encryption key |

### Local Setup

For the frontend, create the appropriate environment file in the frontend project and populate the required Auth0 and backend URL values.

For server-side configuration, populate the backend URL, JWT/session/encryption secrets, Gemini API key and database URL as required by the deployment.

Do not commit populated environment files.

### Security

Never commit:

- API keys
- Auth0 client secrets
- JWT secrets
- Session secrets
- Encryption keys
- Database credentials
- Populated `.env` or `.env.local` files

Add environment files to `.gitignore`.

---

# 📖 Using ThreatForge AI

## 🔍 Run Vulnerability Analysis

1. Sign in through Auth0.
2. Open the security dashboard.
3. Provide a GitHub repository URL.
4. Select the required analysis.
5. Start the scan.
6. Wait for the scan to complete.
7. Review vulnerabilities and affected files.
8. Open AI assistance for explanations/remediation.
9. Generate a report if required.

---

## ⚡ Run Performance Testing

1. Provide the target application URL.
2. Configure the required performance parameters.
3. Select the test type.
4. Start the k6 test.
5. Review:
   - Request counts
   - Failure rates
   - Throughput
   - Average latency
   - p50
   - p95
   - p99
6. Review the stored run in the dashboard.

Only run performance tests against systems you own or have explicit authorization to test.

---

## 🎯 Run Intrusion Testing

1. Provide the target live URL.
2. Review the testing scope.
3. Provide the required consent.
4. Start the controlled DAST workflow.
5. Review discovered weaknesses.
6. Inspect severity and affected areas.
7. Use AI assistance where appropriate.
8. Generate a report.

Only perform intrusion testing against systems where you have explicit authorization.

---

## 🤖 Use the AI Code Assistant

The AI assistant can be used to:

- Ask questions about the repository
- Explain detected vulnerabilities
- Identify affected files
- Understand project structure
- Retrieve relevant code context
- Suggest remediation approaches

The repository is semantically indexed so that AI responses can use relevant code rather than relying only on a generic prompt.

---

# 🖥️ Running Application Screenshots

Use this section to showcase screenshots of the **running ThreatForge AI application**.

Add screenshots to a folder such as `docs/screenshots/` and reference them below.



<img width="1919" height="863" alt="main-threatforge" src="https://github.com/user-attachments/assets/e9b98613-55aa-4fe9-a47e-28413eb20823" />
<img width="1600" height="787" alt="threatforge3" src="https://github.com/user-attachments/assets/cf2fb19c-5e15-4d4e-96ae-305266e99c7e" />
<img width="1599" height="899" alt="threatforge" src="https://github.com/user-attachments/assets/56af27c2-c61a-4dda-ad94-42a7680ef08f" />
<img width="1599" height="899" alt="threatforge1" src="https://github.com/user-attachments/assets/c3bec0f1-1902-4ec3-acb0-92439db3bdc2" />
<img width="1600" height="763" alt="threatforge4" src="https://github.com/user-attachments/assets/f83832c5-3378-49cf-b205-b1359dacdba4" />
<img width="1599" height="899" alt="threatforge8" src="https://github.com/user-attachments/assets/58693024-2fea-4ca4-9cb2-e33fd49e3e1c" />
<img width="1600" height="735" alt="threatforge7" src="https://github.com/user-attachments/assets/49df8e5b-d6a1-4f55-9a0f-ec902a0e3115" />
<img width="1600" height="787" alt="threatforge3" src="https://github.com/user-attachments/assets/4c3415b5-58ba-4519-b5ee-aafeb178f402" />



---

# 📄 Reporting
<img width="1600" height="787" alt="threatforge3" src="https://github.com/user-attachments/assets/10d66178-8eda-4e29-abd7-b05f073278d5" />

ThreatForge's reporting workflow combines stored results from multiple services.

A report can contain:

```text
Scan Metadata
      │
      ├── Security Findings
      │     ├── Severity
      │     ├── CVE/CWE
      │     ├── Evidence
      │     └── Recommendations
      │
      ├── Affected Files
      │
      ├── Intrusion Test Results
      │
      ├── Performance Metrics
      │     ├── Requests
      │     ├── Throughput
      │     ├── Failure Rate
      │     └── p50 / p95 / p99
      │
      └── AI Insights
            ├── Explanation
            └── Remediation
```

Reports are intended to make technical findings easier to document, review and share.

---

# 🔒 Security & Responsible Testing

ThreatForge is intended for **authorized security and performance testing only**.

### Security Practices

- Authenticated access through Auth0
- Environment variables for secrets
- Input validation through Pydantic
- Parameterized PostgreSQL queries
- CORS configuration
- User-based data access
- Consent requirement for intrusion testing
- Controlled execution of dynamic tests

### Responsible Use

Do not use ThreatForge to test:

- Systems you do not own
- Applications without explicit authorization
- Third-party infrastructure without permission
- Payment systems or production services outside an approved testing scope

Always define a safe testing scope before running DAST or performance workloads.

---

# 🚢 Deployment & CI/CD

ThreatForge is designed for containerized deployment.

## Deployment Architecture

```text
                    Git Repository
                          │
                          ▼
                     Jenkins CI/CD
                          │
                    Build & Test
                          │
                          ▼
                       Docker
                          │
             ┌────────────┴────────────┐
             ▼                         ▼
       Frontend Build              Backend Build
             │                         │
             ▼                         ▼
          Vercel                    AWS EC2
                                       │
                                     Nginx
                                       │
                                  HTTPS / Domain
```

### Frontend

The Next.js frontend can be deployed through **Vercel**.

### Backend

The FastAPI backend can be containerized using **Docker** and deployed to **AWS EC2**.

### CI/CD

**Jenkins** automates the backend build/deployment workflow.

Typical pipeline:

```text
Code Push
   │
   ▼
Jenkins
   │
   ├── Checkout
   ├── Build
   ├── Dependency Install
   ├── Tests
   ├── Docker Build
   └── Deployment
          │
          ▼
       AWS EC2
```

---

# 📚 API Documentation

FastAPI automatically exposes interactive API documentation.

Once the backend is running:

```text
http://127.0.0.1:8000/docs
```

and:

```text
http://127.0.0.1:8000/redoc
```

The exact endpoint list is defined by the currently deployed backend routes.

Core API responsibilities include:

- Repository analysis
- Vulnerability scanning
- Intrusion testing
- Performance testing
- AI/code-assistant operations
- Analytics retrieval
- Scan history
- Report generation
- Result retrieval

---

# 💪 Key Strengths

## Unified DevSecOps Platform

ThreatForge combines:

**Security + Performance + AI + Reporting**

in one system.

## Modular Architecture

Each major capability is isolated into a service, making the platform easier to maintain and extend.

## Context-Aware AI

FAISS-based semantic retrieval gives the AI assistant access to relevant repository context.

## Real-World Testing

The platform supports analysis of actual GitHub repositories and authorized live application URLs.

## Strong Data Model

Supabase PostgreSQL provides persistent storage for:

- Scan workflows
- Security findings
- Affected files
- Performance metrics
- Intrusion runs
- AI insights

## Production-Oriented Infrastructure

The system incorporates:

- Docker
- Jenkins CI/CD
- AWS EC2
- Nginx
- HTTPS
- Vercel
- Supabase

---

# 🧩 Architecture at a Glance

```text
┌───────────────────────────────────────────────────────────────┐
│                  FRONTEND + AUTHENTICATION                    │
│                 Next.js + TypeScript + Auth0                  │
│                                                               │
│       Dashboard       Reports       AI Chat       Auth        │
└───────────────────────────────┬───────────────────────────────┘
                                │
                         REST API Requests
                                │
┌───────────────────────────────▼───────────────────────────────┐
│                    BACKEND SERVICE LAYER                      │
│                         FastAPI                               │
│                                                               │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐              │
│  │    SAST    │  │    DAST    │  │    k6      │              │
│  │ Vulnerab.  │  │ Intrusion  │  │ Performance│              │
│  └────────────┘  └────────────┘  └────────────┘              │
│                                                               │
│                 ┌─────────────────────┐                       │
│                 │ AI Code Assistant    │                       │
│                 │ Gemini + Ollama      │                       │
│                 │ FAISS Retrieval     │                       │
│                 └─────────────────────┘                       │
└───────────────────────────────┬───────────────────────────────┘
                                │
                          Result Storage
                                │
┌───────────────────────────────▼───────────────────────────────┐
│                    DATA & PERSISTENCE                         │
│                  Supabase PostgreSQL                          │
│                                                               │
│ scans | findings | affected_files | performance_runs         │
│ simulation_runs | ai_insights                                  │
└───────────────────────────────────────────────────────────────┘
```

---

# 🤝 Contributing

Contributions are welcome.

```bash
git checkout -b feature/your-feature
git add .
git commit -m "feat: add your feature"
git push origin feature/your-feature
```

Then open a pull request.

### Recommended Practices

- Keep backend services modular.
- Validate API inputs.
- Never commit secrets.
- Add tests for new backend functionality.
- Keep frontend/backend contracts synchronized.
- Document new environment variables and services.

---

# 📄 License

This project is licensed under the **MIT License**.

See the `LICENSE` file for the complete license text.

---

<div align="center">

### 🛡️ ThreatForge AI

**Secure. Test. Analyze. Remediate.**

Built as an integrated AI-powered DevSecOps platform.

</div>
