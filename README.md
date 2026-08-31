# 🧠 AI RIS — AI Resume Intelligence System

An AI-powered resume optimizer that analyzes your resume against a job description, scores ATS compatibility with a **deterministic scoring engine**, rewrites bullets, identifies skill gaps, and recommends projects — powered by **FastAPI**, **OpenRouter**, **PyMuPDF**, and **GitIngest**.

---

## ✨ Features

| Feature | Description |
|---|---|
| **Deterministic ATS Engine** | Algorithmic 0–100 match score with skill normalization & evidence tracing |
| **Multi-Engine PDF Extraction** | PyMuPDF, pdfplumber, pypdf, & PyPDF2 fallback for 100% text extraction |
| **Bullet Rewriter** | Fact-grounded bullet rewrites with action verbs + metrics |
| **Skill Gap Analysis** | Color-coded gaps by severity (Critical / Moderate / Minor) |
| **Project Suggestions** | Personalized build projects with tech stacks |
| **GitHub Integration** | Analyzes public GitHub repos via GitIngest |
| **Automated Test Suite** | 45 comprehensive unit tests for scoring, parsing, and schemas |
| **Optimized Resume** | Full downloadable ATS-ready resume |

---

## 🗂️ Project Structure

```
NLP/
├── start.bat                  ← One-click launcher (Windows)
│
├── frontend/                  ← Vite + React (port 5173)
│   ├── index.html
│   ├── package.json
│   └── src/
│       ├── components/        ← Sidebar, UploadPanel, ATSScoreCard, ...
│       ├── pages/             ← Dashboard.jsx
│       └── index.css          ← Full design system
│
└── backend/                   ← FastAPI (port 8000)
    ├── main.py
    ├── requirements.txt
    ├── .env                   ← API keys and origins
    ├── .env.example           ← Template
    ├── routes/
    │   └── analyze.py         ← Main analysis route
    ├── schemas/               ← Pydantic response models
    │   ├── analysis.py
    │   ├── ats.py
    │   └── resume.py
    ├── services/
    │   ├── ats_engine.py      ← Deterministic 0-100 scoring algorithm
    │   ├── llm_service.py     ← OpenRouter (gemini-2.5-flash)
    │   ├── github_service.py  ← GitHub API + GitIngest
    │   ├── parser_service.py  ← Multi-engine PDF + DOCX parser
    │   └── skill_normalizer.py← Skill matching & normalization
    └── test_module1.py..test_module4.py ← 45 automated unit tests
```

---

## ⚙️ Prerequisites

- **Python 3.10+** — [python.org](https://www.python.org/downloads/)
- **Node.js 18+** — [nodejs.org](https://nodejs.org/)
- **OpenRouter API Key** — [openrouter.ai/keys](https://openrouter.ai/keys) (free tier available)

---

## 🚀 Local Development Setup

### Step 1 — Clone the repo

```bash
git clone https://github.com/ShrutiVerma3008/NLP.git
cd NLP
```

### Step 2 — Configure the API Key

Copy the example env file and add your OpenRouter API key:

```bash
cd backend
copy .env.example .env
```

Open `backend/.env` and replace the placeholder:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

> Get a free key at: https://openrouter.ai/keys

### Step 3 — Set up the Backend

```powershell
cd backend

# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 4 — Set up the Frontend

```powershell
cd frontend
npm install
```

---

## ▶️ Running the Project

### Option A — One-Click (Recommended for Windows)

From the project root, simply double-click **`start.bat`** or run:

```cmd
start.bat
```

This automatically:
- Activates the Python venv and starts the FastAPI backend
- Opens a new terminal and starts the Vite frontend

### Option B — Manual (Two Terminals)

**Terminal 1 — Backend:**

```powershell
cd backend
venv\Scripts\activate
python main.py
```

**Terminal 2 — Frontend:**

```powershell
cd frontend
npm run dev
```

### Access the App

| Service | URL |
|---|---|
| **Frontend App** | http://localhost:5173 |
| **Backend API** | http://localhost:8000 |
| **API Docs (Swagger)** | http://localhost:8000/docs |

---

## 🧪 Using the App

1. Open **http://localhost:5173** in your browser
2. Upload a **PDF or DOCX** resume, or switch to "Paste Text"
3. Paste the **job description**
4. *(Optional)* Enter your **GitHub username** — GitIngest will analyze your repos
5. Click **"Optimize My Resume"**
6. View results across tabs:
   - **ATS Score** → Radial score ring + top strengths + recruiter insight
   - **Comparison** → Before/after bullet rewrites + full optimized resume (downloadable)
   - **Skill Gaps** → Color-coded pills by severity
   - **Projects** → 3 recommended build projects with tech stacks
   - **Feedback** → Key improvements + recruiter intelligence summary

---

## ☁️ Deployment

### Backend — Deploy on Render (Free)

1. Create a free account at [render.com](https://render.com)
2. Click **"New Web Service"** → Connect your GitHub repo
3. Set the following:

| Setting | Value |
|---|---|
| **Root Directory** | `backend` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |

4. Add **Environment Variable**:

| Key | Value |
|---|---|
| `OPENROUTER_API_KEY` | `your_openrouter_api_key_here` |

5. Click **"Create Web Service"** — your API will be live at `https://your-service.onrender.com`

---

### Frontend — Deploy on Vercel (Free)

1. Create a free account at [vercel.com](https://vercel.com)
2. Click **"New Project"** → Import your GitHub repo
3. Set the following:

| Setting | Value |
|---|---|
| **Root Directory** | `frontend` |
| **Framework Preset** | `Vite` |
| **Build Command** | `npm run build` |
| **Output Directory** | `dist` |

4. Add **Environment Variable** pointing to your deployed backend:

| Key | Value |
|---|---|
| `VITE_API_URL` | `https://your-service.onrender.com` |

> **Note:** Update the API base URL in your frontend code to use `import.meta.env.VITE_API_URL` before deploying.

5. Click **"Deploy"** — your app will be live at `https://your-app.vercel.app`

---

### Backend — Deploy on Railway (Alternative)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

Set `OPENROUTER_API_KEY` in the Railway dashboard → Variables tab.

---

## 🔑 Changing the AI Model

The app uses `google/gemini-2.5-flash` via OpenRouter by default. To switch models, edit `backend/services/llm_service.py`:

```python
response = await client.chat.completions.create(
    model="google/gemini-2.5-flash",  # ← change this
    ...
)
```

Popular OpenRouter model IDs:

| Model | ID |
|---|---|
| Gemini 2.5 Flash | `google/gemini-2.5-flash` |
| Claude 3 Haiku | `anthropic/claude-3-haiku` |
| Llama 3.1 8B (free) | `meta-llama/llama-3.1-8b-instruct:free` |
| Mistral 7B (free) | `mistralai/mistral-7b-instruct:free` |

Browse all models at [openrouter.ai/models](https://openrouter.ai/models).

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---|---|
| `OPENROUTER_API_KEY is not set` | Add your key to `backend/.env` |
| `pip install` fails | Make sure venv is activated: `venv\Scripts\activate` |
| CORS error in browser | Ensure backend is running on port 8000 |
| `npm install` fails | Make sure Node.js 18+ is installed |
| Port already in use | Kill the process: `npx kill-port 8000 5173` |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.