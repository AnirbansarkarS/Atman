# Atman — Upload your Mind

Atman is an interactive experiment merging human EEG neural data with an AI persona interpreting it. Connect with "Uploaded Minds" via chat, explore their neural graphs in real-time, and trigger thought associations directly into their digital cortex.

## 🚀 Quick Start

### Method 1: Using the one-command bash script (Linux/macOS/Git Bash)
1. Ensure you have Python 3.10+ and Node.js installed.
2. Run the start script from the project root:
   ```bash
   ./start.sh
   ```
   **This will automatically:** 
   - Check/create a Python virtual environment.
   - Install all backend dependencies.
   - Install frontend npm packages.
   - Boot both `uvicorn` and `vite` simultaneously.

### Method 2: Docker Compose (Easiest)
Make sure Docker Desktop is running.
```bash
docker-compose up --build
```
- Frontend will be available at: http://localhost:5173
- Backend API will be at: http://localhost:8000

## 🛠 Manual Setup

**1. Setup the Backend**
```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
export PYTHONPATH="backend" # Windows PS: $env:PYTHONPATH="backend"
python -m uvicorn backend.main:app --reload
```

**2. Setup the Frontend**
```bash
cd frontend
npm install
npm run dev
```

## 📥 Dataset Setup

The EEG dataset (ds004196) is large and **not** committed to the repository. Download it on first run:

```bash
# Option 1: Automatic download (first time only)
pip install openneuro-py
python -m openneuro download ds004196
# Dataset will be downloaded to ./ds004196/ directory

# Option 2: Manual download
# Visit: https://openneuro.org/datasets/ds004196
# Download and extract to ./ds004196/ in project root
```

**Note:** The dataset is stored in BIDS format and is automatically cached after first download.

## ⚙️ Environment Variables
To get the true AI persona experience (rather than local stub responses), place an `.env` file in the project root:
```env
CLAUDE_API_KEY=sk-ant-api03...
GROQ_API_KEY=gsk_...
GEMINI_API_KEY=AIza...
```
If no key is present, the app degrades gracefully with placeholder "stub" responses.

**⚠️ SECURITY:** Never commit your `.env` file. Add your actual API keys only locally—they are in `.gitignore`.

## ✅ Verification Checklist
- **Backend:** `http://localhost:8000/docs` returns a Swagger UI.
- **Frontend:** Loads standard two-panel layout with graphs.
- **Graphs:** `GET /api/graph?type=eeg&subject=01` loads valid matplotlib images.
- **Chat:** Persona streams back natural language responses.
- **Inject:** Thought pills generate targeted memory triggers in the log.