import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Home, Plus, Users, Search, ChevronDown, ChevronUp, MapPin, Mail, Phone, Edit2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter
} from '@/components/ui/dialog';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

export default function HouseholdsPage() {
  const { tenant } = useOutletContext();
  const [households, setHouseholds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [expandedId, setExpandedId] = useState(null);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ household_name: '', address: { street: '', city: '', state: '', zip: '' } });

  const token = localStorage.getItem('session_token');
  const authHeaders = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };

  useEffect(() => { fetchHouseholds(); }, []);

  const fetchHouseholds = async () => {
    try {
      const res = await fetch(`${API_URL}/admin/households`, { headers: authHeaders });
      if (res.ok) {
        const data = await res.json();
        setHouseholds(data.households || []);
      }
    } catch (err) {
      console.error('Failed to fetch households:', err);
    } finally {
      setLoading(false);
    }
  };

  const createHousehold = async () => {
    if (!form.household_name) { toast.error('Household name is required'); return; }
    try {
      const res = await fetch(`${API_URL}/admin/households`, {
        method: 'POST', headers: authHeaders,
        body: JSON.stringify(form),
      });
      if (res.ok) {
        toast.success('Household created');
        setShowCreate(false);
        setForm({ household_name: '', address: { street: '', city: '', state: '', zip: '' } });
        fetchHouseholds();
      }
    } catch (err) { toast.error('Failed to create household'); }
  };

  const filtered = households.filter(h =>
    (h.household_name || '').toLowerCase().includes(search.toLowerCase())
  );

  const getInitials = (name) => {
    if (!name) return '?';
    return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
  };

  const formatAddress = (addr) => {
    if (!addr || typeof addr !== 'object') return null;
    const parts = [addr.street, addr.city, addr.state, addr.zip].filter(Boolean);
    return parts.length > 0 ? parts.join(', ') : null;
  };

  if (loading) {
    return (
      <div className="animate-pulse space-y-6" data-testid="households-loading">
        <div className="h-8 bg-slate-200 rounded w-64" />
        <div className="h-64 bg-slate-200 rounded-lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="households-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Households</h1>
          <p className="page-subtitle">Manage family units, addresses, and household connections</p>
        </div>
        <Button className="btn-primary" onClick={() => setShowCreate(true)} data-testid="create-household-btn">
          <Plus className="w-4 h-4 mr-2" />
          New Household
        </Button>
      </div>

      {/* Search & Stats */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <Input
            placeholder="Search households..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
            data-testid="households-search"
          />
        </div>
        <div className="flex items-center gap-4">
          <Badge variant="secondary" data-testid="households-count">
            <Home className="w-3.5 h-3.5 mr-1" />
            {filtered.length} household{filtered.length !== 1 ? 's' : ''}
          </Badge>
        </div>
      </div>

      {/* Households List */}
      {filtered.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center" data-testid="households-empty">
          <Home className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-900 mb-1">
            {search ? 'No matching households' : 'No households yet'}
          </h3>
          <p className="text-sm text-slate-500 mb-4">
            {search ? 'Try a different search term.' : 'Create a household to group family members together.'}
          </p>
          {!search && (
            <Button className="btn-primary" onClick={() => setShowCreate(true)} data-testid="households-empty-create-btn">
              <Plus className="w-4 h-4 mr-2" />
              Create Household
            </Button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-3">
          {filtered.map((h) => {
            const isExpanded = expandedId === h.id;
            const addr = formatAddress(h.address);
            const memberCount = (h.member_ids || []).length;
            return (
              <div
                key={h.id}
                className="bg-white border border-slate-200 rounded-xl overflow-hidden hover:shadow-sm transition-shadow"
                data-testid={`household-card-${h.id}`}
              >
                <button
                  className="w-full flex items-center justify-between p-4 text-left"
                  onClick={() => setExpandedId(isExpanded ? null : h.id)}
                  data-testid={`household-toggle-${h.id}`}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-amber-50 flex items-center justify-center">
                      <Home className="w-5 h-5 text-amber-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-slate-900">{h.household_name || 'Unnamed Household'}</h3>
                      <div className="flex items-center gap-3 text-sm text-slate-500 mt-0.5">
                        <span className="flex items-center gap-1">
                          <Users className="w-3.5 h-3.5" />
                          {memberCount} member{memberCount !== 1 ? 's' : ''}
                        </span>
                        {addr && (
                          <span className="flex items-center gap-1 truncate max-w-[200px]">
                            <MapPin className="w-3.5 h-3.5 flex-shrink-0" />
                            {addr}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {isExpanded ? <ChevronUp className="w-5 h-5 text-slate-400" /> : <ChevronDown className="w-5 h-5 text-slate-400" />}
                  </div>
                </button>

                {isExpanded && (
                  <div className="border-t border-slate-100 p-4 space-y-3" data-testid={`household-details-${h.id}`}>
                    {addr && (
                      <div className="flex items-start gap-2 text-sm text-slate-600">
                        <MapPin className="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0" />
                        <span>{addr}</span>
                      </div>
                    )}

                    <div>
                      <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Members</p>
                      {memberCount === 0 ? (
                        <p className="text-sm text-slate-400">No members linked to this household yet.</p>
                      ) : (
                        <div className="space-y-2">
                          {(h.member_ids || []).map((memberId, idx) => (
                            <div key={memberId} className="flex items-center gap-2 p-2 bg-slate-50 rounded-lg" data-testid={`household-member-${memberId}`}>
                              <Avatar className="w-7 h-7">
                                <AvatarFallback className="bg-blue-100 text-blue-700 text-xs">{idx + 1}</AvatarFallback>
                              </Avatar>
                              <span className="text-sm text-slate-700">{memberId}</span>
                              {h.primary_contact_id === memberId && (
                                <Badge variant="secondary" className="text-xs ml-auto">Primary</Badge>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {h.created_at && (
                      <p className="text-xs text-slate-400">
                        Created {new Date(h.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                      </p>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Create Dialog */}
      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent data-testid="create-household-dialog">
          <DialogHeader>
            <DialogTitle>New Household</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div>
              <Label>Household Name</Label>
              <Input
                placeholder="e.g. The Smith Family"
                value={form.household_name}
                onChange={(e) => setForm({ ...form, household_name: e.target.value })}
                data-testid="household-name-input"
              />
            </div>
            <div>
              <Label>Street Address</Label>
              <Input
                placeholder="123 Main St"
                value={form.address.street}
                onChange={(e) => setForm({ ...form, address: { ...form.address, street: e.target.value } })}
                data-testid="household-street-input"
              />
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <Label>City</Label>
                <Input
                  placeholder="City"
                  value={form.address.city}
                  onChange={(e) => setForm({ ...form, address: { ...form.address, city: e.target.value } })}
                  data-testid="household-city-input"
                />
              </div>
              <div>
                <Label>State</Label>
                <Input
                  placeholder="TX"
                  value={form.address.state}
                  onChange={(e) => setForm({ ...form, address: { ...form.address, state: e.target.value } })}
                  data-testid="household-state-input"
                />
              </div>
              <div>
                <Label>ZIP</Label>
                <Input
                  placeholder="75001"
                  value={form.address.zip}
                  onChange={(e) => setForm({ ...form, address: { ...form.address, zip: e.target.value } })}
                  data-testid="household-zip-input"
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button onClick={createHousehold} data-testid="save-household-btn">Create Household</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
