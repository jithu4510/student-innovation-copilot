/**
 * Innovation Copilot SPA Frontend Controller
 * AI-Powered Hardware Engineering Workspace & Mentor.
 * Handles AI Plan Rendering, Contextual Engineering Mentor Q&A,
 * Vision Photo Inspection, Deterministic Fallback UI, & Real Analytics.
 */

let currentProjectId = null;
let currentProjectData = null;
let allComponentsData = [];
let uploadedPhotoBase64 = null;

document.addEventListener("DOMContentLoaded", () => {
    loadDashboard();
    fetchComponentsList();
});

// ---------------------------------------------------------
// VIEW NAVIGATION
// ---------------------------------------------------------
function showView(viewId) {
    document.querySelectorAll(".app-view").forEach(el => el.classList.add("d-none"));
    document.querySelectorAll(".eng-nav-btn").forEach(el => el.classList.remove("active"));

    const targetView = document.getElementById(`view-${viewId}`);
    if (targetView) {
        targetView.classList.remove("d-none");
    }

    const navBtn = document.getElementById(`nav-${viewId}`);
    if (navBtn) {
        navBtn.classList.add("active");
    }

    if (viewId === 'dashboard') {
        loadDashboard();
    } else if (viewId === 'create-project') {
        initCreateProjectForm();
    } else if (viewId === 'analytics') {
        loadAnalyticsView();
    } else if (viewId === 'components') {
        loadComponentsView();
    }
}

