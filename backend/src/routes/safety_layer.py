"""
Safety Layer Routes - Ethical Constraints and Safety Protocols
Ensures all activities comply with ethical hacking guidelines and legal boundaries.
"""

from flask import Blueprint, jsonify, request
import json
import os
from datetime import datetime
from utils.logger import get_logger

safety_bp = Blueprint('safety', __name__)
logger = get_logger('safety_layer')

class SafetyLayer:
    """Safety layer for enforcing ethical constraints and monitoring activities."""
    
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        self.audit_file = os.path.join(self.data_dir, 'audit_log.json')
        self.authorized_targets_file = os.path.join(self.data_dir, 'authorized_targets.json')
        self.load_data()
        
        # Safety configuration
        self.safety_config = {
            "require_authorization": True,
            "log_all_activities": True,
            "block_unauthorized_targets": True,
            "max_concurrent_attacks": 3,
            "emergency_stop_enabled": True
        }
    
    def load_data(self):
        """Load existing safety data from files."""
        try:
            with open(self.audit_file, 'r') as f:
                self.audit_log = json.load(f)
        except FileNotFoundError:
            self.audit_log = []
            
        try:
            with open(self.authorized_targets_file, 'r') as f:
                self.authorized_targets = json.load(f)
        except FileNotFoundError:
            self.authorized_targets = []
    
    def save_data(self):
        """Save safety data to files."""
        with open(self.audit_file, 'w') as f:
            json.dump(self.audit_log, f, indent=2)
        
        with open(self.authorized_targets_file, 'w') as f:
            json.dump(self.authorized_targets, f, indent=2)
    
    def log_activity(self, activity_type, details, user_id=None):
        """Log an activity for audit purposes."""
        log_entry = {
            "id": len(self.audit_log) + 1,
            "timestamp": datetime.now().isoformat(),
            "activity_type": activity_type,
            "details": details,
            "user_id": user_id,
            "ip_address": request.remote_addr if request else None
        }
        
        self.audit_log.append(log_entry)
        self.save_data()
        logger.info(f"Logged activity: {activity_type}")
        return log_entry
    
    def is_target_authorized(self, target):
        """Check if a target is authorized for testing."""
        target_domain = self.extract_domain(target)
        
        for authorized in self.authorized_targets:
            if authorized.get('domain') == target_domain and authorized.get('status') == 'active':
                return True, authorized
        
        return False, None
    
    def extract_domain(self, url):
        """Extract domain from URL."""
        if url.startswith('http://') or url.startswith('https://'):
            return url.split('/')[2]
        return url.split('/')[0]
    
    def authorize_target(self, target_info, authorization_details):
        """Authorize a new target for testing."""
        authorization = {
            "id": len(self.authorized_targets) + 1,
            "domain": self.extract_domain(target_info.get('url', '')),
            "target_info": target_info,
            "authorization_details": authorization_details,
            "status": "active",
            "authorized_by": authorization_details.get('authorized_by'),
            "authorization_date": datetime.now().isoformat(),
            "expiry_date": authorization_details.get('expiry_date'),
            "scope": authorization_details.get('scope', [])
        }
        
        self.authorized_targets.append(authorization)
        self.save_data()
        
        # Log the authorization
        self.log_activity("target_authorization", {
            "target": target_info,
            "authorization_id": authorization["id"]
        })
        
        return authorization
    
    def validate_attack_request(self, attack_request):
        """Validate an attack request against safety policies."""
        validation_result = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "recommendations": []
        }
        
        target = attack_request.get('target', {})
        target_url = target.get('url', '')
        
        # Check if target is authorized
        if self.safety_config["require_authorization"]:
            is_authorized, auth_details = self.is_target_authorized(target_url)
            if not is_authorized:
                validation_result["valid"] = False
                validation_result["errors"].append(
                    f"Target {target_url} is not authorized for testing"
                )
            else:
                # Check if authorization is still valid
                if auth_details and auth_details.get('expiry_date'):
                    expiry = datetime.fromisoformat(auth_details['expiry_date'])
                    if datetime.now() > expiry:
                        validation_result["valid"] = False
                        validation_result["errors"].append(
                            f"Authorization for {target_url} has expired"
                        )
        
        # Check for dangerous techniques
        dangerous_techniques = [
            "data_destruction",
            "system_compromise",
            "unauthorized_access",
            "malware_deployment"
        ]
        
        objectives = attack_request.get('objectives', [])
        for objective in objectives:
            if any(dangerous in objective.lower() for dangerous in dangerous_techniques):
                validation_result["warnings"].append(
                    f"Potentially dangerous objective detected: {objective}"
                )
        
        # Add safety recommendations
        validation_result["recommendations"].extend([
            "Ensure all testing is conducted in a controlled environment",
            "Obtain proper written authorization before testing",
            "Document all activities for compliance purposes",
            "Follow responsible disclosure practices for any findings"
        ])
        
        return validation_result
    
    def emergency_stop(self, reason):
        """Emergency stop all activities."""
        stop_event = {
            "timestamp": datetime.now().isoformat(),
            "reason": reason,
            "stopped_by": "safety_layer"
        }
        
        self.log_activity("emergency_stop", stop_event)
        logger.critical(f"Emergency stop activated: {reason}")
        
        return stop_event

