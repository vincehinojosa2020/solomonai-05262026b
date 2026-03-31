import { useState, useEffect, useMemo } from 'react';
import {
  Music, Plus, Search, Edit, Trash2, Loader2, Hash, Clock, Tag,
  ChevronDown, BookOpen, X
} from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from '@/components/ui/dialog';

const MUSICAL_KEYS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B',
  'Cm', 'C#m', 'Dm', 'D#m', 'Em', 'Fm', 'F#m', 'Gm', 'G#m', 'Am', 'A#m', 'Bm'];

export default function SongLibraryPage() {
  const [songs, setSongs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [showEditor, setShowEditor] = useState(false);
  const [showLyrics, setShowLyrics] = useState(null);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({
    title: '', artist: '', ccli_number: '', default_key: 'G', bpm: '', lyrics: '', tags: []
  });

  const token = sessionStorage.getItem('session_token');
  const authHeaders = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };

  const fetchSongs = async (q) => {
    try {
      const params = q ? `?search=${encodeURIComponent(q)}` : '';
      const res = await fetch(`${API_URL}/admin/songs${params}`, { headers: authHeaders });
      if (res.ok) { const d = await res.json(); setSongs(d.songs || []); }
    } catch {} finally { setLoading(false); }
  };

  useEffect(() => { fetchSongs(searchQuery); }, [searchQuery]);

  const saveSong = async () => {
    if (!form.title) { toast.error('Song title is required'); return; }
    const url = editing ? `${API_URL}/admin/songs/${editing}` : `${API_URL}/admin/songs`;
    try {
      const res = await fetch(url, {
        method: editing ? 'PUT' : 'POST', headers: authHeaders,
        body: JSON.stringify({ ...form, bpm: form.bpm ? parseInt(form.bpm) : null })
      });
      if (res.ok) {
        toast.success(editing ? 'Song updated' : 'Song added to library');
        setShowEditor(false); setEditing(null); resetForm(); fetchSongs(searchQuery);
      }
    } catch { toast.error('Failed to save song'); }
  };

  const deleteSong = async (id) => {
    if (!confirm('Delete this song?')) return;
    try {
      await fetch(`${API_URL}/admin/songs/${id}`, { method: 'DELETE', headers: authHeaders });
      toast.success('Song deleted'); fetchSongs(searchQuery);
    } catch { toast.error('Failed to delete'); }
  };

  const openEdit = (song) => {
    setForm({
      title: song.title, artist: song.artist || '', ccli_number: song.ccli_number || '',
      default_key: song.default_key || 'G', bpm: song.bpm || '', lyrics: song.lyrics || '',
      tags: song.tags || []
    });
    setEditing(song.id); setShowEditor(true);
  };

  const resetForm = () => {
    setForm({ title: '', artist: '', ccli_number: '', default_key: 'G', bpm: '', lyrics: '', tags: [] });
  };

  return (
    <div className="page-container" data-testid="song-library-page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 800, color: '#0f172a', letterSpacing: '-0.02em' }}>Song Library</h1>
          <p style={{ fontSize: 14, color: '#64748b', marginTop: 4 }}>
            {songs.length} songs in your worship library
          </p>
        </div>
        <Button onClick={() => { resetForm(); setEditing(null); setShowEditor(true); }} data-testid="add-song-btn">
          <Plus className="w-4 h-4 mr-2" /> Add Song
        </Button>
      </div>

      {/* Search */}
      <div style={{ position: 'relative', marginBottom: 20 }}>
        <Search className="w-4 h-4" style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} />
        <input
          data-testid="song-search"
          type="text" placeholder="Search by title or artist..."
          value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
          style={{ width: '100%', padding: '12px 14px 12px 40px', border: '1px solid #e5e7eb', borderRadius: 10, fontSize: 14, outline: 'none' }}
        />
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 60 }}><Loader2 className="w-6 h-6 animate-spin" style={{ margin: '0 auto', color: '#64748b' }} /></div>
      ) : songs.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 60, color: '#94a3b8' }}>
          <Music className="w-10 h-10" style={{ margin: '0 auto 12px' }} />
          <p style={{ fontSize: 15, fontWeight: 600 }}>No songs in your library</p>
          <p style={{ fontSize: 13, marginTop: 4 }}>Add your first worship song to get started</p>
        </div>
      ) : (
        <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 14, overflow: 'hidden' }}>
          {/* Table header */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 180px 100px 80px 80px 120px', padding: '12px 20px', background: '#f8fafc', borderBottom: '1px solid #e5e7eb', fontSize: 11, fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            <span>Title</span><span>Artist</span><span>Key</span><span>BPM</span><span>CCLI</span><span></span>
          </div>
          {songs.map(song => (
            <div key={song.id} data-testid={`song-${song.id}`}
              style={{ display: 'grid', gridTemplateColumns: '1fr 180px 100px 80px 80px 120px', padding: '14px 20px', borderBottom: '1px solid #f1f5f9', alignItems: 'center', transition: 'background 0.1s' }}>
              <div>
                <p style={{ fontSize: 14, fontWeight: 600, color: '#0f172a' }}>{song.title}</p>
                <div style={{ display: 'flex', gap: 4, marginTop: 3 }}>
                  {(song.tags || []).map(t => (
                    <span key={t} style={{ fontSize: 10, padding: '1px 6px', background: '#f1f5f9', borderRadius: 4, color: '#64748b' }}>{t}</span>
                  ))}
                </div>
              </div>
              <span style={{ fontSize: 13, color: '#64748b' }}>{song.artist}</span>
              <span style={{ fontSize: 13, fontWeight: 600, color: '#0f172a', fontFamily: 'monospace' }}>{song.default_key}</span>
              <span style={{ fontSize: 13, color: '#64748b', fontFamily: 'monospace' }}>{song.bpm || '-'}</span>
              <span style={{ fontSize: 11, color: '#94a3b8', fontFamily: 'monospace' }}>{song.ccli_number || '-'}</span>
              <div style={{ display: 'flex', gap: 4, justifyContent: 'flex-end' }}>
                {song.lyrics && (
                  <Button size="sm" variant="outline" onClick={() => setShowLyrics(song)} title="View lyrics">
                    <BookOpen className="w-3.5 h-3.5" />
                  </Button>
                )}
                <Button size="sm" variant="outline" onClick={() => openEdit(song)}>
                  <Edit className="w-3.5 h-3.5" />
                </Button>
                <Button size="sm" variant="outline" onClick={() => deleteSong(song.id)} className="text-red-500 hover:text-red-700">
                  <Trash2 className="w-3.5 h-3.5" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Song Editor Dialog */}
      <Dialog open={showEditor} onOpenChange={setShowEditor}>
        <DialogContent className="sm:max-w-[560px]" style={{ maxHeight: '85vh', overflowY: 'auto' }}>
          <DialogHeader>
            <DialogTitle>{editing ? 'Edit Song' : 'Add Song'}</DialogTitle>
            <DialogDescription>Add song details for your worship library</DialogDescription>
          </DialogHeader>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14, marginTop: 8 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              <div>
                <label className="form-label">Title *</label>
                <input className="form-input" value={form.title} data-testid="song-title-input"
                  onChange={e => setForm({ ...form, title: e.target.value })} placeholder="How Great Is Our God" />
              </div>
              <div>
                <label className="form-label">Artist</label>
                <input className="form-input" value={form.artist}
                  onChange={e => setForm({ ...form, artist: e.target.value })} placeholder="Chris Tomlin" />
              </div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}>
              <div>
                <label className="form-label">Key</label>
                <select className="form-input" value={form.default_key}
                  onChange={e => setForm({ ...form, default_key: e.target.value })}>
                  {MUSICAL_KEYS.map(k => <option key={k} value={k}>{k}</option>)}
                </select>
              </div>
              <div>
                <label className="form-label">BPM</label>
                <input className="form-input" type="number" value={form.bpm}
                  onChange={e => setForm({ ...form, bpm: e.target.value })} placeholder="120" />
              </div>
              <div>
                <label className="form-label">CCLI #</label>
                <input className="form-input" value={form.ccli_number}
                  onChange={e => setForm({ ...form, ccli_number: e.target.value })} placeholder="1234567" />
              </div>
            </div>
            <div>
              <label className="form-label">Lyrics / Chord Chart</label>
              <textarea className="form-input" rows={8} value={form.lyrics}
                onChange={e => setForm({ ...form, lyrics: e.target.value })}
                placeholder="Paste lyrics or chord chart here..."
                style={{ fontFamily: "'SF Mono', 'Fira Code', monospace", fontSize: 13, lineHeight: 1.6 }} />
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 4 }}>
              <Button variant="outline" onClick={() => { setShowEditor(false); setEditing(null); }}>Cancel</Button>
              <Button onClick={saveSong} data-testid="save-song-btn">
                {editing ? 'Update Song' : 'Add Song'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Lyrics Viewer Dialog */}
      <Dialog open={!!showLyrics} onOpenChange={() => setShowLyrics(null)}>
        <DialogContent className="sm:max-w-[500px]" style={{ maxHeight: '85vh', overflowY: 'auto' }}>
          <DialogHeader>
            <DialogTitle>{showLyrics?.title}</DialogTitle>
            <DialogDescription>{showLyrics?.artist} | Key: {showLyrics?.default_key} | BPM: {showLyrics?.bpm || '-'}</DialogDescription>
          </DialogHeader>
          <pre style={{ fontFamily: "'SF Mono', 'Fira Code', monospace", fontSize: 14, lineHeight: 1.8, whiteSpace: 'pre-wrap', color: '#0f172a', padding: 16, background: '#f8fafc', borderRadius: 10 }}>
            {showLyrics?.lyrics || 'No lyrics available'}
          </pre>
        </DialogContent>
      </Dialog>
    </div>
  );
}