// ---------------------------------------------------------
// DASHBOARD LOGIC
// ---------------------------------------------------------
async function loadDashboard() {
    const grid = document.getElementById("projects-grid");
    grid.innerHTML = `<div class="col-12 text-center py-5"><div class="spinner-border text-primary"></div><p class="mt-2 text-muted">Loading projects...</p></div>`;

    try {
        const res = await fetch("/api/projects");
        const projects = await res.json();

        if (!projects || projects.length === 0) {
            grid.innerHTML = `
                <div class="col-12 text-center py-5">
                    <div class="card p-5 border-0 shadow-sm rounded-3 bg-white">
                        <i class="bi bi-box-seam display-3 text-secondary mb-3"></i>
                        <h4 class="fw-bold text-dark">Your first prototype starts here.</h4>
                        <p class="text-muted mb-4" style="max-width: 500px; margin: 0 auto;">
                            Describe your project idea naturally, type your available hardware components, and let the AI Engineering Mentor guide your build.
                        </p>
                        <div>
                            <button class="btn btn-primary btn-lg rounded-2 px-4 fw-bold me-2" onclick="showView('create-project')">
                                <i class="bi bi-plus-lg me-1"></i> Create Project
                            </button>
                            <button class="btn btn-outline-secondary btn-lg rounded-2 px-4" onclick="launchDemoProject()">
                                Open ESP32 OLED Demo
                            </button>
                        </div>
                    </div>
                </div>
            `;
            return;
        }

        grid.innerHTML = projects.map(p => {
            const compsCount = p.custom_components ? p.custom_components.length : 0;
            const updatedDate = new Date(p.updated_at || Date.now()).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            const difficulty = p.estimated_difficulty || "Intermediate";

            return `
                <div class="col-md-6 col-lg-4">
                    <div class="card h-100 border-0 shadow-sm rounded-3 overflow-hidden">
                        <div class="card-body p-4 d-flex flex-column">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <span class="badge ${p.microcontroller === 'ESP32' ? 'bg-primary-subtle text-primary' : 'bg-success-subtle text-success'} rounded-pill px-3 py-1 font-monospace fw-bold">
                                    <i class="bi bi-cpu me-1"></i> ${p.microcontroller}
                                </span>
                                <span class="badge bg-secondary-subtle text-dark font-monospace">${difficulty}</span>
                            </div>

                            <h4 class="fw-bold mb-1 text-dark">${p.name}</h4>
                            <p class="text-muted small mb-3 flex-grow-1">${p.goal}</p>

                            <div class="mb-3 bg-light p-3 rounded-2">
                                <div class="d-flex justify-content-between align-items-center mb-1">
                                    <small class="fw-bold text-secondary font-monospace">STAGE: ${p.current_stage.toUpperCase()}</small>
                                    <small class="fw-bold text-dark font-monospace">${p.progress_percent}%</small>
                                </div>
                                <div class="progress rounded-pill" style="height: 6px;">
                                    <div class="progress-bar ${p.status === 'completed' ? 'bg-success' : 'bg-primary'}" style="width: ${p.progress_percent}%;"></div>
                                </div>
                            </div>

                            <div class="d-flex justify-content-between align-items-center mb-3 text-muted small font-monospace">
                                <span><i class="bi bi-cpu me-1"></i> ${compsCount} Components</span>
                                <span><i class="bi bi-clock me-1"></i> ${updatedDate}</span>
                            </div>

                            <div class="d-grid mt-auto">
                                <button class="btn ${p.status === 'completed' ? 'btn-outline-success' : 'btn-primary'} rounded-2 fw-semibold" onclick="openWorkspace(${p.id})">
                                    <i class="bi bi-arrow-right-circle me-1"></i> ${p.status === 'completed' ? 'View Working Prototype' : 'Continue Build'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

    } catch (err) {
        console.error("Failed to load dashboard projects", err);
        grid.innerHTML = `<div class="col-12 text-center text-danger py-4">Failed to load projects from server.</div>`;
    }
}

// ---------------------------------------------------------
// DEMO LAUNCHER
// ---------------------------------------------------------
async function launchDemoProject() {
    try {
        const res = await fetch("/api/projects");
        const projects = await res.json();
        const demo = projects.find(p => p.name === "ESP32 OLED Display");

        if (demo) {
            openWorkspace(demo.id);
        } else {
            const resetRes = await fetch("/api/demo/reset", { method: "POST" });
            const data = await resetRes.json();
            openWorkspace(data.project_id);
        }
    } catch (err) {
        console.error("Error launching demo", err);
    }
}

async function resetDemoProject(projectId) {
    if (confirm("Reset the demo project back to initial build step?")) {
        await fetch("/api/demo/reset", { method: "POST" });
        openWorkspace(projectId);
    }
}

// ---------------------------------------------------------
// CREATE PROJECT & DYNAMIC CUSTOM COMPONENTS
// ---------------------------------------------------------
function initCreateProjectForm() {
    const container = document.getElementById("custom-components-container");
    container.innerHTML = "";
    addComponentInputRow("ESP32 Board");
    addComponentInputRow("SSD1306 OLED 0.96\"");
    addComponentInputRow("Jumper Wires");
}

function addComponentInputRow(val = "") {
    const container = document.getElementById("custom-components-container");
    const rowId = 'comp-row-' + Date.now() + '-' + Math.floor(Math.random() * 1000);

    const div = document.createElement("div");
    div.className = "input-group mb-1 custom-comp-row-group";
    div.id = rowId;

    div.innerHTML = `
        <span class="input-group-text bg-light text-muted border-end-0"><i class="bi bi-cpu"></i></span>
        <input type="text" class="form-control custom-comp-input border-start-0" value="${val}" placeholder="Type component name e.g. TDS Sensor, DS18B20..." required>
        <button class="btn btn-outline-danger btn-sm px-3" type="button" onclick="removeComponentRow('${rowId}')">
            <i class="bi bi-trash"></i> Remove
        </button>
    `;

    container.appendChild(div);
}

function removeComponentRow(rowId) {
    const row = document.getElementById(rowId);
    if (row) {
        row.remove();
    }
}

function addSuggestedComponent(name) {
    const inputs = Array.from(document.querySelectorAll(".custom-comp-input"));
    const exists = inputs.some(i => i.value.trim().toLowerCase() === name.toLowerCase());
    if (!exists) {
        addComponentInputRow(name);
    }
}

async function handleCreateProject(e) {
    e.preventDefault();
    const name = document.getElementById("project-name").value;
    const goal = document.getElementById("project-goal").value;
    const microcontroller = document.querySelector('input[name="microcontroller"]:checked').value;

    const custom_components = Array.from(document.querySelectorAll(".custom-comp-input"))
                                    .map(i => i.value.trim())
                                    .filter(val => val.length > 0);

    if (custom_components.length === 0) {
        alert("Please add at least 1 component.");
        return;
    }

    try {
        const res = await fetch("/api/projects", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                name, goal, microcontroller, custom_components
            })
        });

        const data = await res.json();
        if (res.ok) {
            openWorkspace(data.project_id);
        } else {
            alert(data.error || "Failed to create project");
        }
    } catch (err) {
        console.error("Error creating project", err);
    }
}

// ---------------------------------------------------------
// WORKSPACE VIEW & CONTEXTUAL MENTOR UI
// ---------------------------------------------------------
async function openWorkspace(projectId) {
    currentProjectId = projectId;
    showView('workspace');
    const container = document.getElementById("workspace-content");
    container.innerHTML = `<div class="text-center py-5"><div class="spinner-border text-primary"></div></div>`;

    try {
        const res = await fetch(`/api/projects/${projectId}`);
        const p = await res.json();
        currentProjectData = p;

        const isDemo = p.name === "ESP32 OLED Display";
        const currentStep = p.steps[p.current_step_index] || p.steps[p.steps.length - 1];
        const isAiAvailable = p.ai_available || false;

        container.innerHTML = `
            <!-- TOP WORKSPACE BAR -->
            <div class="card border-0 shadow-sm rounded-3 mb-4">
                <div class="card-body p-4">
                    <div class="d-flex flex-wrap justify-content-between align-items-center mb-3 gap-2">
                        <div>
                            <div class="d-flex align-items-center gap-2 mb-2">
                                <span class="badge ${p.microcontroller === 'ESP32' ? 'bg-primary' : 'bg-success'} rounded-pill px-3 py-1 font-monospace">
                                    <i class="bi bi-cpu me-1"></i> ${p.microcontroller}
                                </span>
                                <span class="badge ${isAiAvailable ? 'bg-info-subtle text-info-emphasis' : 'bg-warning-subtle text-dark'} font-monospace">
                                    <i class="bi ${isAiAvailable ? 'bi-robot' : 'bi-shield-check'} me-1"></i> ${isAiAvailable ? 'AI Mentor Active' : 'Guided Offline Mode'}
                                </span>
                            </div>
                            <h2 class="fw-bold mb-1 text-dark">${p.name}</h2>
                            <p class="text-muted lead fs-6 m-0">${p.goal}</p>
                        </div>
                        <div class="d-flex gap-2">
                            <button class="btn btn-outline-primary btn-sm rounded-2" onclick="openPhotoModal()">
                                <i class="bi bi-camera me-1"></i> Inspect Photo
                            </button>
                            ${isDemo ? `
                                <button class="btn btn-outline-warning btn-sm rounded-2" onclick="resetDemoProject(${p.id})">
                                    <i class="bi bi-arrow-counterclockwise me-1"></i> Reset Demo
                                </button>
                            ` : ''}
                            <button class="btn btn-outline-secondary btn-sm rounded-2" onclick="showView('dashboard')">
                                <i class="bi bi-arrow-left me-1"></i> Dashboard
                            </button>
                        </div>
                    </div>

                    <!-- Progress Indicator -->
                    <div class="row align-items-center bg-light rounded-2 p-3 g-2">
                        <div class="col-md-4">
                            <small class="text-muted d-block font-monospace">CURRENT STAGE</small>
                            <span class="fw-bold text-primary font-monospace fs-5">${p.current_stage.toUpperCase()}</span>
                        </div>
                        <div class="col-md-5">
                            <small class="text-muted d-block font-monospace">PROGRESS (${p.completed_steps}/${p.total_steps} STEPS COMPLETED)</small>
                            <div class="d-flex align-items-center gap-2">
                                <div class="progress flex-grow-1 rounded-pill" style="height: 8px;">
                                    <div class="progress-bar ${p.status === 'completed' ? 'bg-success' : 'bg-primary'}" style="width: ${p.progress_percent}%;"></div>
                                </div>
                                <span class="fw-bold font-monospace">${p.progress_percent}%</span>
                            </div>
                        </div>
                        <div class="col-md-3 text-md-end">
                            ${p.status === 'completed' ? `
                                <span class="badge bg-success fs-6 rounded-pill px-3 py-2">
                                    <i class="bi bi-check-circle-fill me-1"></i> Prototype Working!
                                </span>
                            ` : `
                                <button class="btn btn-outline-danger btn-sm rounded-2" onclick="startTroubleshooting(${p.id})">
                                    <i class="bi bi-tools me-1"></i> Troubleshoot
                                </button>
                            `}
                        </div>
                    </div>
                </div>
            </div>

            <!-- WORKSPACE SPLIT PANELS -->
            <div class="row g-4">
                <!-- LEFT SIDEBAR: COMPONENTS & TIMELINE CHECKLIST -->
                <div class="col-lg-4">
                    <!-- COMPONENTS LIST PANEL -->
                    <div class="card border-0 shadow-sm rounded-3 mb-4">
                        <div class="card-header bg-white border-bottom p-3">
                            <h6 class="fw-bold m-0 font-monospace text-secondary"><i class="bi bi-cpu-fill me-1"></i> PROJECT COMPONENTS (${p.custom_components.length})</h6>
                        </div>
                        <div class="card-body p-3">
                            <div class="d-flex flex-column gap-2">
                                ${p.custom_components.map(c => `
                                    <div class="d-flex justify-content-between align-items-center p-2 rounded-2 bg-light border">
                                        <span class="fw-semibold text-dark small">${c.custom_name}</span>
                                        ${c.is_verified ? 
                                            '<span class="badge bg-success-subtle text-success" style="font-size:0.7rem;">Verified Specs</span>' : 
                                            '<span class="badge bg-warning-subtle text-dark" style="font-size:0.7rem;">Needs Verification</span>'
                                        }
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>

                    <!-- 5-STAGE TIMELINE CHECKLIST -->
                    <div class="card border-0 shadow-sm rounded-3">
                        <div class="card-header bg-white border-bottom p-3">
                            <h6 class="fw-bold m-0 font-monospace text-secondary"><i class="bi bi-list-task me-1"></i> BUILD TIMELINE</h6>
                        </div>
                        <div class="card-body p-0">
                            <div class="list-group list-group-flush">
                                ${p.steps.map((s, idx) => {
                                    const isPassed = s.status === 'passed';
                                    const isCurrent = idx === p.current_step_index && p.status !== 'completed';

                                    return `
                                        <div class="list-group-item step-checklist-item ${isPassed ? 'completed' : isCurrent ? 'active' : ''} d-flex align-items-center justify-content-between cursor-pointer" onclick="selectWorkspaceStep(${p.id}, ${idx})">
                                            <div class="d-flex align-items-center gap-2">
                                                <span class="step-badge ${isPassed ? 'bg-success text-white' : isCurrent ? 'bg-primary text-white' : 'bg-light text-muted border'}">
                                                    ${isPassed ? '✓' : s.step_number}
                                                </span>
                                                <div>
                                                    <div class="fw-bold small ${isCurrent ? 'text-primary' : 'text-dark'}">${s.title}</div>
                                                    <small class="text-muted font-monospace" style="font-size:0.75rem;">${s.category}</small>
                                                </div>
                                            </div>
                                            ${isPassed ? '<i class="bi bi-check-lg text-success fs-5"></i>' : isCurrent ? '<i class="bi bi-chevron-right text-primary"></i>' : ''}
                                        </div>
                                    `;
                                }).join('')}
                            </div>
                        </div>
                    </div>
                </div>

                <!-- RIGHT MAIN PANEL: ACTIVE STEP, TEST CHECKPOINT & CONTEXTUAL AI MENTOR -->
                <div class="col-lg-8">
                    ${currentStep ? `
                        <div class="card border-0 shadow-sm rounded-3 overflow-hidden mb-4">
                            <div class="card-header bg-dark text-white p-4 d-flex justify-content-between align-items-center">
                                <div>
                                    <span class="badge bg-primary font-monospace text-uppercase px-3 py-1 mb-1">${currentStep.category}</span>
                                    <h3 class="fw-bold mb-0">Step ${currentStep.step_number}: ${currentStep.title}</h3>
                                </div>
                                <span class="badge ${currentStep.status === 'passed' ? 'bg-success' : 'bg-warning text-dark'} px-3 py-2 font-monospace">
                                    ${currentStep.status === 'passed' ? 'PASSED ✓' : 'IN PROGRESS'}
                                </span>
                            </div>

                            <div class="card-body p-4 p-md-5">
                                <div class="mb-4">
                                    <h5 class="fw-bold text-dark mb-2"><i class="bi bi-terminal me-2 text-primary"></i> Instructions:</h5>
                                    <p class="fs-5 text-dark lh-base p-3 bg-light rounded-3 border-start border-4 border-primary m-0">${currentStep.instruction}</p>
                                </div>

                                <div class="mb-4 p-3 bg-blue-subtle rounded-3 border-start border-4 border-info">
                                    <h6 class="fw-bold text-primary mb-1"><i class="bi bi-lightbulb-fill me-2"></i> Why this step matters:</h6>
                                    <p class="mb-0 text-dark opacity-90 small">${currentStep.why_matters}</p>
                                </div>

                                ${currentStep.warning_note ? `
                                    <div class="mb-4 p-3 bg-warning-subtle rounded-3 border-start border-4 border-warning">
                                        <h6 class="fw-bold text-dark mb-1"><i class="bi bi-exclamation-triangle-fill text-warning me-2"></i> Safety Warning:</h6>
                                        <p class="mb-0 text-dark small">${currentStep.warning_note}</p>
                                    </div>
                                ` : ''}

                                <div class="mb-4">
                                    <small class="text-muted font-monospace fw-bold d-block mb-1">REQUIRED COMPONENTS:</small>
                                    <span class="badge bg-secondary-subtle text-dark font-monospace px-3 py-2 fs-6">${currentStep.required_components}</span>
                                </div>

                                <!-- TESTING CHECKPOINT BOX -->
                                <div class="p-4 bg-light border-2 border-dashed rounded-3 text-center mt-5">
                                    <span class="badge bg-dark font-monospace px-3 py-1 mb-2">TEST CHECKPOINT</span>
                                    <h4 class="fw-bold text-dark mb-3">${currentStep.test_question}</h4>

                                    <div class="d-flex justify-content-center gap-3 mt-4">
                                        <button class="btn btn-success btn-lg rounded-2 px-4 py-3 fw-bold shadow-sm" onclick="submitTestResult(${p.id}, ${currentStep.id}, 'passed')">
                                            <i class="bi bi-check-circle-fill me-2"></i> YES — It works
                                        </button>
                                        <button class="btn btn-danger btn-lg rounded-2 px-4 py-3 fw-bold shadow-sm" onclick="submitTestResult(${p.id}, ${currentStep.id}, 'failed')">
                                            <i class="bi bi-x-circle-fill me-2"></i> NO — Something is wrong
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- CONTEXTUAL PROJECT MENTOR AREA -->
                        <div class="card border-0 shadow-sm rounded-3 mentor-panel">
                            <div class="d-flex justify-content-between align-items-center mb-3">
                                <h5 class="fw-bold text-dark m-0"><i class="bi bi-robot text-primary me-2"></i> Engineering Mentor</h5>
                                ${!isAiAvailable ? '<span class="badge bg-warning-subtle text-dark small"><i class="bi bi-wifi-off me-1"></i> Guided Offline Mode</span>' : ''}
                            </div>

                            <p class="text-muted small mb-3">Ask questions about <strong>Step ${currentStep.step_number}: ${currentStep.title}</strong>. The mentor uses your project memory context.</p>

                            <!-- Quick Action Prompt Chips -->
                            <div class="d-flex flex-wrap gap-2 mb-3">
                                <button class="mentor-chip" onclick="sendQuickMentorPrompt('Explain this step')">💡 Explain this step</button>
                                <button class="mentor-chip" onclick="sendQuickMentorPrompt('Why are we doing this?')">❓ Why are we doing this?</button>
                                <button class="mentor-chip" onclick="sendQuickMentorPrompt('What happens if I use 5V?')">⚡ What happens if I use 5V?</button>
                                <button class="mentor-chip" onclick="sendQuickMentorPrompt('How can I test this before continuing?')">🔍 How to test this?</button>
                            </div>

                            <!-- Q&A History Log -->
                            <div id="mentor-qa-log" class="mb-3">
                                ${p.ai_messages && p.ai_messages.length > 0 ? 
                                    p.ai_messages.map(m => `
                                        <div class="qa-card">
                                            <div class="qa-card-user"><i class="bi bi-person-fill text-primary me-1"></i> "${m.user_question}"</div>
                                            <div class="qa-card-response">${m.ai_response}</div>
                                        </div>
                                    `).join('') : '<small class="text-muted italic d-block mb-2">No mentor questions asked yet for this step.</small>'
                                }
                            </div>

                            <!-- Input Form -->
                            <div class="input-group">
                                <input type="text" id="mentor-question-input" class="form-control rounded-start-2" placeholder="Ask your engineering mentor a question about this step..." onkeypress="handleMentorInputKeyPress(event, ${p.id}, ${currentStep.id})">
                                <button class="btn btn-primary rounded-end-2 px-4 fw-bold" onclick="askMentorQuestion(${p.id}, ${currentStep.id})">
                                    <i class="bi bi-send-fill me-1"></i> Ask
                                </button>
                            </div>
                        </div>
                    ` : '<div class="alert alert-info">Select a step from the left timeline checklist.</div>'}
                </div>
            </div>
        `;

    } catch (err) {
        console.error("Failed to load workspace", err);
        container.innerHTML = `<div class="alert alert-danger">Failed to load project workspace.</div>`;
    }
}

function selectWorkspaceStep(projectId, stepIndex) {
    if (currentProjectData) {
        currentProjectData.current_step_index = stepIndex;
        openWorkspace(projectId);
    }
}

// ---------------------------------------------------------
// AI MENTOR Q&A HANDLERS
// ---------------------------------------------------------
function sendQuickMentorPrompt(promptText) {
    document.getElementById("mentor-question-input").value = promptText;
    const currentStep = currentProjectData.steps[currentProjectData.current_step_index];
    askMentorQuestion(currentProjectId, currentStep.id);
}

function handleMentorInputKeyPress(e, projectId, stepId) {
    if (e.key === 'Enter') {
        askMentorQuestion(projectId, stepId);
    }
}

async function askMentorQuestion(projectId, stepId) {
    const input = document.getElementById("mentor-question-input");
    const question = input.value.trim();
    if (!question) return;

    const logContainer = document.getElementById("mentor-qa-log");
    logContainer.innerHTML += `
        <div class="qa-card">
            <div class="qa-card-user"><i class="bi bi-person-fill text-primary me-1"></i> "${question}"</div>
            <div class="qa-card-response text-muted"><div class="spinner-border spinner-border-sm text-primary me-2"></div>Thinking...</div>
        </div>
    `;
    input.value = "";

    try {
        const res = await fetch(`/api/projects/${projectId}/mentor/ask`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ step_id: stepId, question })
        });

        const data = await res.json();
        openWorkspace(projectId);

    } catch (err) {
        console.error("Failed to ask mentor question", err);
    }
}

// ---------------------------------------------------------
// PHOTO PROTOTYPE INSPECTION
// ---------------------------------------------------------
function openPhotoModal() {
    uploadedPhotoBase64 = null;
    document.getElementById("photo-file-input").value = "";
    document.getElementById("photo-preview-container").classList.add("d-none");
    document.getElementById("photo-analysis-result").classList.add("d-none");
    document.getElementById("btn-analyze-photo").disabled = true;

    const modal = new bootstrap.Modal(document.getElementById("photoUploadModal"));
    modal.show();
}

function previewUploadPhoto(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function(e) {
        const base64Data = e.target.result.split(',')[1];
        uploadedPhotoBase64 = base64Data;

        const img = document.getElementById("photo-preview-img");
        img.src = e.target.result;

        document.getElementById("photo-preview-container").classList.remove("d-none");
        document.getElementById("btn-analyze-photo").disabled = false;
    };
    reader.readAsDataURL(file);
}

async function analyzePrototypePhoto() {
    if (!uploadedPhotoBase64 || !currentProjectId) return;

    const resultBox = document.getElementById("photo-analysis-result");
    resultBox.classList.remove("d-none");
    resultBox.innerHTML = `<div class="text-center py-3"><div class="spinner-border text-primary me-2"></div>Inspecting wiring and components...</div>`;

    try {
        const res = await fetch(`/api/projects/${currentProjectId}/upload_photo`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ image_base64: uploadedPhotoBase64 })
        });

        const data = await res.json();
        resultBox.innerHTML = `
            <div class="p-3 bg-light border rounded-3 mt-3">
                <h6 class="fw-bold text-primary mb-2"><i class="bi bi-camera-fill me-1"></i> Inspection Results:</h6>
                <div class="text-dark small whitespace-pre-line">${data.inspection}</div>
            </div>
        `;
    } catch (err) {
        console.error("Failed to analyze photo", err);
        resultBox.innerHTML = `<div class="alert alert-danger">Failed to analyze photo.</div>`;
    }
}

