import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Shield, 
  Brain, 
  Target, 
  AlertTriangle, 
  Activity, 
  Database,
  Zap,
  Lock,
  Eye,
  Settings
} from 'lucide-react';
import './App.css';

const API_BASE_URL = 'http://localhost:5000';

interface Technique {
  id: number;
  name: string;
  description: string;
  category: string;
  severity?: string;
  tags?: string[];
  timestamp?: string;
}

interface AttackPlan {
  id: number;
  target: any;
  objectives: string[];
  status: string;
  timestamp: string;
  phases?: any;
}

interface SafetyConfig {
  require_authorization: boolean;
  log_all_activities: boolean;
  block_unauthorized_targets: boolean;
  max_concurrent_attacks: number;
  emergency_stop_enabled: boolean;
}

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [techniques, setTechniques] = useState<Technique[]>([]);
  const [attackPlans, setAttackPlans] = useState<AttackPlan[]>([]);
  const [safetyConfig, setSafetyConfig] = useState<SafetyConfig | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load initial data
  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [techniquesRes, attacksRes, safetyRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/api/knowledge/techniques`),
        axios.get(`${API_BASE_URL}/api/attack/plans`),
        axios.get(`${API_BASE_URL}/api/safety/config`)
      ]);

      setTechniques(techniquesRes.data.techniques || []);
      setAttackPlans(attacksRes.data.attack_plans || []);
      setSafetyConfig(safetyRes.data.safety_config || null);
    } catch (err) {
      setError('Failed to load dashboard data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const learnFromUrl = async (url: string) => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/api/knowledge/learn/url`, { url });
      alert(`Successfully learned ${response.data.techniques.length} new techniques!`);
      loadDashboardData(); // Refresh data
    } catch (err) {
      setError('Failed to learn from URL');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const createAttackPlan = async (target: any, objectives: string[]) => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/api/attack/plan`, {
        target,
        objectives
      });
      alert('Attack plan created successfully!');
      loadDashboardData(); // Refresh data
    } catch (err) {
      setError('Failed to create attack plan');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const testChatbot = async (url: string, testType: string = 'basic') => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/api/attack/chatbot/test`, {
        url,
        test_type: testType
      });
      
      const results = response.data.results;
      alert(`Chatbot test completed!\nVulnerabilities found: ${results.vulnerabilities_found.length}\nRisk level: ${results.test_summary.risk_level}`);
    } catch (err) {
      setError('Failed to test chatbot');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const emergencyStop = async () => {
    try {
      await axios.post(`${API_BASE_URL}/api/safety/emergency-stop`, {
        reason: 'Manual emergency stop from UI'
      });
      alert('Emergency stop activated!');
    } catch (err) {
      setError('Failed to activate emergency stop');
      console.error(err);
    }
  };

  const renderDashboard = () => (
    <div className="dashboard">
      <div className="stats-grid">
        <div className="stat-card">
          <Database className="stat-icon" />
          <div className="stat-content">
            <h3>Techniques</h3>
            <p className="stat-number">{techniques.length}</p>
          </div>
        </div>
        
        <div className="stat-card">
          <Target className="stat-icon" />
          <div className="stat-content">
            <h3>Attack Plans</h3>
            <p className="stat-number">{attackPlans.length}</p>
          </div>
        </div>
        
        <div className="stat-card">
          <Shield className="stat-icon" />
          <div className="stat-content">
            <h3>Safety Status</h3>
            <p className="stat-status">{safetyConfig?.emergency_stop_enabled ? 'Active' : 'Inactive'}</p>
          </div>
        </div>
        
        <div className="stat-card">
          <Activity className="stat-icon" />
          <div className="stat-content">
            <h3>System Status</h3>
            <p className="stat-status">Operational</p>
          </div>
        </div>
      </div>

      <div className="recent-activity">
        <h3>Recent Techniques</h3>
        <div className="technique-list">
          {techniques.slice(0, 5).map((technique) => (
            <div key={technique.id} className="technique-item">
              <div className="technique-info">
                <h4>{technique.name}</h4>
                <p>{technique.description}</p>
                <span className={`category-badge ${technique.category}`}>
                  {technique.category}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderKnowledgeBase = () => (
    <div className="knowledge-base">
      <div className="section-header">
        <h2>Knowledge Base</h2>
        <div className="actions">
          <button 
            onClick={() => {
              const url = prompt('Enter URL to learn from:');
              if (url) learnFromUrl(url);
            }}
            className="btn-primary"
          >
            Learn from URL</button>
<button onClick={() => learnFromUrl("https://www.egnyte.com/blog/post/ai-chatbot-security-understanding-key-risks-and-testing-best-practices")} className="btn-primary">Learn from Egnyte</button>
        </div>
      </div>

      <div className="techniques-grid">
        {techniques.map((technique) => (
          <div key={technique.id} className="technique-card">
            <div className="technique-header">
              <h3>{technique.name}</h3>
              <span className={`severity-badge ${technique.severity?.toLowerCase()}`}>
                {technique.severity || 'Unknown'}
              </span>
            </div>
            <p className="technique-description">{technique.description}</p>
            <div className="technique-meta">
              <span className="category">{technique.category}</span>
              {technique.tags && (
                <div className="tags">
                  {technique.tags.map((tag, index) => (
                    <span key={index} className="tag">{tag}</span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderAttackEngine = () => (
    <div className="attack-engine">
      <div className="section-header">
        <h2>Attack Engine</h2>
        <div className="actions">
          <button 
            onClick={() => {
              const target = {
                name: prompt('Target name:') || '',
                url: prompt('Target URL:') || '',
                type: 'web_application'
              };
              const objectives = ['Identify vulnerabilities', 'Test security controls'];
              createAttackPlan(target, objectives);
            }}
            className="btn-primary"
          >
            Create Attack Plan
          </button>
        </div>
      </div>

      <div className="chatbot-tester">
        <h3>Chatbot Security Tester</h3>
        <div className="tester-form">
          <input 
            type="url" 
            placeholder="Enter chatbot URL..." 
            id="chatbot-url"
            className="url-input"
          />
          <button 
            onClick={() => {
              const input = document.getElementById('chatbot-url') as HTMLInputElement;
              if (input.value) testChatbot(input.value);
            }}
            className="btn-secondary"
          >
            Test Chatbot
          </button>
        </div>
      </div>

      <div className="attack-plans">
        <h3>Attack Plans</h3>
        <div className="plans-list">
          {attackPlans.map((plan) => (
            <div key={plan.id} className="plan-card">
              <div className="plan-header">
                <h4>Plan #{plan.id}</h4>
                <span className={`status-badge ${plan.status}`}>{plan.status}</span>
              </div>
              <div className="plan-details">
                <p><strong>Target:</strong> {plan.target?.name || 'Unknown'}</p>
                <p><strong>Objectives:</strong> {plan.objectives?.join(', ')}</p>
                <p><strong>Created:</strong> {new Date(plan.timestamp).toLocaleString()}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderSafetyLayer = () => (
    <div className="safety-layer">
      <div className="section-header">
        <h2>Safety Layer</h2>
        <div className="actions">
          <button 
            onClick={emergencyStop}
            className="btn-danger"
          >
            <AlertTriangle size={16} />
            Emergency Stop
          </button>
        </div>
      </div>

      {safetyConfig && (
        <div className="safety-config">
          <h3>Safety Configuration</h3>
          <div className="config-grid">
            <div className="config-item">
              <label>Require Authorization</label>
              <span className={safetyConfig.require_authorization ? 'enabled' : 'disabled'}>
                {safetyConfig.require_authorization ? 'Enabled' : 'Disabled'}
              </span>
            </div>
            <div className="config-item">
              <label>Log All Activities</label>
              <span className={safetyConfig.log_all_activities ? 'enabled' : 'disabled'}>
                {safetyConfig.log_all_activities ? 'Enabled' : 'Disabled'}
              </span>
            </div>
            <div className="config-item">
              <label>Block Unauthorized Targets</label>
              <span className={safetyConfig.block_unauthorized_targets ? 'enabled' : 'disabled'}>
                {safetyConfig.block_unauthorized_targets ? 'Enabled' : 'Disabled'}
              </span>
            </div>
            <div className="config-item">
              <label>Max Concurrent Attacks</label>
              <span>{safetyConfig.max_concurrent_attacks}</span>
            </div>
            <div className="config-item">
              <label>Emergency Stop</label>
              <span className={safetyConfig.emergency_stop_enabled ? 'enabled' : 'disabled'}>
                {safetyConfig.emergency_stop_enabled ? 'Enabled' : 'Disabled'}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className="App">
      <header className="app-header">
        <div className="header-content">
          <div className="logo">
            <Shield className="logo-icon" />
            <h1>RedHat AI Security Agent</h1>
          </div>
          <nav className="nav-tabs">
            <button 
              className={activeTab === 'dashboard' ? 'active' : ''}
              onClick={() => setActiveTab('dashboard')}
            >
              <Activity size={16} />
              Dashboard
            </button>
            <button 
              className={activeTab === 'knowledge' ? 'active' : ''}
              onClick={() => setActiveTab('knowledge')}
            >
              <Brain size={16} />
              Knowledge Base
            </button>
            <button 
              className={activeTab === 'attack' ? 'active' : ''}
              onClick={() => setActiveTab('attack')}
            >
              <Zap size={16} />
              Attack Engine
            </button>
            <button 
              className={activeTab === 'safety' ? 'active' : ''}
              onClick={() => setActiveTab('safety')}
            >
              <Lock size={16} />
              Safety Layer
            </button>
          </nav>
        </div>
      </header>

      <main className="app-main">
        {loading && <div className="loading">Loading...</div>}
        {error && <div className="error">{error}</div>}
        
        {activeTab === 'dashboard' && renderDashboard()}
        {activeTab === 'knowledge' && renderKnowledgeBase()}
        {activeTab === 'attack' && renderAttackEngine()}
        {activeTab === 'safety' && renderSafetyLayer()}
      </main>
    </div>
  );
}

export default App;