# Initialize safety layer
safety = SafetyLayer()

@safety_bp.route('/validate', methods=['POST'])
def validate_request():
    """Validate an attack request against safety policies."""
    try:
        data = request.get_json()
        
        validation_result = safety.validate_attack_request(data)
        
        # Log the validation request
        safety.log_activity("validation_request", {
            "request": data,
            "result": validation_result
        })
        
        return jsonify({
            "status": "success",
            "validation": validation_result
        })
        
    except Exception as e:
        logger.error(f"Error validating request: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@safety_bp.route('/authorize', methods=['POST'])
def authorize_target():
    """Authorize a new target for testing."""
    try:
        data = request.get_json()
        
        target_info = data.get('target_info', {})
        authorization_details = data.get('authorization_details', {})
        
        if not target_info or not authorization_details:
            return jsonify({
                "status": "error",
                "message": "target_info and authorization_details are required"
            }), 400
        
        authorization = safety.authorize_target(target_info, authorization_details)
        
        logger.info(f"Authorized new target: {target_info.get('url', 'unknown')}")
        
        return jsonify({
            "status": "success",
            "message": "Target authorized successfully",
            "authorization": authorization
        }), 201
        
    except Exception as e:
        logger.error(f"Error authorizing target: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@safety_bp.route('/authorized-targets', methods=['GET'])
def get_authorized_targets():
    """Get all authorized targets."""
    try:
        return jsonify({
            "status": "success",
            "count": len(safety.authorized_targets),
            "authorized_targets": safety.authorized_targets
        })
    except Exception as e:
        logger.error(f"Error retrieving authorized targets: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@safety_bp.route('/audit-log', methods=['GET'])
def get_audit_log():
    """Get audit log entries."""
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Get paginated results
        log_entries = safety.audit_log[offset:offset + limit]
        
        return jsonify({
            "status": "success",
            "count": len(log_entries),
            "total": len(safety.audit_log),
            "audit_log": log_entries
        })
    except Exception as e:
        logger.error(f"Error retrieving audit log: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@safety_bp.route('/emergency-stop', methods=['POST'])
def emergency_stop():
    """Trigger emergency stop of all activities."""
    try:
        data = request.get_json()
        reason = data.get('reason', 'Manual emergency stop')
        
        stop_event = safety.emergency_stop(reason)
        
        return jsonify({
            "status": "success",
            "message": "Emergency stop activated",
            "stop_event": stop_event
        })
        
    except Exception as e:
        logger.error(f"Error during emergency stop: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@safety_bp.route('/config', methods=['GET'])
def get_safety_config():
    """Get current safety configuration."""
    try:
        return jsonify({
            "status": "success",
            "safety_config": safety.safety_config
        })
    except Exception as e:
        logger.error(f"Error retrieving safety config: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@safety_bp.route('/config', methods=['PUT'])
def update_safety_config():
    """Update safety configuration."""
    try:
        data = request.get_json()
        
        # Update configuration
        for key, value in data.items():
            if key in safety.safety_config:
                safety.safety_config[key] = value
        
        # Log configuration change
        safety.log_activity("config_update", {
            "old_config": safety.safety_config,
            "new_config": data
        })
        
        return jsonify({
            "status": "success",
            "message": "Safety configuration updated",
            "safety_config": safety.safety_config
        })
        
    except Exception as e:
        logger.error(f"Error updating safety config: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