// ---------------------------------------------------------
// TEST RESULT CHECKPOINT HANDLER
// ---------------------------------------------------------
async function submitTestResult(projectId, stepId, result) {
    try {
        const res = await fetch(`/api/projects/${projectId}/steps/${stepId}/test`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ result })
        });

        const data = await res.json();

        if (result === 'passed') {
            if (data.project_stage === 'Completed Prototype') {
                alert("🎉 CONGRATULATIONS! Prototype fully completed and verified!");
                openWorkspace(projectId);
            } else {
                openWorkspace(projectId);
            }
        } else {
            renderTroubleshootingSession(data.troubleshooting_session);
        }
    } catch (err) {
        console.error("Failed to submit test result", err);
    }
}

// ---------------------------------------------------------
// RULE-BASED & HYBRID TROUBLESHOOTING ENGINE UI
// ---------------------------------------------------------
async function startTroubleshooting(projectId) {
    currentProjectId = projectId;
    showView('troubleshooting');
    const container = document.getElementById("troubleshooting-container");
    container.innerHTML = `<div class="text-center py-5"><div class="spinner-border text-danger"></div></div>`;

    try {
        const res = await fetch(`/api/projects/${projectId}/troubleshoot/start`, { method: "POST" });
        const sessionData = await res.json();
        renderTroubleshootingSession(sessionData);
    } catch (err) {
        console.error("Failed to start troubleshooting session", err);
    }
}

