import { useEffect, useState } from 'react';
import { Key, Plus, Copy, Trash2, Shield, Eye, EyeOff, AlertTriangle, Check, ExternalLink, Code, BookOpen } from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

export default function DeveloperAPIPage() {
  const [apiKeys, setApiKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newKeyResult, setNewKeyResult] = useState(null);
  const [availablePermissions, setAvailablePermissions] = useState({});
  const [formData, setFormData] = useState({
    name: '',
    permissions: ['members:read', 'events:read', 'groups:read'],
    rate_limit: 1000,
    expires_in_days: null
  });

  const fetchApiKeys = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/admin/api-keys`);
      if (res.ok) {
        const data = await res.json();
        setApiKeys(data.api_keys || []);
        setAvailablePermissions(data.available_permissions || {});
      }
    } catch (error) {
      toast.error('Failed to load API keys');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApiKeys();
  }, []);

  const createApiKey = async () => {
    try {
      const res = await fetch(`${API_URL}/admin/api-keys`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        
        body: JSON.stringify(formData)
      });
      if (res.ok) {
        const data = await res.json();
        setNewKeyResult(data);
        toast.success('API key created!');
        fetchApiKeys();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Failed to create API key');
      }
    } catch (error) {
      toast.error('Failed to create API key');
    }
  };

  const revokeApiKey = async (keyId) => {
    if (!confirm('Are you sure you want to revoke this API key? This cannot be undone.')) return;
    try {
      const res = await fetch(`${API_URL}/admin/api-keys/${keyId}`, {
        method: 'DELETE',
        
      });
      if (res.ok) {
        toast.success('API key revoked');
        fetchApiKeys();
      } else {
        toast.error('Failed to revoke API key');
      }
    } catch (error) {
      toast.error('Failed to revoke API key');
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!');
  };

  const togglePermission = (perm) => {
    setFormData(prev => ({
      ...prev,
      permissions: prev.permissions.includes(perm)
        ? prev.permissions.filter(p => p !== perm)
        : [...prev.permissions, perm]
    }));
  };

  return (
    <div className="developer-api-page" data-testid="developer-api-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Developer API</h1>
          <p className="page-subtitle">Generate API keys for external agents and integrations to access your church data.</p>
        </div>
        <button 
          className="btn-primary"
          onClick={() => { setShowCreateModal(true); setNewKeyResult(null); }}
          data-testid="create-api-key-btn"
        >
          <Plus className="w-4 h-4" /> Create API Key
        </button>
      </div>

      {/* Quick Start Guide */}
      <div className="api-quickstart" data-testid="api-quickstart">
        <div className="api-quickstart-header">
          <BookOpen className="w-5 h-5" />
          <h3>Quick Start Guide</h3>
        </div>
        <div className="api-quickstart-content">
          <div className="api-quickstart-step">
            <span className="step-number">1</span>
            <div>
              <strong>Create an API Key</strong>
              <p>Generate a key with the permissions your agent needs.</p>
            </div>
          </div>
          <div className="api-quickstart-step">
            <span className="step-number">2</span>
            <div>
              <strong>Test the Connection</strong>
              <p>Use the <code>/api/v1/agent/scout</code> endpoint to verify.</p>
            </div>
          </div>
          <div className="api-quickstart-step">
            <span className="step-number">3</span>
            <div>
              <strong>Connect Your Agent</strong>
              <p>Use the key in your MoltBot, OpenClaw, or custom agent.</p>
            </div>
          </div>
        </div>
        <a 
          href={`${API_URL}/v1/agent/docs`} 
          target="_blank" 
          rel="noopener noreferrer"
          className="api-docs-link"
        >
          <Code className="w-4 h-4" /> View API Documentation <ExternalLink className="w-3 h-3" />
        </a>
      </div>

      {/* API Keys List */}
      <div className="api-keys-section" data-testid="api-keys-list">
        <h3><Key className="w-4 h-4" /> Your API Keys</h3>
        
        {loading ? (
          <div className="api-loading">Loading API keys...</div>
        ) : apiKeys.length === 0 ? (
          <div className="api-empty">
            <Key className="w-8 h-8" />
            <p>No API keys yet. Create one to get started!</p>
          </div>
        ) : (
          <div className="api-keys-grid">
            {apiKeys.map((key) => (
              <div 
                key={key.id} 
                className={`api-key-card ${!key.is_active ? 'revoked' : ''}`}
                data-testid={`api-key-${key.id}`}
              >
                <div className="api-key-header">
                  <div className="api-key-name">
                    <Key className="w-4 h-4" />
                    <span>{key.name}</span>
                  </div>
                  <span className={`api-key-status ${key.is_active ? 'active' : 'revoked'}`}>
                    {key.is_active ? 'Active' : 'Revoked'}
                  </span>
                </div>
                
                <div className="api-key-prefix">
                  <code>{key.key_prefix}</code>
                  <button onClick={() => copyToClipboard(key.key_prefix)} title="Copy prefix">
                    <Copy className="w-3 h-3" />
                  </button>
                </div>
                
                <div className="api-key-permissions">
                  {key.permissions.slice(0, 4).map(p => (
                    <span key={p} className="permission-badge">{p}</span>
                  ))}
                  {key.permissions.length > 4 && (
                    <span className="permission-badge more">+{key.permissions.length - 4}</span>
                  )}
                </div>
                
                <div className="api-key-meta">
                  <span>Rate: {key.rate_limit}/hr</span>
                  <span>Used: {key.usage_count} times</span>
                </div>
                
                {key.is_active && (
                  <button 
                    className="api-key-revoke"
                    onClick={() => revokeApiKey(key.id)}
                    data-testid={`revoke-key-${key.id}`}
                  >
                    <Trash2 className="w-4 h-4" /> Revoke
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="api-modal-overlay" onClick={() => !newKeyResult && setShowCreateModal(false)}>
          <div className="api-modal" onClick={e => e.stopPropagation()} data-testid="create-api-key-modal">
            {!newKeyResult ? (
              <>
                <h2>Create API Key</h2>
                <p className="api-modal-desc">Configure permissions for your external agent.</p>
                
                <div className="api-form-group">
                  <label>Key Name</label>
                  <input
                    type="text"
                    placeholder="e.g., MoltBot Production"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    data-testid="api-key-name-input"
                  />
                </div>
                
                <div className="api-form-group">
                  <label>Permissions</label>
                  <div className="permissions-grid">
                    {Object.entries(availablePermissions).map(([perm, desc]) => (
                      <label key={perm} className="permission-checkbox">
                        <input
                          type="checkbox"
                          checked={formData.permissions.includes(perm)}
                          onChange={() => togglePermission(perm)}
                        />
                        <div>
                          <span className="perm-name">{perm}</span>
                          <span className="perm-desc">{desc}</span>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>
                
                <div className="api-form-row">
                  <div className="api-form-group">
                    <label>Rate Limit (requests/hour)</label>
                    <input
                      type="number"
                      value={formData.rate_limit}
                      onChange={(e) => setFormData({ ...formData, rate_limit: parseInt(e.target.value) || 1000 })}
                    />
                  </div>
                  <div className="api-form-group">
                    <label>Expires In (days)</label>
                    <input
                      type="number"
                      placeholder="Never"
                      value={formData.expires_in_days || ''}
                      onChange={(e) => setFormData({ ...formData, expires_in_days: e.target.value ? parseInt(e.target.value) : null })}
                    />
                  </div>
                </div>
                
                <div className="api-modal-actions">
                  <button className="btn-secondary" onClick={() => setShowCreateModal(false)}>Cancel</button>
                  <button 
                    className="btn-primary" 
                    onClick={createApiKey}
                    disabled={!formData.name}
                    data-testid="create-api-key-submit"
                  >
                    <Key className="w-4 h-4" /> Generate Key
                  </button>
                </div>
              </>
            ) : (
              <div className="api-key-created" data-testid="api-key-created">
                <div className="api-key-created-icon">
                  <Check className="w-8 h-8" />
                </div>
                <h2>API Key Created!</h2>
                
                <div className="api-key-warning">
                  <AlertTriangle className="w-5 h-5" />
                  <p>Copy this key now. It will not be shown again!</p>
                </div>
                
                <div className="api-key-display">
                  <code data-testid="new-api-key-value">{newKeyResult.api_key}</code>
                  <button onClick={() => copyToClipboard(newKeyResult.api_key)}>
                    <Copy className="w-4 h-4" /> Copy
                  </button>
                </div>
                
                <div className="api-key-created-info">
                  <p><strong>Name:</strong> {newKeyResult.name}</p>
                  <p><strong>Permissions:</strong> {newKeyResult.permissions.join(', ')}</p>
                  <p><strong>Rate Limit:</strong> {newKeyResult.rate_limit} requests/hour</p>
                  {newKeyResult.expires_at && <p><strong>Expires:</strong> {new Date(newKeyResult.expires_at).toLocaleDateString()}</p>}
                </div>
                
                <button className="btn-primary" onClick={() => setShowCreateModal(false)}>
                  Done
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
