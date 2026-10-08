"""
Flask Backend Application for Innovation Copilot.
Integrates Provider-Agnostic AI Service Layer (Gemini API + Fallback Mode),
Contextual Engineering Mentor Q&A, Photo Prototype Inspection, and Real Product Analytics.
"""

from flask import Flask, render_template, request, jsonify
import json
import sqlite3
import base64
from database import get_db_connection, init_db, log_analytics_event
from ai_service import AIService
from troubleshooting_engine import RuleBasedTroubleshootingEngine, TROUBLESHOOTING_TREES
from build_guide_engine import generate_5stage_build_plan

app = Flask(__name__)

# Ensure DB schema is initialized on app startup
init_db()

@app.route("/")
def index():
    """Serves the main single-page engineering workspace."""
    return render_template("index.html")

# ---------------------------------------------------------
# COMPONENT LIBRARY API
# ---------------------------------------------------------
@app.route("/api/components", methods=["GET"])
def get_components():
    """Returns verified electronics reference components database."""
    conn = get_db_connection()
    components = conn.execute("SELECT * FROM components ORDER BY name ASC").fetchall()
    conn.close()
    return jsonify([dict(c) for c in components])

# ---------------------------------------------------------
# PROJECT MANAGEMENT & AI SCOPING API
# ---------------------------------------------------------
@app.route("/api/projects", methods=["GET"])
def get_projects():
    """Returns all projects with component summaries, progress metrics, and AI status."""
    conn = get_db_connection()
    projects = conn.execute("SELECT * FROM projects ORDER BY updated_at DESC").fetchall()
    result = []

    for p in projects:
        p_dict = dict(p)

        comps = conn.execute("""
            SELECT pc.custom_name, c.name AS library_name, c.voltage, c.type
            FROM project_components pc
            LEFT JOIN components c ON pc.component_id = c.id
            WHERE pc.project_id = ?
        """, (p['id'],)).fetchall()
        p_dict['custom_components'] = [dict(c) for c in comps]

        steps = conn.execute("SELECT status FROM build_steps WHERE project_id = ?", (p['id'],)).fetchall()
        total_steps = len(steps)
        completed_steps = sum(1 for s in steps if s['status'] == 'passed')
        p_dict['total_steps'] = total_steps
        p_dict['completed_steps'] = completed_steps
        p_dict['progress_percent'] = int((completed_steps / total_steps * 100)) if total_steps > 0 else 0
        
        result.append(p_dict)

    conn.close()
    return jsonify(result)

@app.route("/api/projects/<int:project_id>", methods=["GET"])
def get_project_detail(project_id):
    """Returns detailed project record, custom components, build steps, Q&A history, and active troubleshooting."""
    conn = get_db_connection()
    p = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not p:
        conn.close()
        return jsonify({"error": "Project not found"}), 404

    p_dict = dict(p)

    # Decode JSON fields if present
    try:
        p_dict['ai_plan'] = json.loads(p['ai_plan_json']) if p['ai_plan_json'] else None
    except Exception:
        p_dict['ai_plan'] = None

    try:
        p_dict['ai_component_analysis'] = json.loads(p['ai_component_analysis_json']) if p['ai_component_analysis_json'] else None
    except Exception:
        p_dict['ai_component_analysis'] = None

    # Fetch custom components
    comps = conn.execute("""
        SELECT pc.custom_name, c.name AS library_name, c.voltage, c.type, c.common_pins, c.common_problems,
               (CASE WHEN c.id IS NOT NULL THEN 1 ELSE 0 END) AS is_verified
        FROM project_components pc
        LEFT JOIN components c ON pc.component_id = c.id
        WHERE pc.project_id = ?
    """, (project_id,)).fetchall()
    p_dict['custom_components'] = [dict(c) for c in comps]

    # Fetch build steps
    steps = conn.execute("SELECT * FROM build_steps WHERE project_id = ? ORDER BY step_number ASC", (project_id,)).fetchall()
    p_dict['steps'] = [dict(s) for s in steps]

    total_steps = len(steps)
    completed_steps = sum(1 for s in steps if s['status'] == 'passed')
    p_dict['total_steps'] = total_steps
    p_dict['completed_steps'] = completed_steps
    p_dict['progress_percent'] = int((completed_steps / total_steps * 100)) if total_steps > 0 else 0

    # Fetch active troubleshooting session
    session = conn.execute("""
        SELECT * FROM troubleshooting_sessions 
        WHERE project_id = ? AND status = 'in_progress' 
        ORDER BY id DESC LIMIT 1
    """, (project_id,)).fetchone()
    p_dict['active_troubleshooting'] = dict(session) if session else None

    # Fetch AI Mentor Q&A History
    ai_msgs = conn.execute("SELECT * FROM ai_messages WHERE project_id = ? ORDER BY id ASC", (project_id,)).fetchall()
    p_dict['ai_messages'] = [dict(m) for m in ai_msgs]

    p_dict['ai_available'] = AIService.is_ai_available()

    conn.close()
    return jsonify(p_dict)

