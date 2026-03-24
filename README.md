# 💚 AI-Powered Preventive Healthcare Score System

An AI-powered web application that collects user health data and generates a **Preventive Healthcare Score** (0–100) using Google Gemini AI. Features health analytics dashboard, monthly reports, AI chatbot, and doctor recommendations.

## Tech Stack

| Layer     | Technology                    |
|-----------|-------------------------------|
| Frontend  | HTML, CSS, JavaScript         |
| Backend   | Python Flask                   |
| Database  | SQLite                         |
| AI        | Google Gemini API              |
| Charts    | Chart.js                       |

## Features

- 🤖 **AI Health Score** — Gemini-powered preventive healthcare scoring (0–100)
- 📊 **Dashboard** — Score trends, radar chart, vital metrics, trackers
- 📄 **Monthly Reports** — AI-generated health analysis and trends
- 💬 **AI Chatbot** — Ask health questions powered by Gemini
- ⚖️ **BMI Calculator** — Auto-calculated from height/weight
- 🚶 **Step Tracker** — Daily step count monitoring
- 💧 **Water Intake Tracker** — Daily hydration tracking
- 🩺 **Doctor Recommendations** — Specialist suggestions based on risk level
- 🔐 **Session Auth** — Secure login/register system

## Risk Levels

| Score Range | Risk Level  |
|-------------|-------------|
| 80–100      | ✅ Healthy   |
| 60–79       | ⚠️ Moderate  |
| 40–59       | 🔶 Risk      |
| Below 40    | 🔴 High Risk |

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Gemini API Key (Optional)
Create a `.env` file in the `backend/` folder:
```
GEMINI_API_KEY=your_api_key_here
```
> The app works without a Gemini key using local score calculation fallbacks.

### 3. Run the Backend
```bash
cd backend
python app.py
```
Server starts on `http://localhost:5000`

### 4. Open Frontend
Open `frontend/login.html` in your browser, or serve with:
```bash
cd frontend
python -m http.server 8000
```
Then visit `http://localhost:8000/login.html`

## API Endpoints

| Method | Endpoint               | Description                 |
|--------|------------------------|-----------------------------|
| POST   | `/register`            | Register new user            |
| POST   | `/login`               | Login with session           |
| POST   | `/logout`              | Logout                       |
| GET    | `/check-session`       | Verify authentication        |
| POST   | `/submit-health-data`  | Submit health data + get score |
| GET    | `/get-score`           | Get latest score + history   |
| GET    | `/get-report?month=`   | Monthly report               |
| POST   | `/chatbot`             | AI chatbot                   |

## Folder Structure

```
project/
├── frontend/
│   ├── index.html        # Health data form
│   ├── login.html        # Login page
│   ├── register.html     # Registration page
│   ├── dashboard.html    # Health dashboard
│   ├── report.html       # Monthly reports
│   ├── chatbot.html      # AI chatbot
│   ├── style.css         # Styles
│   └── script.js         # Frontend logic
├── backend/
│   ├── app.py            # Flask server
│   ├── gemini_ai.py      # AI module
│   └── database.db       # SQLite (auto-created)
├── requirements.txt
└── README.md
```
