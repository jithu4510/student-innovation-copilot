"""
Automated End-to-End Test Suite for AI-Powered Innovation Copilot Upgrade.
Executes 12-step lifecycle test covering AI Scoping, Component Analysis,
Contextual Project Mentor Q&A, Photo Prototype Inspection, Fallback Mode, and Product Analytics.
"""

import os
import unittest
import json
import base64
from app import app
from database import init_db, get_db_connection

class InnovationCopilotAiTestCase(unittest.TestCase):
    def setUp(self):
        """Sets up test client and initializes fresh database schema."""
        app.config['TESTING'] = True
        self.client = app.test_client()
        init_db()

    def test_full_ai_powered_user_flow(self):
        """Executes full 12-step AI-powered product lifecycle test."""
        
        # 1. Open application / Verify projects list
        res_list = self.client.get('/api/projects')
        self.assertEqual(res_list.status_code, 200)

        # 2 & 3. Create Project with natural goal & custom components (Triggers AI Plan & Component Advisor)
        payload = {
            "name": "ESP32 Smart Water Monitor",
            "goal": "I want to build a water quality monitor that measures TDS, turbidity, and temperature, displaying results on an OLED screen with my ESP32.",
            "microcontroller": "ESP32",
            "custom_components": [
                "ESP32",
                "SSD1306 OLED",
                "TDS sensor",
                "Turbidity sensor",
                "DS18B20"
            ]
        }

        res_create = self.client.post('/api/projects', json=payload)
        self.assertEqual(res_create.status_code, 201)
        created_id = res_create.get_json()['project_id']
        self.assertIsNotNone(created_id)

        # 4. Save & retrieve project detail (Confirm AI Plan / Fallback Plan saved)
        res_detail = self.client.get(f'/api/projects/{created_id}')
        self.assertEqual(res_detail.status_code, 200)
        proj_detail = res_detail.get_json()
        steps = proj_detail['steps']
        self.assertGreaterEqual(len(steps), 5)
        self.assertIn('custom_components', proj_detail)

        # 5. Ask AI Engineering Mentor a question about Build Step 1
        step1_id = steps[0]['id']
        mentor_payload = {
            "step_id": step1_id,
            "question": "Why are we doing this?"
        }
        res_mentor = self.client.post(f'/api/projects/{created_id}/mentor/ask', json=mentor_payload)
        self.assertEqual(res_mentor.status_code, 200)
        mentor_data = res_mentor.get_json()
        self.assertIn('response', mentor_data)

        # Pass Step 1
        self.client.post(f'/api/projects/{created_id}/steps/{step1_id}/test', json={'result': 'passed'})

        # 6. Fail Test Checkpoint on Step 2
        step2_id = steps[1]['id']
        res_s2_fail = self.client.post(f'/api/projects/{created_id}/steps/{step2_id}/test', json={'result': 'failed'})
        self.assertEqual(res_s2_fail.status_code, 200)
        fail_data = res_s2_fail.get_json()
        self.assertEqual(fail_data['status'], 'failed')

        # 7. Start Troubleshooting
        res_tb_start = self.client.post(f'/api/projects/{created_id}/troubleshoot/start')
        self.assertEqual(res_tb_start.status_code, 200)

        # 8 & 9. Step through Troubleshooting Decision Tree
        res_tb_step = self.client.post(f'/api/projects/{created_id}/troubleshoot/step', json={'option_index': 0})
        self.assertEqual(res_tb_step.status_code, 200)

        # 10. Test Photo Prototype Inspection API
        dummy_base64 = base64.b64encode(b"fake_jpeg_bytes").decode("utf-8")
        res_photo = self.client.post(f'/api/projects/{created_id}/upload_photo', json={'image_base64': dummy_base64})
        self.assertEqual(res_photo.status_code, 200)
        photo_data = res_photo.get_json()
        self.assertIn('inspection', photo_data)

        # 11. Complete remaining build steps to complete prototype
        for step in steps[1:]:
            self.client.post(f'/api/projects/{created_id}/steps/{step["id"]}/test', json={'result': 'passed'})

        # 12. Verify Real Product Analytics Dashboard Metrics
        res_analytics = self.client.get('/api/analytics')
        self.assertEqual(res_analytics.status_code, 200)
        analytics_data = res_analytics.get_json()
        self.assertGreaterEqual(analytics_data['total_projects'], 1)
        self.assertGreaterEqual(analytics_data['total_steps_completed'], 1)
        self.assertIn('recent_events', analytics_data)

        print("\n[OK] FULL 12-STEP AI-POWERED LIFECYCLE TEST PASSED PERFECTLY!")

if __name__ == '__main__':
    unittest.main()