@app.route("/api/projects", methods=["POST"])
def create_project():
    """
    Creates a new project. Invokes AI Project Planner & Component Advisor if API key available,
    or falls back gracefully to deterministic rule generation.
    """
    data = request.json
    name = data.get("name")
    goal = data.get("goal")
    microcontroller = data.get("microcontroller", "ESP32")
    custom_component_list = data.get("custom_components", [])
    current_problem = data.get("current_problem", "")

    if not name or not goal:
        return jsonify({"error": "Project name and goal are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Generate AI Plan & Component Analysis (or fallback)
    ai_plan = AIService.generate_project_plan(name, goal, microcontroller, custom_component_list)
    ai_analysis = AIService.analyze_components(custom_component_list)

    estimated_diff = ai_plan.get("estimated_difficulty", "Intermediate")

    cursor.execute("""
        INSERT INTO projects (name, goal, microcontroller, current_stage, current_step_index, status, current_problem, estimated_difficulty, ai_plan_json, ai_component_analysis_json)
        VALUES (?, ?, ?, 'Preparation', 0, 'in_progress', ?, ?, ?, ?)
    """, (name, goal, microcontroller, current_problem, estimated_diff, json.dumps(ai_plan), json.dumps(ai_analysis)))
    
    project_id = cursor.lastrowid

    # Store project components
    verified_comps = conn.execute("SELECT id, name FROM components").fetchall()
    verified_map = {c['name'].lower(): c['id'] for c in verified_comps}

    typed_strings = []
    for raw_name in custom_component_list:
        comp_str = str(raw_name).strip()
        if not comp_str:
            continue
        typed_strings.append(comp_str)

        matched_id = None
        for v_name, v_id in verified_map.items():
            if v_name in comp_str.lower() or comp_str.lower() in v_name:
                matched_id = v_id
                break

        cursor.execute("""
            INSERT INTO project_components (project_id, component_id, custom_name)
            VALUES (?, ?, ?)
        """, (project_id, matched_id, comp_str))

    # Populate build steps from AI plan or fallback
    steps = ai_plan.get("steps", [])
    for idx, s in enumerate(steps, start=1):
        step_num = s.get("step_number", idx)
        category = s.get("category", "Assembly")
        title = s.get("title", f"Step {step_num}")
        instruction = s.get("instruction", "")
        why_matters = s.get("why_matters", "")
        req_comps = s.get("required_components", ", ".join(typed_strings))
        warning_note = s.get("warning_note", "")
        test_question = s.get("test_question", "Did this step complete successfully?")

        cursor.execute("""
            INSERT INTO build_steps (project_id, step_number, category, title, instruction, why_matters, required_components, warning_note, test_question, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        """, (project_id, step_num, category, title, instruction, why_matters, req_comps, warning_note, test_question))

    conn.commit()
    conn.close()

    # Log real analytics
    log_analytics_event("project_created", project_id, {
        "name": name,
        "mcu": microcontroller,
        "ai_used": ai_plan.get("ai_available", False),
        "components_count": len(typed_strings)
    })

    return jsonify({"message": "Project created successfully", "project_id": project_id, "ai_available": ai_plan.get("ai_available", False)}), 201

# ---------------------------------------------------------
# CONTEXTUAL AI ENGINEERING MENTOR Q&A API
# ---------------------------------------------------------
@app.route("/api/projects/<int:project_id>/mentor/ask", methods=["POST"])
def ask_engineering_mentor(project_id):
    """
    Handles contextual Engineering Mentor questions from student inside workspace build steps.
    Sends relevant project memory context to AI Service or returns fallback answer.
    """
    data = request.json
    step_id = data.get("step_id")
    user_question = data.get("question")

    if not user_question:
        return jsonify({"error": "Question is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    p = cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not p:
        conn.close()
        return jsonify({"error": "Project not found"}), 404

    # Fetch custom components
    comps = cursor.execute("SELECT custom_name FROM project_components WHERE project_id = ?", (project_id,)).fetchall()
    project_context = dict(p)
    project_context['custom_components'] = [dict(c) for c in comps]

    # Fetch current step context
    step_context = {}
    if step_id:
        step_row = cursor.execute("SELECT * FROM build_steps WHERE id = ?", (step_id,)).fetchone()
        if step_row:
            step_context = dict(step_row)

    # Call AI Mentor Service
    mentor_res = AIService.explain_build_step(project_context, step_context, user_question)
    ai_response = mentor_res.get("answer", "No answer available.")

    # Save to ai_messages Q&A history log
    cursor.execute("""
        INSERT INTO ai_messages (project_id, step_id, user_question, ai_response)
        VALUES (?, ?, ?, ?)
    """, (project_id, step_id, user_question, ai_response))
    conn.commit()

    # Log analytics
    log_analytics_event(
        "ai_request" if mentor_res.get("ai_available") else "ai_fallback",
        project_id,
        {"question": user_question, "step_id": step_id}
    )

    conn.close()

    return jsonify({
        "question": user_question,
        "response": ai_response,
        "ai_available": mentor_res.get("ai_available", False)
    })

# ---------------------------------------------------------
# BUILD STEPS & CHECKPOINT TESTING
# ---------------------------------------------------------
@app.route("/api/projects/<int:project_id>/steps/<int:step_id>/test", methods=["POST"])
def record_test_result(project_id, step_id):
    """Evaluates checkpoint result, updates progress, and initiates troubleshooting if failed."""
    data = request.json
    result = data.get("result") # 'passed' or 'failed'
    notes = data.get("notes", "")

    if result not in ['passed', 'failed']:
        return jsonify({"error": "Invalid result status"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE build_steps SET status = ? WHERE id = ? AND project_id = ?", (result, step_id, project_id))
    cursor.execute("INSERT INTO test_results (project_id, step_id, result, notes) VALUES (?, ?, ?, ?)",
                   (project_id, step_id, result, notes))

    if result == 'passed':
        steps = cursor.execute("SELECT * FROM build_steps WHERE project_id = ? ORDER BY step_number ASC", (project_id,)).fetchall()
        step_index = 0
        for idx, s in enumerate(steps):
            if s['id'] == step_id:
                step_index = idx + 1
                break

        if step_index >= len(steps):
            new_stage = "Completed Prototype"
            status = "completed"
            log_analytics_event("project_completed", project_id, {"completed_steps": len(steps)})
        else:
            new_stage = steps[step_index]['category']
            status = "in_progress"
            log_analytics_event("step_completed", project_id, {"step_id": step_id, "step_index": step_index})

        cursor.execute("""
            UPDATE projects SET current_step_index = ?, current_stage = ?, status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (step_index, new_stage, status, project_id))

        conn.commit()
        conn.close()

        return jsonify({
            "status": "passed",
            "message": "Step verified successfully!",
            "next_step_index": step_index,
            "project_stage": new_stage
        })

    else: # Checkpoint failed -> Start Troubleshooting
        log_analytics_event("troubleshooting_started", project_id, {"step_id": step_id})

        cursor.execute("UPDATE projects SET current_stage = 'Troubleshooting', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (project_id,))

        comps = cursor.execute("SELECT custom_name FROM project_components WHERE project_id = ?", (project_id,)).fetchall()
        comp_names = [c['custom_name'] for c in comps]

        tree_key = RuleBasedTroubleshootingEngine.get_tree_key(comp_names)
        session_data = RuleBasedTroubleshootingEngine.start_session(project_id, step_id, tree_key)

        cursor.execute("""
            INSERT INTO troubleshooting_sessions (project_id, step_id, current_node_id, history_json, status)
            VALUES (?, ?, ?, ?, 'in_progress')
        """, (project_id, step_id, session_data['current_node_id'], json.dumps(session_data['history'])))

        session_id = cursor.lastrowid
        session_data['session_id'] = session_id

        conn.commit()
        conn.close()

        return jsonify({
            "status": "failed",
            "message": "Checkpoint failed. Diagnostic sequence started.",
            "troubleshooting_session": session_data
        })

# ---------------------------------------------------------
# TROUBLESHOOTING & PHOTO INSPECTION API
# ---------------------------------------------------------
@app.route("/api/projects/<int:project_id>/troubleshoot/start", methods=["POST"])
def start_troubleshooting(project_id):
    """Starts or resets a troubleshooting flow for a project."""
    conn = get_db_connection()
    cursor = conn.cursor()

    p = cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not p:
        conn.close()
        return jsonify({"error": "Project not found"}), 404

    steps = cursor.execute("SELECT id FROM build_steps WHERE project_id = ? ORDER BY step_number ASC", (project_id,)).fetchall()
    step_id = steps[0]['id'] if steps else 0

    comps = cursor.execute("SELECT custom_name FROM project_components WHERE project_id = ?", (project_id,)).fetchall()
    comp_names = [c['custom_name'] for c in comps]

    tree_key = RuleBasedTroubleshootingEngine.get_tree_key(comp_names, p['current_problem'] or "")
    session_data = RuleBasedTroubleshootingEngine.start_session(project_id, step_id, tree_key)

    cursor.execute("UPDATE troubleshooting_sessions SET status = 'cancelled' WHERE project_id = ? AND status = 'in_progress'", (project_id,))

    cursor.execute("""
        INSERT INTO troubleshooting_sessions (project_id, step_id, current_node_id, history_json, status)
        VALUES (?, ?, ?, ?, 'in_progress')
    """, (project_id, step_id, session_data['current_node_id'], json.dumps(session_data['history'])))

    session_data['session_id'] = cursor.lastrowid
    cursor.execute("UPDATE projects SET current_stage = 'Troubleshooting' WHERE id = ?", (project_id,))

    conn.commit()
    conn.close()

    return jsonify(session_data)

@app.route("/api/projects/<int:project_id>/troubleshoot/step", methods=["POST"])
def process_troubleshooting_step(project_id):
    """Advances diagnostic state machine."""
    data = request.json
    option_index = data.get("option_index")

    if option_index is None:
        return jsonify({"error": "option_index is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    session = cursor.execute("""
        SELECT * FROM troubleshooting_sessions 
        WHERE project_id = ? AND status = 'in_progress' 
        ORDER BY id DESC LIMIT 1
    """, (project_id,)).fetchone()

    if not session:
        conn.close()
        return jsonify({"error": "No active troubleshooting session"}), 404

    history = json.loads(session['history_json'])
    comps = cursor.execute("SELECT custom_name FROM project_components WHERE project_id = ?", (project_id,)).fetchall()
    comp_names = [c['custom_name'] for c in comps]

    tree_key = RuleBasedTroubleshootingEngine.get_tree_key(comp_names)
    result = RuleBasedTroubleshootingEngine.process_answer(
        tree_key, session['current_node_id'], option_index, history
    )

    if not result:
        conn.close()
        return jsonify({"error": "Invalid option selection"}), 400

    new_status = result['status']
    cursor.execute("""
        UPDATE troubleshooting_sessions 
        SET current_node_id = ?, history_json = ?, status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (result['current_node_id'], json.dumps(result['history']), new_status, session['id']))

    if result['is_terminal'] and result['status'] == 'resolved':
        current_step = cursor.execute("SELECT category FROM build_steps WHERE id = ?", (session['step_id'],)).fetchone()
        cat = current_step['category'] if current_step else 'Wiring'
        cursor.execute("UPDATE projects SET current_stage = ? WHERE id = ?", (cat, project_id))
        cursor.execute("UPDATE build_steps SET status = 'passed' WHERE id = ?", (session['step_id'],))

    conn.commit()
    conn.close()

    result['session_id'] = session['id']
    return jsonify(result)

@app.route("/api/projects/<int:project_id>/upload_photo", methods=["POST"])
def upload_prototype_photo(project_id):
    """Processes uploaded prototype photo for vision inspection or returns fallback check guidance."""
    data = request.json or {}
    image_base64 = data.get("image_base64")

    conn = get_db_connection()
    p = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not p:
        conn.close()
        return jsonify({"error": "Project not found"}), 404

    comps = conn.execute("SELECT custom_name FROM project_components WHERE project_id = ?", (project_id,)).fetchall()
    project_context = dict(p)
    project_context['custom_components'] = [dict(c) for c in comps]
    conn.close()

    # Call AI Vision Service
    inspection_res = AIService.inspect_prototype_image(image_base64, project_context)

    log_analytics_event("photo_uploaded", project_id, {"ai_used": inspection_res.get("ai_available", False)})

    return jsonify(inspection_res)

# ---------------------------------------------------------
# REAL ANALYTICS API
# ---------------------------------------------------------
@app.route("/api/analytics", methods=["GET"])
def get_real_analytics():
    """Returns real product usage analytics from SQLite database."""
    conn = get_db_connection()

    total_projects = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
    completed_projects = conn.execute("SELECT COUNT(*) FROM projects WHERE status = 'completed'").fetchone()[0]
    active_projects = total_projects - completed_projects

    total_steps_completed = conn.execute("SELECT COUNT(*) FROM test_results WHERE result = 'passed'").fetchone()[0]
    troubleshooting_sessions_count = conn.execute("SELECT COUNT(*) FROM troubleshooting_sessions").fetchone()[0]

    ai_requests_count = conn.execute("SELECT COUNT(*) FROM analytics WHERE event_type = 'ai_request'").fetchone()[0]
    ai_fallback_count = conn.execute("SELECT COUNT(*) FROM analytics WHERE event_type = 'ai_fallback'").fetchone()[0]

    recent_events = conn.execute("SELECT * FROM analytics ORDER BY timestamp DESC LIMIT 10").fetchall()

    conn.close()

    return jsonify({
        "total_projects": total_projects,
        "active_projects": active_projects,
        "completed_projects": completed_projects,
        "total_steps_completed": total_steps_completed,
        "troubleshooting_sessions_count": troubleshooting_sessions_count,
        "ai_requests_count": ai_requests_count,
        "ai_fallback_count": ai_fallback_count,
        "recent_events": [dict(e) for e in recent_events]
    })

# ---------------------------------------------------------
# DEMO RESET ROUTE
# ---------------------------------------------------------
@app.route("/api/demo/reset", methods=["POST"])
def reset_demo():
    """Resets the 'ESP32 OLED Display' demo project back to initial step 1 state."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM projects WHERE name = 'ESP32 OLED Display'")
    row = cursor.fetchone()

    if row:
        demo_id = row['id']
        cursor.execute("""
            UPDATE projects SET current_stage = 'Preparation', current_step_index = 0, status = 'in_progress', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (demo_id,))
        cursor.execute("UPDATE build_steps SET status = 'pending' WHERE project_id = ?", (demo_id,))
        cursor.execute("DELETE FROM test_results WHERE project_id = ?", (demo_id,))
        cursor.execute("DELETE FROM troubleshooting_sessions WHERE project_id = ?", (demo_id,))
        cursor.execute("DELETE FROM ai_messages WHERE project_id = ?", (demo_id,))

        conn.commit()
        conn.close()
        return jsonify({"message": "Demo project reset successfully", "project_id": demo_id})
    else:
        conn.close()
        init_db()
        return jsonify({"message": "Demo project initialized"}), 200

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
