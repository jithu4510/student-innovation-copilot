"""
Database initialization and analytics module for Innovation Copilot.
Handles SQLite tables, schema migrations, component database seeding, analytics logging, and Q&A history.
Supports Vercel serverless deployment using /tmp storage fallback.
"""

import sqlite3
import os
import json

# Handle Vercel serverless read-only filesystem
if os.environ.get("VERCEL"):
    DB_PATH = "/tmp/innovation_copilot.db"
else:
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "innovation_copilot.db")

def get_db_connection():
    """Establishes connection to SQLite database with WAL mode (or standard for /tmp) and 10s timeout."""
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
    except Exception:
        pass
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes schema, applies migrations, and seeds default component library and demo project."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Verified Components Library Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS components (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        type TEXT NOT NULL,
        voltage TEXT NOT NULL,
        common_pins TEXT NOT NULL,
        protocol TEXT NOT NULL,
        common_problems TEXT NOT NULL,
        description TEXT NOT NULL,
        icon TEXT NOT NULL
    );
    """)

    # 2. Projects Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        goal TEXT NOT NULL,
        microcontroller TEXT NOT NULL,
        current_stage TEXT NOT NULL DEFAULT 'Preparation',
        current_step_index INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'in_progress',
        current_problem TEXT,
        estimated_difficulty TEXT DEFAULT 'Intermediate',
        ai_plan_json TEXT,
        ai_component_analysis_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Migration
    cursor.execute("PRAGMA table_info(projects)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'estimated_difficulty' not in columns:
        cursor.execute("ALTER TABLE projects ADD COLUMN estimated_difficulty TEXT DEFAULT 'Intermediate'")
    if 'ai_plan_json' not in columns:
        cursor.execute("ALTER TABLE projects ADD COLUMN ai_plan_json TEXT")
    if 'ai_component_analysis_json' not in columns:
        cursor.execute("ALTER TABLE projects ADD COLUMN ai_component_analysis_json TEXT")

    # 3. Project Components Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS project_components (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        component_id INTEGER,
        custom_name TEXT NOT NULL,
        FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
        FOREIGN KEY (component_id) REFERENCES components (id) ON DELETE SET NULL
    );
    """)

    # 4. Build Steps Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS build_steps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        step_number INTEGER NOT NULL,
        category TEXT NOT NULL,
        title TEXT NOT NULL,
        instruction TEXT NOT NULL,
        why_matters TEXT NOT NULL,
        required_components TEXT NOT NULL,
        warning_note TEXT,
        test_question TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
    );
    """)

    # 5. Test Results Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS test_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        step_id INTEGER NOT NULL,
        result TEXT NOT NULL,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
        FOREIGN KEY (step_id) REFERENCES build_steps (id) ON DELETE CASCADE
    );
    """)

    # 6. Troubleshooting Sessions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS troubleshooting_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        step_id INTEGER NOT NULL,
        current_node_id TEXT NOT NULL,
        history_json TEXT NOT NULL DEFAULT '[]',
        status TEXT NOT NULL DEFAULT 'in_progress',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
        FOREIGN KEY (step_id) REFERENCES build_steps (id) ON DELETE CASCADE
    );
    """)

    # 7. Real Analytics Logging Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS analytics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,
        project_id INTEGER,
        details_json TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 8. AI Mentor Messages Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ai_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        step_id INTEGER,
        user_question TEXT NOT NULL,
        ai_response TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
    );
    """)

    conn.commit()

    # Seed Component Database
    seed_components(conn)

    # Seed Demo Project
    seed_demo_project(conn)

    conn.commit()
    conn.close()

