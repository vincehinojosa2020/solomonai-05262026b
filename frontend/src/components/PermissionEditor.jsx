import { useState, useEffect } from 'react';
import { Shield, Save, RotateCcw, Loader2, AlertTriangle, CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

const PERMISSION_GROUPS = [
  {
    title: 'Member Access',
    permissions: [
      { key: 'member.home', label: 'Home' },
      { key: 'member.giving', label: 'Give' },
      { key: 'member.kids', label: 'Kids' },
      { key: 'member.watch', label: 'Watch' },
      { key: 'member.merch', label: 'Merch' },
      { key: 'member.cafe', label: 'Cafe' },
      { key: 'member.groups', label: 'Groups' },
      { key: 'member.events', label: 'Events' },
      { key: 'member.prayer', label: 'Prayer' },
      { key: 'member.volunteer', label: 'Volunteer' },
    ],
  },
  {
    title: 'Ministry Tools',
    permissions: [
      { key: 'admin.dashboard', label: 'Dashboard' },
      { key: 'admin.members.view', label: 'View Members' },
      { key: 'admin.members.edit', label: 'Edit Members' },
      { key: 'admin.kids.manage', label: 'Kids Check-In' },
      { key: 'admin.media.upload', label: 'Upload Media' },
      { key: 'admin.groups.manage', label: 'Manage Groups' },
      { key: 'admin.groups.leader', label: 'Group Leader' },
      { key: 'admin.events.create', label: 'Create Events' },
      { key: 'admin.communications', label: 'Announcements' },
      { key: 'admin.volunteers.manage', label: 'Volunteers' },
      { key: 'admin.geofence', label: 'Geofence' },
      { key: 'admin.communications.send', label: 'Communications' },
    ],
  },
  {
    title: 'Financial',
    permissions: [
      { key: 'admin.giving', label: 'View Giving' },
      { key: 'admin.giving.process', label: 'Process Giving' },
      { key: 'admin.cafe.manage', label: 'Cafe Mgmt' },
      { key: 'admin.merch.manage', label: 'Merch Mgmt' },
      { key: 'admin.reports', label: 'View Reports' },
      { key: 'admin.reports.export', label: 'Export Reports' },
    ],
  },
  {
    title: 'Administrative',
    permissions: [
      { key: 'admin.users.create', label: 'Create Users' },
      { key: 'admin.roles.assign', label: 'Assign Roles' },
      { key: 'admin.settings', label: 'Settings' },
    ],
  },
];

export default function PermissionEditor({ userId, userName }) {
  const [permissions, setPermissions] = useState([]);
  const [role, setRole] = useState('');
  const [templates, setTemplates] = useState({});
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [isCustom, setIsCustom] = useState(false);
  const [originalPerms, setOriginalPerms] = useState([]);

  useEffect(() => {
    if (userId) {
      loadData();
    }
  }, [userId]);

  const loadData = async () => {
    setLoading(true);
    try {
      const token = sessionStorage.getItem('session_token');
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};

      const [permsRes, templatesRes] = await Promise.all([
        fetch(`${API_URL}/admin/members/${userId}/permissions`, { headers }),
        fetch(`${API_URL}/admin/roles/templates`, { headers }),
      ]);

      if (permsRes.ok) {
        const data = await permsRes.json();
        setPermissions(data.permissions || []);
        setOriginalPerms(data.permissions || []);
        setRole(data.role || '');
        setSelectedTemplate(data.role || '');
      }

      if (templatesRes.ok) {
        const data = await templatesRes.json();
        setTemplates(data.templates || {});
      }
    } catch (err) {
      toast.error('Failed to load permissions');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedTemplate && templates[selectedTemplate]) {
      const templatePerms = templates[selectedTemplate].permissions || [];
      const isSame = templatePerms.length === permissions.length && templatePerms.every(p => permissions.includes(p));
      setIsCustom(!isSame);
    }
  }, [permissions, selectedTemplate, templates]);

  const handleTemplateChange = (tmpl) => {
    setSelectedTemplate(tmpl);
    if (templates[tmpl]) {
      setPermissions([...(templates[tmpl].permissions || [])]);
    }
  };

  const togglePermission = (perm) => {
    setPermissions(prev =>
      prev.includes(perm) ? prev.filter(p => p !== perm) : [...prev, perm]
    );
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const token = sessionStorage.getItem('session_token');
      const headers = { 'Content-Type': 'application/json', ...(token ? { 'Authorization': `Bearer ${token}` } : {}) };

      // Update role if template changed
      if (selectedTemplate !== role) {
        await fetch(`${API_URL}/admin/members/${userId}/role`, {
          method: 'PUT', headers,
          body: JSON.stringify({ role_template: selectedTemplate }),
        });
      }

      // Update permissions
      const res = await fetch(`${API_URL}/admin/members/${userId}/permissions`, {
        method: 'PUT', headers,
        body: JSON.stringify({ permissions }),
      });

      if (res.ok) {
        setOriginalPerms([...permissions]);
        setRole(selectedTemplate);
        toast.success('Permissions saved');
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Failed to save');
      }
    } catch (err) {
      toast.error('Network error');
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    if (templates[selectedTemplate]) {
      setPermissions([...(templates[selectedTemplate].permissions || [])]);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const hasChanges = JSON.stringify([...permissions].sort()) !== JSON.stringify([...originalPerms].sort()) || selectedTemplate !== role;

  return (
    <div className="space-y-6" data-testid="permission-editor">
      {/* Role Template */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="flex-1 min-w-[200px]">
          <label className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1 block">Role Template</label>
          <select
            value={selectedTemplate}
            onChange={e => handleTemplateChange(e.target.value)}
            className="w-full h-10 rounded-lg border border-slate-300 px-3 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            data-testid="role-template-select"
          >
            {Object.entries(templates).map(([key, tmpl]) => (
              <option key={key} value={key}>{tmpl.title || key}</option>
            ))}
          </select>
        </div>
        {isCustom && (
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-50 border border-amber-200 rounded-lg">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
            <span className="text-xs font-medium text-amber-700">Custom — differs from template</span>
          </div>
        )}
      </div>

      {/* Permission Grid */}
      {PERMISSION_GROUPS.map((group) => (
        <div key={group.title} className="space-y-3">
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{group.title}</h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2">
            {group.permissions.map((perm) => {
              const checked = permissions.includes(perm.key);
              return (
                <label
                  key={perm.key}
                  className={`flex items-center gap-2 p-2.5 rounded-lg border cursor-pointer transition-all text-sm ${
                    checked
                      ? 'bg-blue-50 border-blue-200 text-blue-800'
                      : 'bg-white border-slate-200 text-slate-500 hover:border-slate-300'
                  }`}
                  data-testid={`perm-${perm.key}`}
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => togglePermission(perm.key)}
                    className="w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="font-medium">{perm.label}</span>
                </label>
              );
            })}
          </div>
        </div>
      ))}

      {/* Actions */}
      <div className="flex items-center justify-between pt-4 border-t border-slate-200">
        <div className="text-xs text-slate-400">
          {permissions.length} permission{permissions.length !== 1 ? 's' : ''} assigned
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={handleReset} data-testid="perm-reset">
            <RotateCcw className="w-3.5 h-3.5 mr-1.5" /> Reset to Template
          </Button>
          <Button size="sm" onClick={handleSave} disabled={saving || !hasChanges} data-testid="perm-save">
            {saving ? <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" /> : <Save className="w-3.5 h-3.5 mr-1.5" />}
            Save Changes
          </Button>
        </div>
      </div>
    </div>
  );
}