function renderTroubleshootingSession(sessionData) {
    showView('troubleshooting');
    const container = document.getElementById("troubleshooting-container");

    const node = sessionData.current_node;
    const history = sessionData.history || [];
    const isTerminal = node.is_terminal || false;

    if (isTerminal) {
        const isSuccess = node.status === 'resolved';

        container.innerHTML = `
            <div class="card border-0 shadow-sm rounded-3 overflow-hidden">
                <div class="${isSuccess ? 'bg-success' : 'bg-warning text-dark'} text-white p-4 text-center">
                    <i class="bi ${isSuccess ? 'bi-check-circle-fill' : 'bi-exclamation-triangle-fill'} display-3 mb-2"></i>
                    <h3 class="fw-bold mb-1">${node.title}</h3>
                    <p class="mb-0 opacity-90 font-monospace">Diagnostic Sequence Completed</p>
                </div>
                <div class="card-body p-4 p-md-5">
                    <div class="p-4 bg-light border rounded-3 mb-4">
                        <h5 class="fw-bold text-dark mb-2"><i class="bi bi-tools me-2 text-primary"></i> Action Instruction:</h5>
                        <p class="fs-5 text-dark mb-0">${node.action}</p>
                    </div>

                    ${node.recommendation ? `
                        <p class="text-muted mb-4"><i class="bi bi-info-circle me-1"></i> ${node.recommendation}</p>
                    ` : ''}

                    <div class="d-flex justify-content-center">
                        <button class="btn btn-primary btn-lg rounded-2 fw-bold px-4" onclick="openWorkspace(${sessionData.project_id})">
                            <i class="bi bi-arrow-left-circle me-2"></i> Return to Workspace & Re-Test
                        </button>
                    </div>
                </div>
            </div>
        `;
        return;
    }

    container.innerHTML = `
        <div class="card border-0 shadow-sm rounded-3 overflow-hidden">
            <div class="troubleshoot-header d-flex justify-content-between align-items-center">
                <div>
                    <span class="badge bg-danger font-monospace px-3 py-1 mb-1">HYBRID HARDWARE DIAGNOSTICS</span>
                    <h4 class="fw-bold m-0 text-white">${sessionData.tree_title || 'Hardware Diagnostic Flow'}</h4>
                </div>
                <button class="btn btn-sm btn-outline-light rounded-2" onclick="openWorkspace(${sessionData.project_id})">Cancel</button>
            </div>

            <div class="card-body p-4 p-md-5">
                ${history.length > 0 ? `
                    <div class="mb-4">
                        <small class="text-muted font-monospace fw-bold d-block mb-2">DIAGNOSTIC HISTORY LOG:</small>
                        <div class="d-flex flex-column gap-1">
                            ${history.map(h => `
                                <div class="p-2 bg-light rounded-2 border-start border-3 border-secondary small">
                                    <div class="fw-bold text-dark">${h.question}</div>
                                    <div class="text-secondary font-monospace">Answer: "${h.selected_answer}"</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}

                <div class="diagnostic-question-box mb-4">
                    <h4 class="fw-bold text-dark mb-2">${node.question}</h4>
                    <p class="text-muted small mb-0"><i class="bi bi-info-circle me-1"></i> ${node.why}</p>
                </div>

                <small class="text-muted font-monospace fw-bold d-block mb-2">SELECT YOUR ANSWER:</small>
                <div class="d-grid gap-3">
                    ${node.options.map((opt, idx) => `
                        <button class="btn ${opt.is_issue ? 'diag-option-no' : 'diag-option-yes'} diag-option-btn d-flex justify-content-between align-items-center" onclick="submitTroubleshootingStep(${sessionData.project_id}, ${idx})">
                            <span>${opt.text}</span>
                            <i class="bi bi-chevron-right"></i>
                        </button>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
}

async function submitTroubleshootingStep(projectId, optionIndex) {
    try {
        const res = await fetch(`/api/projects/${projectId}/troubleshoot/step`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ option_index: optionIndex })
        });

        const sessionData = await res.json();
        renderTroubleshootingSession(sessionData);
    } catch (err) {
        console.error("Failed to process troubleshooting step", err);
    }
}

