"""
Knowledge Base Routes - Learning and Data Ingestion Module
Handles the collection, processing, and storage of security knowledge.
"""

from flask import Blueprint, jsonify, request
import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
from openai import OpenAI
from utils.logger import get_logger

knowledge_bp = Blueprint('knowledge', __name__)
logger = get_logger('knowledge_base')

# Initialize OpenAI client
client = OpenAI()

class KnowledgeBase:
    """Knowledge base for storing and retrieving security information."""
    
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        self.techniques_file = os.path.join(self.data_dir, 'techniques.json')
        self.vulnerabilities_file = os.path.join(self.data_dir, 'vulnerabilities.json')
        self.load_data()
    
    def load_data(self):
        """Load existing data from files."""
        try:
            with open(self.techniques_file, 'r') as f:
                self.techniques = json.load(f)
        except FileNotFoundError:
            self.techniques = []
            
        try:
            with open(self.vulnerabilities_file, 'r') as f:
                self.vulnerabilities = json.load(f)
        except FileNotFoundError:
            self.vulnerabilities = []
    
    def save_data(self):
        """Save data to files."""
        with open(self.techniques_file, 'w') as f:
            json.dump(self.techniques, f, indent=2)
        
        with open(self.vulnerabilities_file, 'w') as f:
            json.dump(self.vulnerabilities, f, indent=2)
    
    def add_technique(self, technique_data):
        """Add a new technique to the knowledge base."""
        technique_data['id'] = len(self.techniques) + 1
        technique_data['timestamp'] = datetime.now().isoformat()
        self.techniques.append(technique_data)
        self.save_data()
        return technique_data
    
    def add_vulnerability(self, vuln_data):
        """Add a new vulnerability to the knowledge base."""
        vuln_data['id'] = len(self.vulnerabilities) + 1
        vuln_data['timestamp'] = datetime.now().isoformat()
        self.vulnerabilities.append(vuln_data)
        self.save_data()
        return vuln_data
    
    def search_techniques(self, query):
        """Search techniques by keyword."""
        results = []
        query_lower = query.lower()
        for technique in self.techniques:
            if (query_lower in technique.get('name', '').lower() or 
                query_lower in technique.get('description', '').lower() or
                query_lower in ' '.join(technique.get('tags', [])).lower()):
                results.append(technique)
        return results

# Initialize knowledge base
kb = KnowledgeBase()

@knowledge_bp.route('/techniques', methods=['GET'])
def get_techniques():
    """Get all techniques from the knowledge base."""
    try:
        return jsonify({
            "status": "success",
            "count": len(kb.techniques),
            "techniques": kb.techniques
        })
    except Exception as e:
        logger.error(f"Error retrieving techniques: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@knowledge_bp.route('/techniques', methods=['POST'])
def add_technique():
    """Add a new technique to the knowledge base."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'description', 'category']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "status": "error", 
                    "message": f"Missing required field: {field}"
                }), 400
        
        technique = kb.add_technique(data)
        logger.info(f"Added new technique: {technique['name']}")
        
        return jsonify({
            "status": "success",
            "message": "Technique added successfully",
            "technique": technique
        }), 201
        
    except Exception as e:
        logger.error(f"Error adding technique: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@knowledge_bp.route('/techniques/search', methods=['GET'])
def search_techniques():
    """Search techniques by query."""
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({
                "status": "error",
                "message": "Query parameter 'q' is required"
            }), 400
        
        results = kb.search_techniques(query)
        
        return jsonify({
            "status": "success",
            "query": query,
            "count": len(results),
            "results": results
        })
        
    except Exception as e:
        logger.error(f"Error searching techniques: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@knowledge_bp.route('/learn/url', methods=['POST'])
def learn_from_url():
    """Learn new techniques from a given URL."""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({
                "status": "error",
                "message": "URL is required"
            }), 400
        
        # Fetch content from URL
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Parse HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract text content
        text_content = soup.get_text()
        
        # Use AI to analyze and extract security techniques
        prompt = f"""
        Analyze the following security-related content and extract any hacking techniques, vulnerabilities, or security methods mentioned. 
        Return the information in JSON format with the following structure:
        {{
            "techniques": [
                {{
                    "name": "technique name",
                    "description": "detailed description",
                    "category": "category (e.g., injection, social_engineering, etc.)",
                    "severity": "low/medium/high/critical",
                    "tags": ["tag1", "tag2"],
                    "source_url": "{url}"
                }}
            ]
        }}
        
        Content to analyze:
        {text_content[:4000]}  # Limit content to avoid token limits
        """
        
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are a cybersecurity expert analyzing security content."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        # Parse AI response
        ai_response = response.choices[0].message.content
        
        try:
            # Extract JSON from response
            start_idx = ai_response.find('{')
            end_idx = ai_response.rfind('}') + 1
            json_str = ai_response[start_idx:end_idx]
            extracted_data = json.loads(json_str)
            
            # Add techniques to knowledge base
            added_techniques = []
            for technique_data in extracted_data.get('techniques', []):
                technique = kb.add_technique(technique_data)
                added_techniques.append(technique)
            
            logger.info(f"Learned {len(added_techniques)} techniques from {url}")
            
            return jsonify({
                "status": "success",
                "message": f"Successfully learned {len(added_techniques)} techniques",
                "techniques": added_techniques,
                "source_url": url
            })
            
        except json.JSONDecodeError:
            logger.error(f"Failed to parse AI response as JSON: {ai_response}")
            return jsonify({
                "status": "error",
                "message": "Failed to parse extracted techniques"
            }), 500
        
    except requests.RequestException as e:
        logger.error(f"Error fetching URL {url}: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to fetch URL: {str(e)}"
        }), 400
        
    except Exception as e:
        logger.error(f"Error learning from URL: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@knowledge_bp.route('/vulnerabilities', methods=['GET'])
def get_vulnerabilities():
    """Get all vulnerabilities from the knowledge base."""
    try:
        return jsonify({
            "status": "success",
            "count": len(kb.vulnerabilities),
            "vulnerabilities": kb.vulnerabilities
        })
    except Exception as e:
        logger.error(f"Error retrieving vulnerabilities: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@knowledge_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get knowledge base statistics."""
    try:
        return jsonify({
            "status": "success",
            "stats": {
                "total_techniques": len(kb.techniques),
                "total_vulnerabilities": len(kb.vulnerabilities),
                "categories": list(set([t.get('category', 'unknown') for t in kb.techniques])),
                "last_updated": max([t.get('timestamp', '') for t in kb.techniques] + ['']) if kb.techniques else None
            }
        })
    except Exception as e:
        logger.error(f"Error retrieving stats: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
