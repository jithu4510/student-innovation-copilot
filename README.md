# Innovation Copilot - Hardware Engineering Workspace 🛠️

**Innovation Copilot** is a clean, modern, student-friendly hardware engineering workspace designed to help middle/high school students (aged 13–18) turn hardware project ideas into working, verified electronics prototypes.

> ⚠️ **STRICT PRINCIPLE**: This application is **100% NON-AI and deterministic**. It does **NOT** use LLMs, chatbots, AI APIs, or generated responses. All intelligence stems from structured project data and rule-based diagnostic state machines.

---

## 🌟 Key Product Features

1. **Engineering Workspace UI**: Clean, professional layout (similar to GitHub Projects / Linear / Xcode) with zero AI chat bubbles or fake marketing fluff.
2. **Dynamic Custom Component System**:
   - Students can type **any custom components** (e.g. `TDS Sensor`, `Turbidity Sensor`, `DS18B20`, `SSD1306 OLED 0.96"`, `Breadboard`).
   - Add/remove unlimited component text rows with optional quick-suggestion shortcuts.
   - Known components display verified pinouts; custom components are preserved without inventing fake specs.
3. **Structured 5-Stage Build System**:
   - Organizes projects into 5 clear stages: `1. Preparation`, `2. Assembly`, `3. Wiring`, `4. Software/Test`, and `5. Final Verification`.
   - Each step features `title`, `instruction`, `why_matters`, `required_components`, `warning_note`, and `test_question`.
4. **Deterministic Troubleshooting Engine**:
   - Interactive diagnostic state machines guiding students through step-by-step diagnostic checks (`[ YES ]` / `[ NO ]`) to exact fix actions.
5. **Full SQLite Persistence**:
   - Projects, typed custom components, build steps, test results, and diagnostic sessions persist across browser refreshes and application restarts.
6. **Pre-Loaded Demo Project**:
   - Ready-to-test **"ESP32 OLED Display"** project demonstrating the complete end-to-end flow.

---

## 📁 Project Structure

```
innovation-copilot/
├── app.py                      # Flask REST API backend
├── database.py                 # SQLite schema, tables & component library seeding
├── troubleshooting_engine.py   # State-machine hardware diagnostic decision trees
├── build_guide_engine.py       # Generator for structured 5-stage build plans
├── templates/
│   └── index.html              # Modern, responsive engineering workspace HTML
├── static/
│   ├── css/
│   │   └── style.css           # Workspace CSS theme (slate/navy accents)
│   └── js/
│       └── app.js              # SPA frontend controller & state manager
├── test_e2e.py                 # Automated test suite validating the 16-step user lifecycle
└── README.md                   # Documentation & setup guide
```

---

## 🧪 Automated 16-Step Lifecycle Test

Run the full end-to-end verification suite:

```bash
C:\Users\jites\AppData\Local\Python\bin\python.exe test_e2e.py
```

### Verified User Lifecycle Flow:
1. Open application.
2. Create project ("Smart Water Quality Monitor").
3. Type 5 custom components (`ESP32-WROOM`, `SSD1306 OLED 0.96"`, `TDS Sensor`, `Turbidity Sensor`, `DS18B20`).
4. Save project to SQLite database.
5. Simulate browser refresh & confirm persistence.
6. Open project workspace.
7. Complete Build Step 1 (Preparation).
8. Fail test checkpoint on Step 2 (Assembly).
9. Enter deterministic troubleshooting sequence.
10. Follow diagnostic decision tree (`[ YES ]` / `[ NO ]`).
11. Resolve issue & apply recommended fix.
12. Complete remaining build steps.
13. Return to dashboard & verify 100% completion status.

---

## 🚀 How to Run Locally

```bash
# 1. Navigate to project directory
cd C:\Users\jites\.gemini\antigravity\scratch\innovation-copilot

# 2. Run Flask application server
C:\Users\jites\AppData\Local\Python\bin\python.exe app.py

# 3. Open in browser:
http://127.0.0.1:5000
```