// ---------------------------------------------------------
// REAL PRODUCT ANALYTICS VIEW
// ---------------------------------------------------------
async function loadAnalyticsView() {
    showView('analytics');
    const container = document.getElementById("analytics-content");
    container.innerHTML = `<div class="text-center py-5"><div class="spinner-border text-primary"></div></div>`;

    try {
        const res = await fetch("/api/analytics");
        const a = await res.json();

        container.innerHTML = `
            <div class="row g-4 mb-4">
                <div class="col-md-3">
                    <div class="stat-card">
                        <small class="text-muted font-monospace d-block mb-1">TOTAL PROJECTS</small>
                        <div class="stat-num">${a.total_projects}</div>
                        <small class="text-secondary">${a.active_projects} Active | ${a.completed_projects} Completed</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card">
                        <small class="text-muted font-monospace d-block mb-1">STEPS VERIFIED</small>
                        <div class="stat-num text-success">${a.total_steps_completed}</div>
                        <small class="text-secondary">Passed Checkpoints</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card">
                        <small class="text-muted font-monospace d-block mb-1">DIAGNOSTIC SESSIONS</small>
                        <div class="stat-num text-warning">${a.troubleshooting_sessions_count}</div>
                        <small class="text-secondary">Hardware Troubleshoots</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card">
                        <small class="text-muted font-monospace d-block mb-1">AI MENTOR REQUESTS</small>
                        <div class="stat-num text-info">${a.ai_requests_count + a.ai_fallback_count}</div>
                        <small class="text-secondary">${a.ai_requests_count} Live AI | ${a.ai_fallback_count} Fallbacks</small>
                    </div>
                </div>
            </div>

            <div class="card border-0 shadow-sm rounded-3">
                <div class="card-header bg-white border-bottom p-3">
                    <h6 class="fw-bold m-0 font-monospace text-dark"><i class="bi bi-clock-history me-2"></i> REAL PRODUCT ACTIVITY LOG (SQLITE PERSISTED)</h6>
                </div>
                <div class="card-body p-0">
                    <div class="table-responsive">
                        <table class="table table-hover mb-0 small">
                            <thead class="table-light">
                                <tr>
                                    <th>Event Type</th>
                                    <th>Project ID</th>
                                    <th>Details</th>
                                    <th>Timestamp</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${a.recent_events && a.recent_events.length > 0 ? 
                                    a.recent_events.map(e => `
                                        <tr>
                                            <td><span class="badge bg-secondary-subtle text-dark font-monospace">${e.event_type}</span></td>
                                            <td>${e.project_id || '-'}</td>
                                            <td class="font-monospace">${e.details_json || '{}'}</td>
                                            <td>${e.timestamp}</td>
                                        </tr>
                                    `).join('') : '<tr><td colspan="4" class="text-center text-muted py-3">No activity logged yet.</td></tr>'
                                }
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;

    } catch (err) {
        console.error("Failed to load analytics", err);
        container.innerHTML = `<div class="alert alert-danger">Failed to load analytics metrics.</div>`;
    }
}

// ---------------------------------------------------------
// COMPONENT LIBRARY VIEW
// ---------------------------------------------------------
async function fetchComponentsList() {
    try {
        const res = await fetch("/api/components");
        allComponentsData = await res.json();
    } catch (err) {
        console.error("Failed to fetch components list", err);
    }
}

function loadComponentsView() {
    filterComponents();
}

function filterComponents() {
    const search = (document.getElementById("component-search")?.value || "").toLowerCase();
    const container = document.getElementById("components-grid");

    const filtered = allComponentsData.filter(c => 
        c.name.toLowerCase().includes(search) ||
        c.type.toLowerCase().includes(search) ||
        c.protocol.toLowerCase().includes(search)
    );

    if (filtered.length === 0) {
        container.innerHTML = `<div class="col-12 text-center py-5 text-muted">No verified components match your search.</div>`;
        return;
    }

    container.innerHTML = filtered.map(c => `
        <div class="col-md-6 col-lg-4">
            <div class="card h-100 border-0 shadow-sm rounded-3 overflow-hidden">
                <div class="card-body p-4 d-flex flex-column">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <span class="badge bg-primary-subtle text-primary font-monospace">${c.type}</span>
                        <span class="badge bg-light text-dark font-monospace border">${c.voltage}</span>
                    </div>
                    <h4 class="fw-bold mb-1 text-dark">${c.name}</h4>
                    <p class="text-muted small mb-3 flex-grow-1">${c.description}</p>

                    <div class="bg-light p-2 rounded-2 mb-3 font-monospace small">
                        <div class="text-secondary fw-bold">PINS:</div>
                        <div class="text-truncate text-dark">${c.common_pins}</div>
                    </div>

                    <button class="btn btn-outline-primary rounded-2 btn-sm fw-semibold mt-auto" onclick="openComponentModal(${c.id})">
                        View Hardware Specs
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

function openComponentModal(compId) {
    const c = allComponentsData.find(x => x.id === compId);
    if (!c) return;

    document.getElementById("modal-comp-name").textContent = c.name;
    document.getElementById("modal-comp-body").innerHTML = `
        <div class="row g-3 mb-4">
            <div class="col-md-6">
                <small class="text-muted d-block font-monospace">TYPE</small>
                <span class="fw-bold fs-6 text-dark">${c.type}</span>
            </div>
            <div class="col-md-6">
                <small class="text-muted d-block font-monospace">OPERATING VOLTAGE</small>
                <span class="fw-bold fs-6 text-primary">${c.voltage}</span>
            </div>
            <div class="col-md-6">
                <small class="text-muted d-block font-monospace">COMMUNICATION PROTOCOL</small>
                <span class="fw-bold fs-6 text-success">${c.protocol}</span>
            </div>
            <div class="col-md-6">
                <small class="text-muted d-block font-monospace">COMMON PINS</small>
                <span class="fw-bold fs-6 font-monospace">${c.common_pins}</span>
            </div>
        </div>

        <div class="p-3 bg-warning-subtle rounded-2 border-start border-4 border-warning">
            <h6 class="fw-bold text-dark mb-1"><i class="bi bi-exclamation-triangle-fill text-warning me-2"></i> Common Problems & Pitfalls:</h6>
            <p class="mb-0 small text-dark">${c.common_problems}</p>
        </div>
    `;

    const modal = new bootstrap.Modal(document.getElementById('componentModal'));
    modal.show();
}
