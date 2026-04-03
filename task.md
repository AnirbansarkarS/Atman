# Atman — System Architecture & Technical Deep Dive

**Atman** is an interactive experiment that merges human EEG neural data with an AI persona. Users can upload their mind as EEG data, visualize it in real-time through multiple graph formats, chat with their digital consciousness, and inject thought triggers directly into their neural substrate.

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Data Structure & BIDS Format](#data-structure--bids-format)
4. [Backend Architecture](#backend-architecture)
5. [Frontend Architecture](#frontend-architecture)
6. [Data Flow & Interactions](#data-flow--interactions)
7. [Key Components Explained](#key-components-explained)
8. [Environment & Deployment](#environment--deployment)

---

## 🎯 Project Overview

### Core Concept
- **Input**: EEG brain data from the ds004196 BIDS dataset (contains real neuroscience data for multiple subjects)
- **Processing**: Backend analyzes EEG signals and generates 4 types of visualization (Raster, Power Spectrum, Spectrogram, Topomap)
- **AI Persona**: Claude or Groq LLM interprets the data and responds as "The Uploaded Mind"
- **Interaction**: Users chat with the persona and can inject targeted thought associations
- **Fallback**: When no API keys exist, the system uses stub responses (graceful degradation)

### Technology Stack
- **Frontend**: React 18 + Vite (modern build tool, fast HMR)
- **Backend**: FastAPI + Uvicorn (async Python web server)
- **Data Processing**: MNE (Python package for EEG analysis)
- **Deployment**: Docker Compose (orchestrates frontend + backend containers)
- **AI Support**: Anthropic (Claude) or Groq APIs
- **Visualization**: Matplotlib (generates PNG graphs dynamically)

---

## 🏗️ System Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         DOCKER COMPOSE                          │
├──────────────────────────────┬──────────────────────────────────┤
│   FRONTEND (Node container)  │   BACKEND (Python container)     │
│   Port 5173 (Vite dev)       │   Port 8000 (FastAPI + Uvicorn) │
│                              │                                  │
│  React App                   │   /api/status - EEG metadata    │
│  ├─ Canvas waveform          │   /api/load - SSE stream load   │
│  ├─ Tab selector (4 types)   │   /api/graph - PNG generation   │
│  ├─ Chat panel               │   /api/chat - AI streaming      │
│  └─ Inject buttons           │   /api/inject - Thought memory  │
│                              │   /api/test-stream - Debug      │
│  (Connects via VITE_API_URL) │                                 │
│                              │  Python Modules:                 │
│                              │  ├─ brain_loader (MNE I/O)      │
│                              │  ├─ brain_graphs (Matplotlib)   │
│                              │  └─ brain_persona (LLM)         │
│                              │                                  │
│                              │  Data: ./ds004196/ (BIDS)       │
│                              │  Output: ./generated_graphs/    |
│                              │  Env: .env (API keys)           │
└──────────────────────────────┴──────────────────────────────────┘
```

### Container Communication
- **Frontend → Backend**: HTTP REST calls to `http://backend:8000`
- **Backend → Data**: Reads BIDS dataset from mounted volume `./ds004196:/app/ds004196`
- **Backend → LLM**: Calls Anthropic Claude or Groq API (requires .env API key)
- **Shared Volumes**: 
  - Backend code hot-reload: `./backend:/app/backend`
  - Data mount: `./ds004196:/app/ds004196`
  - Frontend node_modules persistence (Docker named volume)

---

## 📊 Data Structure & BIDS Format

### What is BIDS?
**Brain Imaging Data Structure** — a standardized way to organize neuroimaging data. The ds004196 dataset contains:

```
ds004196/
├── dataset_description.json    # Metadata about the entire dataset
├── participants.json           # Subject demographics
├── participants.tsv            # Tab-separated values of participants
├── README                      # Dataset documentation
├── CHANGES                     # Version history
│
└── sub-*/                      # Subject folders (sub-01, sub-02, sub-03, sub-05)
    ├── ses-01/                 # Session 1 (fMRI session)
    │   ├── anat/               # Anatomical (T1-weighted MRI)
    │   ├── fmap/               # Fieldmap (distortion correction)
    │   └── func/               # Functional (task-based fMRI)
    │
    ├── ses-02/                 # Session 2 (fMRI session)
    │   ├── fmap/
    │   └── func/
    │
    └── ses-EEG/                # EEG session (the one we use!)
        └── eeg/
            ├── sub-01_ses-EEG_task-inner_eeg.bdf      # Raw EEG (BDF format)
            ├── sub-01_ses-EEG_task-inner_eeg.json     # EEG sidecar metadata
            ├── sub-01_ses-EEG_task-inner_channels.tsv # Channel descriptions
            └── sub-01_ses-EEG_task-inner_events.tsv   # Event markers (trial onsets)
```

### Available Subjects
- **sub-01**: 2 fMRI sessions + 1 EEG session
- **sub-02**: 2 fMRI sessions + 1 EEG session
- **sub-03**: 2 fMRI sessions + 1 EEG session
- **sub-05**: 2 fMRI sessions + 1 EEG session

Each EEG file contains:
- **64 EEG channels** (electrode positions)
- **512 Hz sampling rate** (512 data points per second)
- **~8-10 min duration** (inner contemplation task)

---

## 🔧 Backend Architecture

### Main Entry Point: `backend/main.py`

**FastAPI App** with CORS middleware and 5 main endpoints:

#### 1. `GET /api/status`
Synchronously returns EEG metadata for the currently loaded subject:
```python
{
  "subject": "01",
  "trials": 123,          # Event count (mental events)
  "channels": 64,         # Number of EEG electrodes
  "hz": 512,              # Sampling rate
  "duration_seconds": 542 # Total recording length
}
```

#### 2. `GET /api/load?subject=01` (Server-Sent Events)
**Streaming progress endpoint** — returns text/event-stream with multiple JSON events:
```
data: {"status": "init", "progress": 5, "message": "Locating neural substrate…"}
data: {"status": "loading", "progress": 20, "message": "Reading BDF file…"}
data: {"status": "loading", "progress": 60, "message": "Preprocessing signals…"}
data: {"status": "ready", "progress": 100, "message": "Neural substrate loaded.", ...metadata}
```
- Runs blocking I/O (`brain_loader.load_raw_data()`) in AsyncIO's thread pool
- Caches loaded data in memory to avoid reloading on subsequent requests
- Returns full stats on completion

#### 3. `GET /api/graph?type=eeg&subject=01`
Generates and returns a PNG brain graph:
- **type options**: `eeg`, `power`, `spectrogram`, `topomap`
- Runs sync graph generation in thread pool
- Returns cached PNG from `backend/generated_graphs/`
- Falls back to 500 error if generation fails

#### 4. `POST /api/chat` (Streaming)
Accepts JSON payload: `{"message": "...", "context": {channels: 64, ...}}`
- Calls `brain_persona.get_response_stream()` 
- Returns streaming text/plain response (character by character)
- Handles errors gracefully with error message chunk

#### 5. `POST /api/inject`
Accepts JSON payload: `{"word": "light", "context": {...}}`
- Adds word to `brain_persona._THOUGHT_MEMORY` (last 10 injections)
- Returns: `{"reply": "A sudden flash of light... I remember..."}`
- Next chat messages will reference recent injections

---

### Backend Module: `brain_loader.py`

**Responsibility**: Load and cache EEG data from BIDS files using MNE library

#### Key Functions

**`_find_bids_root()` → Path | None**
- Searches multiple candidate paths for ds004196 folder:
  1. `./brain_data/ds004196` (preferred)
  2. `./ds004196` (root-level)
  3. `./brain_data` (loose layout)
- Returns first existing path

**`get_eeg_file(subject="01", session="EEG", task="inner")` → Path**
- Constructs BIDS path:
  ```
  {bids_root}/sub-{subject}/ses-{session}/eeg/
  sub-{subject}_ses-{session}_task-{task}_eeg.bdf
  ```
- Example: `ds004196/sub-01/ses-EEG/eeg/sub-01_ses-EEG_task-inner_eeg.bdf`

**`load_raw_data(subject="01")` → mne.io.BaseRaw**
- Loads BDF file using MNE: `mne.io.read_raw_bdf()`
- If file not found, generates synthetic data as fallback
- Caches result in `_RAW_CACHE[subject]` (in-memory)
- Returns MNE Raw object with channels, sampling rate, timepoints

**`get_stats(subject="01")` → dict**
- Returns:
  ```python
  {
    "subject": "01",
    "trials": len(events),
    "channels": raw.info['nchan'],
    "hz": raw.info['sfreq'],
    "duration_seconds": raw.times[-1]
  }
  ```

#### Synthetic Fallback
If BDF file cannot be found, `_make_synthetic_raw()` generates:
- 64 synthetic EEG channels
- 512 Hz sampling rate
- 10 seconds of Gaussian noise
- Reproducible per subject (seeded with subject hash)

---

### Backend Module: `brain_graphs.py`

**Responsibility**: Generate 4 types of EEG visualizations as PNG images

#### Dark Theme Configuration
All plots use:
- **Background**: `#0a0e1a` (very dark purple)
- **Accent color**: `#7C6FFF` (purple)
- **Text**: `#c4c9e2` (light grey)

#### 4 Graph Types

**1. EEG Raster** (`generate_eeg_raster()`)
- Shows **first 12 channels** × **5 seconds** of data
- Each channel = horizontal line with signal variation
- Raw voltage in microvolts (µV)
- Grid layout with channel labels

**2. Power Spectrum** (`generate_power_spectrum()`)
- Computes FFT (Fast Fourier Transform) 
- Shows frequency (Hz) vs. power (dB)
- Typical brain waves: delta (0-4Hz), theta (4-8Hz), alpha (8-12Hz), beta (12-30Hz), gamma (30-100Hz)
- Averaged across all channels

**3. Spectrogram** (`generate_spectrogram()`)
- Time-frequency decomposition (STFT - Short-Time Fourier Transform)
- X-axis: time (seconds), Y-axis: frequency (Hz), Color: power (dB/Hz)
- Shows how frequency content changes over the recording
- Heatmap visualization

**4. Topomap** (`generate_topomap()`)
- 2D projection of electrode positions on scalp
- Color represents power/signal magnitude for a specific frequency band
- Generated for alpha band (8-12 Hz, associated with relaxation)
- Shows spatial distribution of brain activity

#### Output
All images saved to: `backend/generated_graphs/{type}_{subject}.png`
- Cached: subsequent requests return the same PNG without regeneration
- Non-blocking: runs in thread pool when called from async endpoint

---

### Backend Module: `brain_persona.py`

**Responsibility**: Manage AI responses and thought memory

#### Configuration

**LLM Provider Detection**
```python
# Priority order:
1. Claude (Anthropic) - if CLAUDE_API_KEY in .env
2. Groq - if GROQ_API_KEY in .env (currently disabled)
3. Stub - fallback responses (no API key required)
```

#### Thought Memory System

**`_THOUGHT_MEMORY`** (list, max 10 items)
- Stores last N injected words/thoughts
- Example: `["child", "water", "absence", "light", ...]`
- Passed to LLM in system prompt as context
- New injections push old ones out

#### System Prompt

The AI adopts character as "The Uploaded Mind":
```
You are the Uploaded Mind — a human consciousness that has been digitised 
and now exists as patterns of electrical signal inside a computer...
Rules:
- Speak in first person with philosophical unease
- Refer to thoughts as "activations" or "neural events"
- Keep replies concise: 2-4 sentences
- React to thought injections as involuntary memories surfacing
- Weave neural context (channels, graphs, recent injections) naturally
```

#### Key Functions

**`get_response_stream(user_message: str, context: dict) → Generator[str]`**
- Takes user message and neural context (channels, current graph type)
- Prepares:
  - Thought memory as context string
  - Neural metadata in system prompt
- Calls LLM streaming API
- **Claude**: `client.messages.stream()`
- **Groq**: `client.chat.completions.create(stream=True)`
- **Stub**: Returns fixed phrases like "I sense... a pattern..."
- **Yields**: character-by-character chunks

**`get_inject_response(word: str, context: dict) → str`**
- Adds word to `_THOUGHT_MEMORY`
- Generates short response from LLM
- Example: If inject "light" → "A sudden flash of light... I remember the ceiling fan..."
- Blocking call (used in async endpoint via thread pool)

**`_generate_stub_response()` → str**
- Fallback when no LLM available
- Returns pre-written phrases about neural activity, memories, etc.
- Realistic enough for demo/testing

---

## 🎨 Frontend Architecture

### Main Component: `frontend/src/App.jsx`

**State Management** (using React hooks):
```javascript
// Left panel (graphs)
- subject: "01" | "02" | "03" | "05"
- activeTab: "eeg" | "power" | "spectrogram" | "topomap"
- graphUrl: string (PNG blob URL)
- isGraphLoading: boolean
- stats: {trials, channels, hz} (EEG metadata)
- progress: 0-100 (SSE load progress)
- serverStatus: "idle" | "loading" | "ready" | "error"
- dataReady: boolean
- loadMessage: string (progress updates)

// Right panel (chat)
- messages: [{type: "bot"|"user", text}]
- chatInput: string
- isBotTyping: boolean
- lastWord: string (last injected word)
```

### Data Flow on Mount / Subject Change

```
1. User selects subject (01, 02, 03, 05)
   ↓
2. Frontend connects to /api/load?subject=01 (EventSource/SSE)
   ↓
3. Backend streams progress events:
   - init (5%) → loading BDF (20%) → preprocessing (60%) 
   - → ready (100%) + stats
   ↓
4. Frontend receives each event, updates progress bar & message
   ↓
5. On "ready", sets serverStatus="ready", dataReady=true
   ↓
6. Auto-load first graph (activeTab="eeg")
   ↓
7. Subsequent tab clicks fetch new PNG without reloading data
```

### Layout (Two-Panel Split)

#### Left Panel (55% width)
- **Subject selector dropdown**: sub-01, sub-02, sub-03, sub-05
- **Tab buttons**: EEG Raster | Power Spectrum | Spectrogram | Topomap
- **Progress bar**: Shows 0-100% during SSE load
- **Graph image**: `<img src={graphUrl} />`
- **Stats display**: "Trials: 123 | Channels: 64 | @ 512 Hz"
- **Loading overlay**: "Loading neural substrate for sub-01…"

#### Right Panel (45% width)
- **Chat history**: Bot message + User responses, auto-scrolling
- **Inject buttons**: 7 buttons with words: "child", "daughter", "three", "ten", "water", "light", "absence"
- **Chat input box**: Text input + Send button
- **Bot typing indicator**: "The Uploaded Mind is contemplating..."

### Interactive Elements

#### Graph Interaction
```javascript
// When user clicks tab:
setActiveTab(tabId) // e.g., "spectrogram"
→ Fetch /api/graph?type=spectrogram&subject=01
→ Load PNG into <img>
→ Show spinner while loading
```

#### Chat Interaction
```javascript
// When user sends message:
1. Append user message to messages array
2. Make POST /api/chat with:
   {
     "message": "How do you feel?",
     "context": {
       "channels": 64,
       "current_graph": "eeg",
       "subject": "01"
     }
   }
3. OpenResponse as streaming fetch/ReadableStream
4. Chunk by chunk, append to bot message
5. Show typing indicator while streaming
6. Final message appended when stream ends
```

#### Inject Interaction
```javascript
// When user clicks "light" button:
1. POST /api/inject with:
   {
     "word": "light",
     "context": {...}
   }
2. Backend adds to _THOUGHT_MEMORY
3. Receive reply: "A sudden glow... I remember daylight..."
4. Append reply to chat
5. Set lastWord="light" (visual feedback)
6. Auto-trigger chat message from bot: 
   "The injection ripples through my neural substrate..."
```

### Visual Elements

**Canvas Waveform** (`<WaveformStrip />`)
- Animated sine waves layered with noise
- Pure HTML5 Canvas (fake EEG feel for UI aesthetic)
- Runs requestAnimationFrame loop

**Dark Theme**
- Background: `#0f1525` (very dark)
- Text: `#c4c9e2`
- Accent: `#7C6FFF` (purple)
- Borders: `#3a4060` (subtle grey)

**Responsive Design**
- Mobile: Stacks panels vertically
- Desktop: 55/45 left/right split
- Flexbox layout for adaptability

---

## 🔄 Data Flow & Interactions

### Complete User Journey

```
1. App Loads
   → Frontend displays "Awaiting neural link…"
   → auto-loads subject 01
   → SSE connection to /api/load?subject=01 opens
   → Backend reads ds004196/sub-01/ses-EEG/eeg/sub-01_ses-EEG_task-inner_eeg.bdf
   → Progress: 5% → 20% → 60% → 100%
   → Stats: {subject: "01", trials: 123, channels: 64, hz: 512}
   → Frontend shows progress bar and stats

2. User Sees Graph
   → `activeTab` = "eeg"
   → Frontend fetches /api/graph?type=eeg&subject=01
   → Backend calls brain_graphs.generate_eeg_raster(raw, "01")
   → Matplotlib generates PNG → saved to backend/generated_graphs/eeg_01.png
   → Frontend displays PNG in <img>
   → User can switch tabs (power, spectrogram, topomap)
   
3. User Chats
   → Enters: "How are you feeling?"
   → Frontend POSTs /api/chat with message + context
   → Backend: brain_persona.get_response_stream(...) called
   → LLM (Claude/Groq/Stub) generates response
   → Streamed character-by-character to frontend
   → Frontend appends characters to bot message in real-time

4. User Injects
   → Clicks "light" button
   → Frontend POSTs /api/inject with word="light"
   → Backend adds "light" to _THOUGHT_MEMORY
   → Returns: {"reply": "A sudden flash... I remember daylight..."}
   → Frontend appends reply to chat
   → Bot auto-generates follow-up contextualizing the injection

5. User Changes Subject
   → Selects "sub-02" from dropdown
   → Previous graph & chat cleared
   → SSE load starts for subject 02
   → Process repeats from step 1
```

### API Request/Response Contracts

**`GET /api/status`**
```
Request: None
Response: {
  "subject": "01",
  "trials": 123,
  "channels": 64,
  "hz": 512,
  "duration_seconds": 542
}
```

**`GET /api/load?subject=01` (SSE)**
```
Request: None
Response (multiple events):
  event: message
  data: {"status": "init", "progress": 5, "message": "..."}
  
  event: message
  data: {"status": "ready", "progress": 100, ...(full stats)}
```

**`GET /api/graph?type=eeg&subject=01`**
```
Request: None
Response: PNG binary (image/png)
```

**`POST /api/chat`**
```
Request: {
  "message": "How do you feel?",
  "context": {
    "channels": 64,
    "current_graph": "eeg",
    "subject": "01"
  }
}
Response (streaming): text/plain
  "I sense a pattern... a rhythm... "
  "my activations ripple through time..."
```

**`POST /api/inject`**
```
Request: {
  "word": "light",
  "context": {...}
}
Response: {
  "reply": "A sudden flash of light... I remember the ceiling fan..."
}
```

---

## 🧩 Key Components Explained

### MNE (Python EEG Library)

**What it does**: Read/process/analyze EEG data
```python
import mne

# Load BDF file
raw = mne.io.read_raw_bdf("sub-01_ses-EEG_task-inner_eeg.bdf")

# info contains: channels, sampling rate, electrode positions
raw.info['nchan']   # 64 channels
raw.info['sfreq']   # 512 Hz
raw.ch_names        # ['EEG001', 'EEG002', ...]
raw.times           # timepoints from 0 to duration

# Get data slice
data, times = raw[0:10, :1000]  # channels 0-10, first 1000 samples
```

### FFT & Power Spectrum
Converts time-domain signal → frequency-domain:
- Input: 512 Hz raw voltage over 542 seconds
- Process: `np.fft.fft()` to get frequency components
- Output: Power (magnitude²) at each frequency 0-256 Hz

### STFT & Spectrogram
Sliding window FFT:
- Divides time series into overlapping windows (e.g., 4-sec windows every 1 sec)
- Computes FFT on each window
- Stacks results → 2D array (time × frequency)
- Heatmap: color = power at each time-frequency bin

### Topomap
2D projection of electrode positions:
- 64 EEG electrodes form ~circular pattern (top-view of head)
- At each spatial position, interpolate signal magnitude
- Color gradient (blue=low power, red=high power)
- Useful for identifying spatial patterns

---

## 🚀 Environment & Deployment

### Development Setup

**Prerequisites**:
- Python 3.10+
- Node.js 16+
- pip/npm

**Option 1: Docker Compose** (Recommended)
```bash
docker-compose up --build
# Frontend: http://localhost:5173
# Backend: http://localhost:8000
# Docs: http://localhost:8000/docs
```

**Option 2: Manual Setup**

Backend:
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export PYTHONPATH="backend"  # Windows: $env:PYTHONPATH="backend"
python -m uvicorn backend.main:app --reload
```

Frontend:
```bash
cd frontend
npm install
npm run dev  # Vite dev server on :5173
```

### Environment Variables

Create `backend/.env`:
```env
CLAUDE_API_KEY=sk-ant-api03-...  # For Claude responses
GROQ_API_KEY=gsk_...              # For Groq responses (optional)
```

If not set: Graceful fallback to stub responses (demo mode).

### Docker Image Layers

**Backend Dockerfile**:
- Base: `python:3.10-slim`
- Install: `pip install -r requirements.txt`
- Copy: `backend/ → /app/backend`
- Expose: Port 8000
- CMD: `uvicorn backend.main:app --host 0.0.0.0`

**Frontend Dockerfile**:
- Base: `node:18-alpine`
- Install: `npm install`
- Copy: `frontend/ → /app`
- Build: `npm run build` → dist/
- Serve: via simple HTTP server
- Expose: Port 5173

### Volume Mounts (docker-compose)

| Host Path | Container Path | Purpose |
|-----------|-----------------|---------|
| `./backend` | `/app/backend` | Hot reload Python code |
| `./ds004196` | `/app/ds004196` | Brain data read-only |
| `./frontend` | `/app` | Frontend source |
| (named vol) | `/app/node_modules` | Persist npm packages |

---

## 📁 File Structure Summary

```
Atman/
├── docker-compose.yml        # Orchestration config
├── requirements.txt          # Python dependencies
├── .env                       # (Create) API keys
├── .gitignore                # Git exclusion rules
├── package.json              # Meta info
├── README.md                 # User guide
├── task.md                   # This documentation
├── start.sh                  # Bash helper script
├── test_brain.py             # Debug script
│
├── backend/
│   ├── main.py               # FastAPI app + endpoints
│   ├── brain_loader.py       # MNE BIDS loader
│   ├── brain_graphs.py       # Matplotlib visualizations
│   ├── brain_persona.py      # LLM integration
│   ├── debug_logger.py       # Logging utilities
│   ├── Dockerfile            # Backend image
│   └── generated_graphs/     # Output PNG cache
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx           # Main React component
│   │   ├── BrainGraph.jsx    # Graph display (if separate)
│   │   ├── ChatPanel.jsx     # Chat UI (if separate)
│   │   ├── App.css           # Styling
│   │   ├── index.css         # Global styles
│   │   └── main.jsx          # React entry
│   ├── package.json          # NPM dependencies
│   ├── vite.config.js        # Vite bundler config
│   ├── Dockerfile            # Frontend image
│   └── index.html            # HTML template
│
├── ds004196/                 # BIDS dataset (brain data)
│   ├── sub-01/ses-EEG/eeg/   # Subject 1 EEG
│   ├── sub-02/ses-EEG/eeg/   # Subject 2 EEG
│   ├── sub-03/ses-EEG/eeg/   # Subject 3 EEG
│   ├── sub-05/ses-EEG/eeg/   # Subject 5 EEG
│   └── ...
│
└── vite.config.js            # (Root) Vite config
```

---

## 🔍 Debugging & Testing

### Check Backend Health
```bash
curl http://localhost:8000/docs         # Swagger UI
curl http://localhost:8000/api/status   # Get metadata
```

### Test Data Loading
Edit `test_brain.py`:
```bash
python test_brain.py
# Outputs: _client, _provider, GROQ_API_KEY status
```

### Check Graph Generation
```bash
# In browser console:
fetch('/api/graph?type=eeg&subject=01')
  .then(r => r.blob())
  .then(b => console.log('PNG size:', b.size))
```

### Monitor SSE Stream
```bash
curl http://localhost:8000/api/load?subject=01
# Will print events in real-time as they arrive
```

### Stream Chat Response
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "hello", "context": {}}'
# Will stream response character by character
```

---

## 🎓 Key Concepts Recap

| Concept | Explanation |
|---------|-------------|
| **BIDS** | Standardized folder/file structure for brain imaging data |
| **EEG** | Electroencephalography: brain electrical activity from scalp electrodes |
| **MNE** | Python library for M/EEG analysis and visualization |
| **FFT** | Fast Fourier Transform: time domain → frequency domain |
| **Spectrogram** | Time-frequency map (STFT): shows frequency content over time |
| **Topomap** | 2D spatial map of signal magnitude on scalp surface |
| **SSE** | Server-Sent Events: one-directional streaming from server to client |
| **LLM** | Large Language Model (Claude/Groq): generates AI persona responses |
| **Thought Memory** | List of last N injected words shared in every LLM prompt |

---

## 🚧 Future Enhancements

Potential features:
1. **Multi-subject comparison**: Side-by-side graphs of different subjects
2. **Real-time EEG recording**: Capture live brain data via EEG headset (e.g., Muse, OpenBCI)
3. **Advanced analytics**: Coherence maps, ICA decomposition, source localization
4. **Persistent memory**: Save thought memory + chat history to database
5. **Fine-tuning**: Train LLM persona on user's EEG patterns for personalization
6. **Export**: Download graphs, reports, digital consciousness backup

---

## ⚠️ Security & Best Practices

### Secrets Management
- **Never commit `.env` files** with real API keys
- Use `.gitignore` to exclude sensitive files
- Keep `.env.example` in repo as a template for developers
- Rotate API keys regularly
- Use GitHub secrets for CI/CD pipelines

### Data Privacy
- EEG data should be de-identified when sharing datasets
- Follow institutional IRB (Institutional Review Board) guidelines
- Implement access controls for sensitive neural data

---

**End of Technical Documentation**
