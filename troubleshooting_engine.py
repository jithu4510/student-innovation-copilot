"""
Rule-Based Troubleshooting Engine for Innovation Copilot.
Provides deterministic, step-by-step diagnostic trees for common hardware issues.
Strictly NO AI / NO LLM - state machine diagnostic trees.
"""

TROUBLESHOOTING_TREES = {
    # 1. OLED / Display Troubleshooting Diagnostic Tree
    "oled_display_issues": {
        "title": "OLED Display Not Displaying Diagnostic Flow",
        "start_node": "step1_power",
        "nodes": {
            "step1_power": {
                "question": "Step 1: Power Verification. Is the OLED display module receiving power (VCC & GND connected)?",
                "why": "OLED display driver IC requires a stable 3.3V power supply and shared GND reference to illuminate pixels.",
                "options": [
                    {
                        "text": "YES - Power pins are connected",
                        "next_node": "step2_data_lines",
                        "is_issue": False
                    },
                    {
                        "text": "NO - Pins were loose or unpowered",
                        "next_node": "action_fix_power",
                        "is_issue": True
                    }
                ]
            },
            "action_fix_power": {
                "question": "Diagnostic Guidance: Connect OLED VCC to 3.3V and GND to GND firmly on your microcontroller.",
                "why": "Verify jumper wires are pressed all the way into breadboard holes.",
                "options": [
                    {
                        "text": "I checked it - Power is now connected",
                        "next_node": "step2_data_lines",
                        "is_issue": False
                    }
                ]
            },
            "step2_data_lines": {
                "question": "Step 2: Signal Data Wiring. Are SDA connected to GPIO 21 (or A4) and SCL connected to GPIO 22 (or A5)?",
                "why": "I2C protocol requires dedicated SDA (Serial Data) and SCL (Serial Clock) signals.",
                "options": [
                    {
                        "text": "YES - Data pins match hardware assignment",
                        "next_node": "step3_i2c_scanner",
                        "is_issue": False
                    },
                    {
                        "text": "NO - Wires were swapped or on wrong pins",
                        "next_node": "action_fix_data_pins",
                        "is_issue": True
                    }
                ]
            },
            "action_fix_data_pins": {
                "question": "Diagnostic Guidance: Swap jumper wires so SDA connects to GPIO 21 and SCL connects to GPIO 22.",
                "why": "Swapped SDA/SCL lines prevent I2C handshaking.",
                "options": [
                    {
                        "text": "I checked it - Pins are now correctly mapped",
                        "next_node": "step3_i2c_scanner",
                        "is_issue": False
                    }
                ]
            },
            "step3_i2c_scanner": {
                "question": "Step 3: I2C Scanner Verification. Run the I2C scanner sketch in Serial Monitor. Did the scanner detect an I2C device?",
                "why": "An I2C scanner pings bus addresses to verify physical chip electrical communication.",
                "options": [
                    {
                        "text": "YES - Device detected (e.g. at 0x3C or 0x3D)",
                        "next_node": "step4_address_check",
                        "is_issue": False
                    },
                    {
                        "text": "NO - Scanner reported 0 devices found",
                        "next_node": "resolved_wiring_fault",
                        "is_issue": True
                    }
                ]
            },
            "step4_address_check": {
                "question": "Step 4: I2C Address in Code. Does the address in your Arduino sketch (e.g. 0x3C) match the scanner output?",
                "why": "Most OLEDs default to 0x3C, but some use 0x3D. Address mismatch causes silent initialization failure.",
                "options": [
                    {
                        "text": "YES - Address in code matches 0x3C",
                        "next_node": "resolved_success",
                        "is_issue": False
                    },
                    {
                        "text": "NO - Address was 0x3D in scanner, 0x3C in code",
                        "next_node": "action_fix_address",
                        "is_issue": True
                    }
                ]
            },
            "action_fix_address": {
                "question": "Diagnostic Guidance: Change code initialization to `display.begin(SSD1306_SWITCHCAPVCC, 0x3D);` and re-upload.",
                "why": "Updates Adafruit_SSD1306 library to communicate on target address 0x3D.",
                "options": [
                    {
                        "text": "I checked it - Re-uploaded code with address 0x3D",
                        "next_node": "resolved_success",
                        "is_issue": False
                    }
                ]
            },
            # Terminal Nodes
            "resolved_success": {
                "is_terminal": True,
                "status": "resolved",
                "title": "Problem Solved ✓",
                "action": "Hardware wiring and display driver software initialization are verified and working.",
                "recommendation": "Return to workspace build guide to complete prototype!"
            },
            "resolved_wiring_fault": {
                "is_terminal": True,
                "status": "unresolved",
                "title": "Basic Checks Completed",
                "action": "No I2C device detected on bus. The next step is to inspect the display module or try swapping jumper wires and breadboard rows.",
                "recommendation": "Replace jumper wires or test display on alternate microcontroller."
            }
        }
    },
    # 2. General Sensor & Hardware Troubleshooting Flow
    "general_hardware_issues": {
        "title": "General Hardware Diagnostic Flow",
        "start_node": "step1_power",
        "nodes": {
            "step1_power": {
                "question": "Step 1: Check Power Connections. Is the module VCC connected to required voltage (3.3V or 5V) and GND to GND?",
                "why": "Sensors and modules fail to communicate if operating voltage is missing or GND reference is loose.",
                "options": [
                    {
                        "text": "YES - Power and GND are connected",
                        "next_node": "step2_gpio_mapping",
                        "is_issue": False
                    },
                    {
                        "text": "NO - Power wire was disconnected",
                        "next_node": "action_fix_power",
                        "is_issue": True
                    }
                ]
            },
            "action_fix_power": {
                "question": "Diagnostic Guidance: Firmly attach VCC to operating voltage pin and GND to GND pin.",
                "why": "Ensures module IC turns on.",
                "options": [
                    {
                        "text": "I checked it - Power is connected",
                        "next_node": "step2_gpio_mapping",
                        "is_issue": False
                    }
                ]
            },
            "step2_gpio_mapping": {
                "question": "Step 2: Signal Pin Mapping. Does the pin number declared in code match the physical pin connected?",
                "why": "Firmware reads data strictly from specified GPIO pin numbers.",
                "options": [
                    {
                        "text": "YES - Physical pin matches code declaration",
                        "next_node": "step3_baud_delay",
                        "is_issue": False
                    },
                    {
                        "text": "NO - Wires were in wrong GPIO socket",
                        "next_node": "action_fix_pin",
                        "is_issue": True
                    }
                ]
            },
            "action_fix_pin": {
                "question": "Diagnostic Guidance: Update pin declaration in code or move physical wire to match.",
                "why": "Fixes pin routing mismatch.",
                "options": [
                    {
                        "text": "I checked it - Pin mapping updated",
                        "next_node": "step3_baud_delay",
                        "is_issue": False
                    }
                ]
            },
            "step3_baud_delay": {
                "question": "Step 3: Serial Baud Rate & Loop Delay. Is Serial Monitor set to 115200 baud with a 1000ms delay in loop?",
                "why": "Reading sensors too fast or mismatched baud rate causes output corruption or returned NaN values.",
                "options": [
                    {
                        "text": "YES - Baud rate and sampling delay are set",
                        "next_node": "resolved_success",
                        "is_issue": False
                    },
                    {
                        "text": "NO - Need to adjust delay or baud rate",
                        "next_node": "action_fix_delay",
                        "is_issue": True
                    }
                ]
            },
            "action_fix_delay": {
                "question": "Diagnostic Guidance: Add `delay(1000);` in loop and set Serial Monitor to 115200 baud.",
                "why": "Stabilizes serial telemetry output.",
                "options": [
                    {
                        "text": "I checked it - Code updated",
                        "next_node": "resolved_success",
                        "is_issue": False
                    }
                ]
            },
            "resolved_success": {
                "is_terminal": True,
                "status": "resolved",
                "title": "Problem Solved ✓",
                "action": "Hardware power, GPIO mapping, and signal telemetry verified.",
                "recommendation": "Return to workspace build guide!"
            }
        }
    }
}

