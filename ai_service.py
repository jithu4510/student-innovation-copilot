"""
Provider-Agnostic AI Service Layer for Innovation Copilot.
Handles AI Project Scoping, Structured Build Planning, Contextual Step Mentoring,
Hybrid Troubleshooting, Vision-based Photo Inspection, and Hardware Verification.
Supports Gemini API (or OpenAI/custom) with seamless deterministic Fallback Mode.
"""

import os
import json
import urllib.request
import urllib.error

class AIService:
    @staticmethod
    def get_api_key():
        """Retrieves Gemini or OpenAI API key from environment variables."""
        return os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY")

    @classmethod
    def is_ai_available(cls):
        """Checks if a valid AI API key is configured."""
        key = cls.get_api_key()
        return bool(key and len(key.strip()) > 5)

    @classmethod
    def _call_gemini_api(cls, prompt, image_base64=None, system_instruction=None, json_response=False):
        """
        Executes HTTP REST call to Google Gemini API using urllib.
        Returns parsed JSON or raw text. Returns None if API key missing or request fails.
        """
        api_key = cls.get_api_key()
        if not api_key:
            return None

        # Model endpoint
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

        contents = []
        parts = []

        if prompt:
            parts.append({"text": prompt})

        if image_base64:
            parts.append({
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": image_base64
                }
            })

        contents.append({"parts": parts})

        payload = {"contents": contents}

        if system_instruction:
            payload["system_instruction"] = {
                "parts": [{"text": system_instruction}]
            }

        if json_response:
            payload["generationConfig"] = {
                "response_mime_type": "application/json"
            }

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=12) as response:
                res_body = json.loads(response.read().decode("utf-8"))
                candidates = res_body.get("candidates", [])
                if candidates:
                    text_out = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    if json_response:
                        try:
                            return json.loads(text_out)
                        except Exception:
                            return text_out
                    return text_out
        except Exception as e:
            print(f"[AIService Warning] Gemini API call failed: {e}")
            return None

        return None

    @classmethod
    def generate_project_plan(cls, name, goal, microcontroller, custom_components):
        """
        Generates a structured project plan with AI or falls back to rule-based 5-stage plan.
        Returns dict with project_summary, difficulty, risks, required/optional components, and phases/steps.
        """
        system_instruction = (
            "You are an expert electronics and robotics engineering mentor for students aged 13-18. "
            "Generate realistic, encouraging, and technically accurate project scope and build plans. "
            "Never invent false electrical specifications. Respond strictly in JSON."
        )

        prompt = f"""
        Project Name: {name}
        Project Goal: {goal}
        Microcontroller: {microcontroller}
        Components Provided by Student: {', '.join(custom_components)}

        Generate a JSON object with this exact structure:
        {{
            "project_summary": "Short 2-sentence engineering summary of project architecture",
            "estimated_difficulty": "Beginner | Intermediate | Advanced",
            "potential_risks": ["Risk 1 e.g. voltage limits", "Risk 2 e.g. noise"],
            "required_components": ["comp 1", "comp 2"],
            "optional_components": ["comp 1"],
            "phases": [
                {{
                    "phase_number": 1,
                    "name": "Phase 1: Hardware Preparation",
                    "description": "Short description"
                }}
            ],
            "steps": [
                {{
                    "step_number": 1,
                    "category": "Preparation",
                    "title": "Short title",
                    "instruction": "Detailed clear instruction for student",
                    "why_matters": "Educational rationale",
                    "required_components": "Component names needed",
                    "warning_note": "Safety or voltage warning",
                    "test_question": "Verification question for student"
                }}
            ]
        }}
        """

        res = cls._call_gemini_api(prompt, system_instruction=system_instruction, json_response=True)
        if isinstance(res, dict) and "steps" in res:
            res["ai_available"] = True
            return res

        # Fallback to Rule-based generator
        from build_guide_engine import generate_5stage_build_plan
        fallback_steps = generate_5stage_build_plan(microcontroller, custom_components)

        return {
            "ai_available": False,
            "project_summary": f"Guided prototype build plan for {name} using {microcontroller}.",
            "estimated_difficulty": "Intermediate",
            "potential_risks": [
                f"Verify power supply logic voltage ({microcontroller} operates at 3.3V or 5V).",
                "Disconnect USB power before making physical wiring adjustments."
            ],
            "required_components": custom_components,
            "optional_components": ["Breadboard Power Module", "Multimeter"],
            "phases": [
                {"phase_number": 1, "name": "Preparation", "description": "Inventory & pinout inspection"},
                {"phase_number": 2, "name": "Assembly", "description": "Breadboard hardware placement"},
                {"phase_number": 3, "name": "Wiring", "description": "Power rails & signal connections"},
                {"phase_number": 4, "name": "Software/Test", "description": "Firmware upload & serial telemetry"},
                {"phase_number": 5, "name": "Final Verification", "description": "Continuous stability test"}
            ],
            "steps": fallback_steps
        }

    @classmethod
    def analyze_components(cls, custom_components):
        """Analyzes component capabilities, combinations, missing parts, and logic constraints."""
        system_instruction = (
            "You are a hardware component advisor. Distinguish between VERIFIED INFORMATION "
            "and INFORMATION THAT NEEDS VERIFICATION. Never guess unknown specs. Respond in JSON."
        )

        prompt = f"""
        Analyze these hardware components for a student project:
        {', '.join(custom_components)}

        Generate JSON:
        {{
            "summary": "Capabilities overview",
            "verified_specs": ["Spec 1", "Spec 2"],
            "needs_verification": ["Items needing datasheet check"],
            "missing_recommendations": ["Suggested accessories e.g. resistors, cables"],
            "power_considerations": "Voltage & current notes"
        }}
        """

        res = cls._call_gemini_api(prompt, system_instruction=system_instruction, json_response=True)
        if isinstance(res, dict):
            res["ai_available"] = True
            return res

        return {
            "ai_available": False,
            "summary": f"Identified {len(custom_components)} components for hardware assembly.",
            "verified_specs": ["Standard microcontroller IO headers", "Breadboard compatible pin spacing"],
            "needs_verification": ["Custom sensors require manufacturer datasheet pinout check"],
            "missing_recommendations": ["Current limiting resistors (220Ω)", "Solid-core jumper wires"],
            "power_considerations": "Always verify operating voltage (3.3V vs 5V) before applying power."
        }

    @classmethod
    def explain_build_step(cls, project_context, step_context, question):
        """
        Answers student Q&A in contextual Engineering Mentor format:
        WHAT TO DO, WHY, EXPECTED RESULT, NEXT STEP.
        """
        system_instruction = (
            "You are an encouraging Engineering Mentor for middle/high school students building electronics projects. "
            "Answer student questions concisely using the provided CURRENT PROJECT CONTEXT. "
            "Never give giant walls of text. Format response with sections: WHAT TO DO, WHY, EXPECTED RESULT, NEXT."
        )

        prompt = f"""
        CURRENT PROJECT CONTEXT:
        - Project: {project_context.get('name')}
        - Goal: {project_context.get('goal')}
        - Microcontroller: {project_context.get('microcontroller')}
        - Components: {', '.join([c.get('custom_name','') for c in project_context.get('custom_components',[])])}
        - Current Step ({step_context.get('category')}): {step_context.get('title')}
        - Step Instruction: {step_context.get('instruction')}

        STUDENT QUESTION:
        "{question}"

        Format your answer clearly:

        WHAT TO DO
        1. Concise step...

        WHY
        Short educational explanation.

        EXPECTED RESULT
        What the student should see or measure.

        NEXT STEP
        What to do once verified.
        """

        res = cls._call_gemini_api(prompt, system_instruction=system_instruction)
        if res:
            return {"ai_available": True, "answer": res}

        # Deterministic Fallback Answer
        return {
            "ai_available": False,
            "answer": (
                "WHAT TO DO\n"
                f"1. Follow the step instructions for '{step_context.get('title')}'.\n"
                "2. Double check power (VCC) and ground (GND) connections before turning on power.\n\n"
                "WHY\n"
                "Verifying connections prevents short circuits and protects your hardware ICs.\n\n"
                "EXPECTED RESULT\n"
                f"{step_context.get('test_question')}\n\n"
                "NEXT STEP\n"
                "Click 'YES — It works' to advance to the next step, or 'NO' if you need diagnostic help."
            )
        }

    @classmethod
    def troubleshoot_problem(cls, project_context, problem_desc, history_log):
        """Prioritizes next diagnostic step using student problem description and check history."""
        system_instruction = (
            "You are a hardware diagnostic expert. Use past completed checks to avoid repeating suggestions. "
            "Give practical, prioritised next diagnostic actions."
        )

        prompt = f"""
        PROJECT CONTEXT:
        Project: {project_context.get('name')}
        Microcontroller: {project_context.get('microcontroller')}
        Components: {', '.join([c.get('custom_name','') for c in project_context.get('custom_components',[])])}

        STUDENT PROBLEM DESCRIPTION:
        "{problem_desc}"

        COMPLETED DIAGNOSTIC CHECKS:
        {json.dumps(history_log)}

        Respond concisely with:
        1. Primary suspect cause
        2. Immediate single action check to perform next
        3. Safety warning if applicable
        """

        res = cls._call_gemini_api(prompt, system_instruction=system_instruction)
        if res:
            return {"ai_available": True, "advice": res}

        return {
            "ai_available": False,
            "advice": (
                "Guided Diagnostic Advice:\n"
                "1. Verify VCC and GND jumper wires are firmly connected to your power rail.\n"
                "2. Check that SDA connects to data pin (GPIO 21) and SCL connects to clock pin (GPIO 22).\n"
                "3. Verify your code baud rate matches Serial Monitor (115200 baud)."
            )
        }

    @classmethod
    def inspect_prototype_image(cls, image_base64, project_context):
        """Vision analysis of prototype photos for visible wiring errors."""
        system_instruction = (
            "You are a hardware inspection AI. Analyze prototype photos for visible wiring, board placement, "
            "and obvious connection errors. Never claim a connection is correct if image is unclear. Always add a safety disclaimer."
        )

        prompt = f"""
        Inspect this hardware prototype photo for project '{project_context.get('name')}'.
        Identify:
        1. Visible board type and modules
        2. Apparent wire connections
        3. Any obvious loose wires, reversed polarity, or pin shifts
        4. Safety check warning
        """

        res = cls._call_gemini_api(prompt, image_base64=image_base64, system_instruction=system_instruction)
        if res:
            return {"ai_available": True, "inspection": res}

        return {
            "ai_available": False,
            "inspection": (
                "Photo Analysis (Offline Mode):\n"
                "I cannot reliably verify electrical connections from this image without AI vision active.\n"
                "Please manually trace VCC to red power rail, GND to black rail, and signal wires to GPIO pins."
            )
        }
