import { useEffect, useMemo, useState } from 'react';
import { MessageSquare, Search, Filter } from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

export default function LeadershipNotesPage() {
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('All');
  const [tenantFilter, setTenantFilter] = useState(null);

  useEffect(() => {
    const storedTenant = sessionStorage.getItem('impersonate_tenant');
    if (storedTenant) {
      const parsed = JSON.parse(storedTenant);
      setTenantFilter(parsed?.id || null);
    } else {
      setTenantFilter(null);
    }
  }, []);

  const fetchNotes = async () => {
    setLoading(true);
    try {
      const url = tenantFilter ? `${API_URL}/admin/notes?tenant_id=${tenantFilter}` : `${API_URL}/admin/notes`;
      const res = await fetch(url, { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        setNotes(data.notes || []);
      } else {
        toast.error('Failed to load notes');
      }
    } catch (error) {
      toast.error('Failed to load notes');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotes();
  }, [tenantFilter]);

  const categories = useMemo(() => {
    const set = new Set(['All']);
    notes.forEach((note) => {
      if (note.category) set.add(note.category);
    });
    return Array.from(set);
  }, [notes]);

  const filteredNotes = useMemo(() => {
    return notes.filter((note) => {
      const matchesCategory = categoryFilter === 'All' || note.category === categoryFilter;
      const query = searchQuery.toLowerCase();
      const matchesSearch = !query || note.subject?.toLowerCase().includes(query) || note.message?.toLowerCase().includes(query);
      return matchesCategory && matchesSearch;
    });
  }, [notes, categoryFilter, searchQuery]);

  return (
    <div className="notes-admin" data-testid="notes-admin-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Leave a Note</h1>
          <p className="page-subtitle">Review member notes, prayer requests, and leadership messages.</p>
        </div>
      </div>

      <div className="notes-controls" data-testid="notes-controls">
        <div className="notes-search">
          <Search className="w-4 h-4" />
          <input
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            placeholder="Search notes"
            data-testid="notes-search-input"
          />
        </div>
        <div className="notes-filter">
          <Filter className="w-4 h-4" />
          <select
            value={categoryFilter}
            onChange={(event) => setCategoryFilter(event.target.value)}
            data-testid="notes-category-filter"
          >
            {categories.map((category) => (
              <option key={category} value={category}>{category}</option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="notes-empty" data-testid="notes-loading">Loading notes...</div>
      ) : filteredNotes.length === 0 ? (
        <div className="notes-empty" data-testid="notes-empty">No notes yet.</div>
      ) : (
        <div className="notes-grid" data-testid="notes-grid">
          {filteredNotes.map((note) => (
            <div key={note.id} className="note-card" data-testid={`note-${note.id}`}>
              <div className="note-card-header">
                <div>
                  <span className="note-category">{note.category || 'General'}</span>
                  <h3>{note.subject}</h3>
                </div>
                <MessageSquare className="w-4 h-4" />
              </div>
              <p className="note-message">{note.message}</p>
              <div className="note-meta">
                <span>{note.member_name || 'Member'} • {note.member_email || 'member@church.com'}</span>
                {note.tenant_name && <span className="note-tenant">{note.tenant_name}</span>}
                <span>{new Date(note.created_at).toLocaleString()}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