class RuleBasedTroubleshootingEngine:
    """State machine solver for hardware troubleshooting trees."""

    @staticmethod
    def get_tree_key(custom_components, problem_text=""):
        """Determines matching diagnostic tree based on project components."""
        comps_upper = [c.upper() for c in custom_components]
        if any("OLED" in c or "DISPLAY" in c for c in comps_upper) or "OLED" in problem_text.upper():
            return "oled_display_issues"
        return "general_hardware_issues"

    @staticmethod
    def start_session(project_id, step_id, tree_key="oled_display_issues"):
        """Initializes a new troubleshooting session starting at the root node."""
        tree = TROUBLESHOOTING_TREES.get(tree_key, TROUBLESHOOTING_TREES["oled_display_issues"])
        start_node_id = tree["start_node"]
        start_node = tree["nodes"][start_node_id]

        return {
            "project_id": project_id,
            "step_id": step_id,
            "tree_key": tree_key,
            "tree_title": tree["title"],
            "current_node_id": start_node_id,
            "current_node": start_node,
            "history": [],
            "status": "in_progress"
        }

    @staticmethod
    def process_answer(tree_key, current_node_id, option_index, history=None):
        """Advances diagnostic state machine based on option selection."""
        if history is None:
            history = []

        tree = TROUBLESHOOTING_TREES.get(tree_key, TROUBLESHOOTING_TREES["oled_display_issues"])
        current_node = tree["nodes"].get(current_node_id)

        if not current_node or "options" not in current_node:
            return None

        if option_index < 0 or option_index >= len(current_node["options"]):
            return None

        selected_option = current_node["options"][option_index]
        next_node_id = selected_option["next_node"]
        next_node = tree["nodes"].get(next_node_id)

        history.append({
            "node_id": current_node_id,
            "question": current_node["question"],
            "selected_answer": selected_option["text"],
            "is_issue": selected_option.get("is_issue", False)
        })

        is_terminal = next_node.get("is_terminal", False)
        status = next_node.get("status", "in_progress") if is_terminal else "in_progress"

        return {
            "tree_key": tree_key,
            "tree_title": tree["title"],
            "current_node_id": next_node_id,
            "current_node": next_node,
            "history": history,
            "status": status,
            "is_terminal": is_terminal
        }