def log_analytics_event(event_type, project_id=None, details=None):
    """Logs real product analytics events to SQLite database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        details_str = json.dumps(details) if details else None
        cursor.execute("""
            INSERT INTO analytics (event_type, project_id, details_json)
            VALUES (?, ?, ?)
        """, (event_type, project_id, details_str))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Analytics Warning] {e}")

def seed_components(conn):
    """Seeds verified component library reference database."""
    components = [
        {
            "name": "ESP32",
            "type": "Microcontroller",
            "voltage": "3.3V (Logic)",
            "common_pins": "3V3, GND, GPIO 21 (SDA), GPIO 22 (SCL), TX, RX, GPIO 2, GPIO 4",
            "protocol": "I2C, SPI, UART, Wi-Fi, Bluetooth",
            "common_problems": "Connecting 5V directly to GPIO pins damages chip. Serial Monitor baud rate mismatch (must use 115200 baud). Weak USB cable causes brownout reset.",
            "description": "Powerful 32-bit dual-core microcontroller with integrated Wi-Fi and Bluetooth.",
            "icon": "cpu"
        },
        {
            "name": "Arduino Uno",
            "type": "Microcontroller",
            "voltage": "5V (Logic)",
            "common_pins": "5V, 3.3V, GND, Analog A4 (SDA), Analog A5 (SCL), Digital 0-13",
            "protocol": "I2C, SPI, UART",
            "common_problems": "Upload fails if RX (0) / TX (1) pins are attached to external hardware during upload. Current limit per pin is 40mA.",
            "description": "Classic 8-bit ATmega328P microcontroller board ideal for electronics beginners.",
            "icon": "motherboard"
        },
        {
            "name": "SSD1306 OLED",
            "type": "Display",
            "voltage": "3.3V - 5V",
            "common_pins": "VCC, GND, SDA, SCL",
            "protocol": "I2C (Address 0x3C or 0x3D)",
            "common_problems": "Blank display if I2C address in code does not match chip (0x3C vs 0x3D). Swapped SDA and SCL wires.",
            "description": "0.96-inch monochrome 128x64 or 128x32 graphic OLED display module.",
            "icon": "display"
        },
        {
            "name": "DHT11",
            "type": "Sensor",
            "voltage": "3.3V - 5V",
            "common_pins": "VCC, DATA, NC, GND",
            "protocol": "1-Wire Digital",
            "common_problems": "Reading values faster than once per 2 seconds causes returned NaN errors. Missing 10kΩ pull-up resistor on DATA.",
            "description": "Digital temperature and humidity sensor with single-bus digital acquisition.",
            "icon": "thermometer"
        },
        {
            "name": "HC-SR04",
            "type": "Sensor",
            "voltage": "5V",
            "common_pins": "VCC, Trig, Echo, GND",
            "protocol": "Pulse Timing",
            "common_problems": "Echo pin outputs 5V logic; requires voltage divider (1kΩ/2kΩ) before connecting to 3.3V ESP32 GPIO pins.",
            "description": "Ultrasonic distance sensor measuring range from 2cm to 400cm.",
            "icon": "radar"
        },
        {
            "name": "Servo",
            "type": "Actuator",
            "voltage": "4.8V - 6.0V",
            "common_pins": "VCC (Red), GND (Brown/Black), Signal (Orange)",
            "protocol": "PWM",
            "common_problems": "Servo high peak current draw causes microcontroller reset; power directly from dedicated power rail.",
            "description": "Micro 9g servo motor with 180-degree position control.",
            "icon": "gear"
        },
        {
            "name": "Push Button",
            "type": "Input",
            "voltage": "3.3V / 5V",
            "common_pins": "Pin A, Pin B",
            "protocol": "Digital Input",
            "common_problems": "Floating pin state when unpressed. Requires INPUT_PULLUP in code or external pulldown resistor.",
            "description": "Tactile switch providing digital HIGH/LOW state when pressed.",
            "icon": "toggle-on"
        },
        {
            "name": "LED",
            "type": "Output",
            "voltage": "1.8V - 3.3V",
            "common_pins": "Anode (+) [Long leg], Cathode (-) [Short leg]",
            "protocol": "Digital Output",
            "common_problems": "LED burns out without current-limiting resistor (220Ω - 330Ω) in series. Reverse polarity connection.",
            "description": "Light Emitting Diode for visual indicator status.",
            "icon": "lightbulb"
        },
        {
            "name": "Buzzer",
            "type": "Output",
            "voltage": "3.3V - 5V",
            "common_pins": "Positive (+), Negative (-)",
            "protocol": "Digital / PWM Tone",
            "common_problems": "Passive buzzer requires tone() frequency signal; active buzzer requires simple digital HIGH voltage.",
            "description": "Piezo sound transducer for audible alerts and alarms.",
            "icon": "volume-up"
        },
        {
            "name": "Potentiometer",
            "type": "Input",
            "voltage": "0V - VCC",
            "common_pins": "Terminal 1 (GND), Wiper (Analog), Terminal 2 (VCC)",
            "protocol": "Analog Voltage",
            "common_problems": "Shorted power supply if VCC and GND are connected to adjacent outer pins.",
            "description": "3-terminal variable resistor providing adjustable analog voltage input.",
            "icon": "sliders"
        }
    ]

    cursor = conn.cursor()
    for comp in components:
        cursor.execute("""
        INSERT INTO components (name, type, voltage, common_pins, protocol, common_problems, description, icon)
        VALUES (:name, :type, :voltage, :common_pins, :protocol, :common_problems, :description, :icon)
        ON CONFLICT(name) DO UPDATE SET
            type=excluded.type,
            voltage=excluded.voltage,
            common_pins=excluded.common_pins,
            protocol=excluded.protocol,
            common_problems=excluded.common_problems,
            description=excluded.description,
            icon=excluded.icon;
        """, comp)
    conn.commit()

def seed_demo_project(conn):
    """Seeds the ready-to-use 'ESP32 OLED Display' demo project."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM projects WHERE name = 'ESP32 OLED Display'")
    row = cursor.fetchone()

    if row:
        demo_id = row['id']
    else:
        cursor.execute("""
        INSERT INTO projects (name, goal, microcontroller, current_stage, current_step_index, status, current_problem, estimated_difficulty)
        VALUES ('ESP32 OLED Display', 'Interface an SSD1306 0.96" OLED display to ESP32 over I2C and display a test message.', 'ESP32', 'Preparation', 0, 'in_progress', 'OLED screen is blank after flashing code', 'Beginner')
        """)
        demo_id = cursor.lastrowid

        custom_comps = [
            ("ESP32", 1),
            ("SSD1306 OLED 0.96\"", 3),
            ("Jumper Wires", None),
            ("Breadboard", None)
        ]
        for name, comp_id in custom_comps:
            cursor.execute("""
            INSERT INTO project_components (project_id, component_id, custom_name)
            VALUES (?, ?, ?)
            """, (demo_id, comp_id, name))

        steps = [
            {
                "step_number": 1,
                "category": "Preparation",
                "title": "Unpack & Inspect Components",
                "instruction": "Inspect your ESP32 board and SSD1306 OLED display. Locate the 4 pins on the OLED module: VCC, GND, SDA, and SCL.",
                "why_matters": "Verifying pin labels before wiring prevents accidental reversed polarity connections.",
                "required_components": "ESP32, SSD1306 OLED 0.96\"",
                "warning_note": "Do not connect USB power to the ESP32 while wiring.",
                "test_question": "Have you identified the VCC, GND, SDA, and SCL pins on your OLED module?"
            },
            {
                "step_number": 2,
                "category": "Assembly",
                "title": "Insert Components into Breadboard",
                "instruction": "Place the ESP32 board firmly into the breadboard bridging the center divider. Insert the SSD1306 OLED module into an adjacent breadboard section.",
                "why_matters": "Firm mechanical insertion prevents loose pin contacts and intermittent power disconnects.",
                "required_components": "ESP32, SSD1306 OLED 0.96\", Breadboard",
                "warning_note": "Ensure breadboard pins do not short across adjacent rows.",
                "test_question": "Are both the ESP32 and OLED firmly seated in the breadboard?"
            },
            {
                "step_number": 3,
                "category": "Wiring",
                "title": "Connect Power & I2C Data Lines",
                "instruction": "Connect OLED VCC -> ESP32 3.3V (Red wire). Connect OLED GND -> ESP32 GND (Black wire). Connect OLED SDA -> ESP32 GPIO 21 (Blue wire). Connect OLED SCL -> ESP32 GPIO 22 (Yellow wire).",
                "why_matters": "ESP32 uses GPIO 21 for I2C Data (SDA) and GPIO 22 for I2C Clock (SCL) by default in Arduino Wire library.",
                "required_components": "Jumper Wires",
                "warning_note": "Connect VCC to 3.3V pin ONLY. 5V may damage 3.3V-only display drivers.",
                "test_question": "Are VCC, GND, SDA (GPIO 21), and SCL (GPIO 22) wired correctly?"
            },
            {
                "step_number": 4,
                "category": "Software/Test",
                "title": "Upload OLED Verification Sketch",
                "instruction": "Connect ESP32 to computer via USB. Open Arduino IDE, select board 'ESP32 Dev Module', set Serial Monitor to 115200 baud, and upload the minimal Adafruit_SSD1306 test sketch.",
                "why_matters": "Uploads the graphics library driver code and tests I2C communication at address 0x3C.",
                "required_components": "ESP32",
                "warning_note": "Verify Adafruit_SSD1306 and Adafruit_GFX libraries are installed.",
                "test_question": "Does the OLED display show the 'Innovation Copilot Ready' test message?"
            },
            {
                "step_number": 5,
                "category": "Final Verification",
                "title": "Prototype Final Inspection",
                "instruction": "Confirm the display text updates smoothly and power supply remains stable over 60 seconds of operation.",
                "why_matters": "Final verification ensures reliable continuous operation before enclosing your prototype.",
                "required_components": "ESP32, SSD1306 OLED 0.96\"",
                "warning_note": "Check board temperature to confirm no short circuits exist.",
                "test_question": "Is your OLED display prototype operating stably?"
            }
        ]

        for s in steps:
            cursor.execute("""
            INSERT INTO build_steps (project_id, step_number, category, title, instruction, why_matters, required_components, warning_note, test_question, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            """, (demo_id, s['step_number'], s['category'], s['title'], s['instruction'], s['why_matters'], s['required_components'], s['warning_note'], s['test_question']))

    conn.commit()

if __name__ == '__main__':
    init_db()
    print("Database schema initialized and updated successfully.")
