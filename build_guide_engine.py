"""
Build Guide Engine for Innovation Copilot.
Generates structured 5-stage build plans for hardware electronics projects.
Fully supports custom components typed by students without relying on external AI services.
"""

def generate_5stage_build_plan(microcontroller, custom_components):
    """
    Generates a structured 5-stage build plan based on microcontroller & typed custom component list.
    Stages: 1. Preparation, 2. Assembly, 3. Wiring, 4. Software/Test, 5. Final Verification.
    """
    # Clean component strings list
    comps_str = ", ".join(custom_components) if custom_components else "Microcontroller & jumper wires"
    
    # Determine I2C & logic voltage defaults
    mcu_upper = microcontroller.upper()
    if "ESP32" in mcu_upper:
        vcc_spec = "3.3V"
        i2c_pins = "GPIO 21 (SDA) and GPIO 22 (SCL)"
        baud_rate = "115200"
    elif "ARDUINO" in mcu_upper:
        vcc_spec = "5V"
        i2c_pins = "Analog A4 (SDA) and Analog A5 (SCL)"
        baud_rate = "9600"
    else:
        vcc_spec = "Operating Voltage (3.3V or 5V as per spec)"
        i2c_pins = "Standard SDA/SCL Data pins"
        baud_rate = "115200"

    has_oled = any("OLED" in c.upper() or "DISPLAY" in c.upper() for c in custom_components)
    has_sensor = any(any(s in c.upper() for s in ["SENSOR", "DHT", "TDS", "TURBIDITY", "DS18B20", "HC-SR04", "TEMP"]) for c in custom_components)

    steps = [
        # Stage 1: Preparation
        {
            "step_number": 1,
            "category": "Preparation",
            "title": "Inventory & Pinout Inspection",
            "instruction": f"Gather and inspect your components: {comps_str}. Identify power (VCC/GND) and signal pins on each module before wiring.",
            "why_matters": f"Double-checking component labels prevents reverse polarity damage. {microcontroller} uses {vcc_spec} logic.",
            "required_components": comps_str,
            "warning_note": "Ensure USB power is disconnected from your microcontroller during physical setup.",
            "test_question": "Have you verified the pin labels on all your project components?"
        },
        # Stage 2: Assembly
        {
            "step_number": 2,
            "category": "Assembly",
            "title": "Breadboard Placement & Mechanical Layout",
            "instruction": f"Seat your {microcontroller} firmly across the breadboard divider rail. Mount external components ensuring pins do not short across adjacent breadboard rows.",
            "why_matters": "Firm mechanical mounting prevents loose contacts and noise in digital sensor lines.",
            "required_components": comps_str,
            "warning_note": "Avoid pushing component legs forcefully into breadboard holes to prevent bending pins.",
            "test_question": "Are all components securely placed in the breadboard?"
        },
        # Stage 3: Wiring
        {
            "step_number": 3,
            "category": "Wiring",
            "title": "Power Rail & Signal Wiring",
            "instruction": f"Connect power VCC -> {vcc_spec} and GND -> GND. " + 
                         (f"Connect I2C display SDA and SCL pins to {microcontroller} {i2c_pins}. " if has_oled else "") +
                         (f"Connect sensor signal line to designated GPIO digital/analog pin. " if has_sensor else "") +
                         "For unverified custom modules, refer to manufacturer pinout diagram.",
            "why_matters": f"Establishing common ground reference ensures noise-free signal transmission between {microcontroller} and modules.",
            "required_components": comps_str,
            "warning_note": f"Do not supply 5V to 3.3V-only pins on {microcontroller}.",
            "test_question": "Are VCC, GND, and signal data lines wired according to pin specifications?"
        },
        # Stage 4: Software/Test
        {
            "step_number": 4,
            "category": "Software/Test",
            "title": "Upload Firmware & Checkpoint Verification",
            "instruction": f"Connect {microcontroller} to computer via USB cable. Open IDE, select board '{microcontroller}', set Serial Monitor to {baud_rate} baud, and flash starter code.",
            "why_matters": "Serial output logs confirm that microcontroller firmware initializes component communications.",
            "required_components": microcontroller,
            "warning_note": f"Ensure correct COM port and baud rate ({baud_rate}) are selected.",
            "test_question": "Does the system serial monitor or display show valid test output?"
        },
        # Stage 5: Final Verification
        {
            "step_number": 5,
            "category": "Final Verification",
            "title": "Continuous Operation & Prototype Stability",
            "instruction": "Leave prototype powered on for 60 seconds. Verify stable sensor readings or display updates without brownouts.",
            "why_matters": "Validates circuit stability and thermal/current power balance for a reliable finished prototype.",
            "required_components": comps_str,
            "warning_note": "If any module feels excessively hot, immediately disconnect power.",
            "test_question": "Is your hardware prototype operating continuously and reliably?"
        }
    ]

    return steps
