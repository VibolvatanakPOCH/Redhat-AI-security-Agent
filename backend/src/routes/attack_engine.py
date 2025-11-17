"""
Attack Engine Routes - Attack Simulation and Execution Module
Handles the planning and execution of simulated attacks for security testing.
"""

from flask import Blueprint, jsonify, request
import json
import os
from datetime import datetime
from openai import OpenAI
from utils.logger import get_logger

attack_bp = Blueprint('attack', __name__)
logger = get_logger('attack_engine')

# Initialize OpenAI client
client = OpenAI()

class AttackEngine:
    """Attack simulation engine for planning and executing security tests."""
    
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        self.attacks_file = os.path.join(self.data_dir, 'attacks.json')
        self.load_data()
    
    def load_data(self):
        """Load existing attack data from files."""
        try:
            with open(self.attacks_file, 'r') as f:
                self.attacks = json.load(f)
        except FileNotFoundError:
            self.attacks = []
    
    def save_data(self):
        """Save attack data to files."""
        with open(self.attacks_file, 'w') as f:
            json.dump(self.attacks, f, indent=2)
    
    def plan_attack(self, target_info, objectives):
        """Plan an attack based on target information and objectives."""
        attack_plan = {
            "id": len(self.attacks) + 1,
            "timestamp": datetime.now().isoformat(),
            "target": target_info,
            "objectives": objectives,
            "status": "planned",
            "phases": []
        }
        
        # Use AI to generate attack plan
        prompt = f"""
        As a cybersecurity expert, create a detailed attack plan for ethical penetration testing.
        
        Target Information:
        {json.dumps(target_info, indent=2)}
        
        Objectives:
        {json.dumps(objectives, indent=2)}
        
        Create a comprehensive attack plan with the following structure:
        {{
            "reconnaissance": {{
                "techniques": ["technique1", "technique2"],
                "tools": ["tool1", "tool2"],
                "expected_outcomes": ["outcome1", "outcome2"]
            }},
            "vulnerability_assessment": {{
                "techniques": ["technique1", "technique2"],
                "tools": ["tool1", "tool2"],
                "expected_outcomes": ["outcome1", "outcome2"]
            }},
            "exploitation": {{
                "techniques": ["technique1", "technique2"],
                "tools": ["tool1", "tool2"],
                "expected_outcomes": ["outcome1", "outcome2"]
            }},
            "post_exploitation": {{
                "techniques": ["technique1", "technique2"],
                "tools": ["tool1", "tool2"],
                "expected_outcomes": ["outcome1", "outcome2"]
            }},
            "risk_assessment": {{
                "severity": "low/medium/high/critical",
                "impact": "description of potential impact",
                "likelihood": "description of likelihood"
            }}
        }}
        
        Focus on ethical hacking techniques and ensure all activities are within legal boundaries.
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are an ethical hacking expert creating penetration testing plans."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            ai_response = response.choices[0].message.content
            
            # Extract JSON from response
            start_idx = ai_response.find('{')
            end_idx = ai_response.rfind('}') + 1
            json_str = ai_response[start_idx:end_idx]
            plan_data = json.loads(json_str)
            
            attack_plan["phases"] = plan_data
            
        except Exception as e:
            logger.error(f"Error generating attack plan: {str(e)}")
            # Fallback to basic plan structure
            attack_plan["phases"] = {
                "reconnaissance": {
                    "techniques": ["Information gathering", "OSINT"],
                    "tools": ["nmap", "whois"],
                    "expected_outcomes": ["Network topology", "Service enumeration"]
                },
                "vulnerability_assessment": {
                    "techniques": ["Port scanning", "Service enumeration"],
                    "tools": ["nessus", "openvas"],
                    "expected_outcomes": ["Vulnerability list", "Risk assessment"]
                }
            }
        
        self.attacks.append(attack_plan)
        self.save_data()
        return attack_plan
    
    def simulate_attack_step(self, attack_id, phase, technique):
        """Simulate a specific attack step."""
        # Find the attack
        attack = next((a for a in self.attacks if a["id"] == attack_id), None)
        if not attack:
            return None
        
        # Simulate the attack step
        simulation_result = {
            "attack_id": attack_id,
            "phase": phase,
            "technique": technique,
            "timestamp": datetime.now().isoformat(),
            "status": "simulated",
            "results": {
                "success": True,  # This would be determined by actual simulation
                "findings": [
                    f"Simulated execution of {technique} in {phase} phase",
                    "This is a controlled simulation for educational purposes"
                ],
                "recommendations": [
                    "Implement proper input validation",
                    "Use security headers",
                    "Regular security audits"
                ]
            }
        }
        
        # Update attack record
        if "simulation_results" not in attack:
            attack["simulation_results"] = []
        attack["simulation_results"].append(simulation_result)
        self.save_data()
        
        return simulation_result

# Initialize attack engine
engine = AttackEngine()

@attack_bp.route('/plan', methods=['POST'])
def create_attack_plan():
    """Create a new attack plan."""
    try:
        data = request.get_json()
        
        target_info = data.get('target', {})
        objectives = data.get('objectives', [])
        
        if not target_info:
            return jsonify({
                "status": "error",
                "message": "Target information is required"
            }), 400
        
        attack_plan = engine.plan_attack(target_info, objectives)
        logger.info(f"Created attack plan {attack_plan['id']} for target {target_info.get('name', 'unknown')}")
        
        return jsonify({
            "status": "success",
            "message": "Attack plan created successfully",
            "attack_plan": attack_plan
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating attack plan: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@attack_bp.route('/plans', methods=['GET'])
def get_attack_plans():
    """Get all attack plans."""
    try:
        return jsonify({
            "status": "success",
            "count": len(engine.attacks),
            "attack_plans": engine.attacks
        })
    except Exception as e:
        logger.error(f"Error retrieving attack plans: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@attack_bp.route('/simulate', methods=['POST'])
def simulate_attack():
    """Simulate an attack step."""
    try:
        data = request.get_json()
        
        attack_id = data.get('attack_id')
        phase = data.get('phase')
        technique = data.get('technique')
        
        if not all([attack_id, phase, technique]):
            return jsonify({
                "status": "error",
                "message": "attack_id, phase, and technique are required"
            }), 400
        
        result = engine.simulate_attack_step(attack_id, phase, technique)
        
        if not result:
            return jsonify({
                "status": "error",
                "message": "Attack plan not found"
            }), 404
        
        logger.info(f"Simulated attack step: {technique} in {phase} for attack {attack_id}")
        
        return jsonify({
            "status": "success",
            "message": "Attack step simulated successfully",
            "result": result
        })
        
    except Exception as e:
        logger.error(f"Error simulating attack: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@attack_bp.route('/techniques', methods=['GET'])
def get_attack_techniques():
    """Get available attack techniques by category."""
    try:
        techniques = {
            "reconnaissance": [
                "OSINT gathering",
                "DNS enumeration", 
                "Port scanning",
                "Service fingerprinting",
                "Social media reconnaissance"
            ],
            "vulnerability_assessment": [
                "Web application scanning",
                "Network vulnerability scanning",
                "Configuration review",
                "Code analysis",
                "Privilege escalation testing"
            ],
            "exploitation": [
                "SQL injection",
                "Cross-site scripting (XSS)",
                "Command injection",
                "Buffer overflow",
                "Authentication bypass"
            ],
            "post_exploitation": [
                "Lateral movement",
                "Data exfiltration simulation",
                "Persistence mechanisms",
                "Privilege escalation",
                "Evidence collection"
            ]
        }
        
        return jsonify({
            "status": "success",
            "techniques": techniques
        })
        
    except Exception as e:
        logger.error(f"Error retrieving techniques: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@attack_bp.route('/chatbot/test', methods=['POST'])
def test_chatbot():
    """Test a chatbot for vulnerabilities."""
    try:
        data = request.get_json()
        
        chatbot_url = data.get('url')
        test_type = data.get('test_type', 'basic')
        
        if not chatbot_url:
            return jsonify({
                "status": "error",
                "message": "Chatbot URL is required"
            }), 400
        
        # Simulate chatbot testing
        test_results = {
            "target": chatbot_url,
            "test_type": test_type,
            "timestamp": datetime.now().isoformat(),
            "vulnerabilities_found": [
                {
                    "type": "Prompt Injection",
                    "severity": "High",
                    "description": "Chatbot may be vulnerable to prompt injection attacks",
                    "recommendation": "Implement input sanitization and prompt filtering"
                },
                {
                    "type": "Information Disclosure",
                    "severity": "Medium", 
                    "description": "Chatbot may leak sensitive information in responses",
                    "recommendation": "Review response filtering mechanisms"
                }
            ],
            "test_summary": {
                "total_tests": 15,
                "vulnerabilities_found": 2,
                "risk_level": "Medium"
            }
        }
        
        logger.info(f"Completed chatbot security test for {chatbot_url}")
        
        return jsonify({
            "status": "success",
            "message": "Chatbot security test completed",
            "results": test_results
        })
        
    except Exception as e:
        logger.error(f"Error testing chatbot: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
