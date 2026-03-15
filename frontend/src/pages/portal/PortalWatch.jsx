import { useState, useRef, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Play, ChevronLeft, ChevronRight, Clock, Search, Plus, X,
  BookmarkPlus, Info, LayoutGrid, Rows3, User, Sparkles,
  Heart, Users, Briefcase, Music, Book, Home, ChevronDown,
  Share2, MessageCircle, Copy, Check, Instagram, Facebook, Twitter, Mail, Smartphone,
  FileText, Edit3, Trash2, Send, Globe, Lock, UserPlus
} from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

// ═══════════════════════════════════════════════════════════════════════════════
// ABUNDANT TV - Unified Watch & Library Experience
// Now fetches content from database - managed by church admin
// ═══════════════════════════════════════════════════════════════════════════════

// Categories for filtering videos
const CATEGORIES = [
  { id: 'all', label: 'All', icon: LayoutGrid },
  { id: 'faith', label: 'Faith', icon: Heart },
  { id: 'family', label: 'Family', icon: Users },
  { id: 'leadership', label: 'Leadership', icon: Briefcase },
  { id: 'worship', label: 'Worship', icon: Music },
  { id: 'growth', label: 'Growth', icon: Book },
  { id: 'community', label: 'Community', icon: Home },
];

// ═══════════════════════════════════════════════════════════════════════════════
// VIDEO PLAYER MODAL - Masterclass-style with side-by-side notes
// ═══════════════════════════════════════════════════════════════════════════════

const VideoPlayer = ({ isOpen, onClose, video, onShare, user }) => {
  const [notes, setNotes] = useState([]);
  const [newNote, setNewNote] = useState('');
  const [savingNote, setSavingNote] = useState(false);
  const [showNotes, setShowNotes] = useState(true);

  useEffect(() => {
    if (isOpen && video?.id) {
      fetchVideoNotes();
    }
  }, [isOpen, video?.id]);

  const fetchVideoNotes = async () => {
    if (!video?.id) return;
    try {
      const res = await fetch(`${API_URL}/portal/video-notes/video/${video.id}`, { 
        
      });
      if (res.ok) {
        const data = await res.json();
        setNotes(data.notes || []);
      }
    } catch (error) {
      console.error('Failed to fetch notes:', error);
    }
  };

  const saveNote = async () => {
    if (!newNote.trim() || !video?.id) return;
    setSavingNote(true);
    try {
      const res = await fetch(`${API_URL}/portal/video-notes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        
        body: JSON.stringify({
          video_id: video.id,
          content: newNote.trim(),
          timestamp: null, // Could add video timestamp here
          is_public: false
        })
      });
      if (res.ok) {
        toast.success('Note saved!');
        setNewNote('');
        fetchVideoNotes();
      } else {
        toast.error('Failed to save note');
      }
    } catch (error) {
      toast.error('Error saving note');
    } finally {
      setSavingNote(false);
    }
  };

  const deleteNote = async (noteId) => {
    try {
      const res = await fetch(`${API_URL}/portal/video-notes/${noteId}`, {
        method: 'DELETE',
        
      });
      if (res.ok) {
        toast.success('Note deleted');
        fetchVideoNotes();
      }
    } catch (error) {
      toast.error('Failed to delete note');
    }
  };

  if (!isOpen || !video) return null;

  const handleGive = () => {
    window.location.href = '/portal/give';
  };

  return (
    <motion.div
      className="atv-modal atv-modal-fullscreen"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <div className="atv-modal-masterclass">
        {/* Header */}
        <div className="atv-masterclass-header">
          <button className="atv-modal-back" onClick={onClose}>
            <ChevronLeft className="w-5 h-5" />
            <span>Back to Library</span>
          </button>
          <div className="atv-masterclass-title">
            <h2>{video.title}</h2>
            <span>with {video.instructor}</span>
          </div>
          <div className="atv-masterclass-actions">
            <button className="atv-mc-btn" onClick={handleGive} data-testid="video-give-btn">
              <Heart className="w-4 h-4" />
              Give
            </button>
            <button className="atv-mc-btn" onClick={() => onShare && onShare(video)} data-testid="video-share-btn">
              <Share2 className="w-4 h-4" />
              Share
            </button>
            <button 
              className={`atv-mc-btn ${showNotes ? 'active' : ''}`} 
              onClick={() => setShowNotes(!showNotes)}
              data-testid="toggle-notes-btn"
            >
              <FileText className="w-4 h-4" />
              Notes
            </button>
          </div>
        </div>

        {/* Main Content - Video + Notes side by side */}
        <div className={`atv-masterclass-content ${showNotes ? 'with-notes' : ''}`}>
          {/* Video Section */}
          <div className="atv-masterclass-video">
            <iframe
              src={`https://www.youtube.com/embed/${video.youtubeId}?autoplay=1&rel=0&modestbranding=1`}
              title={video.title}
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          </div>

          {/* Notes Panel - Masterclass style */}
          {showNotes && (
            <div className="atv-masterclass-notes" data-testid="video-notes-panel">
              <div className="atv-notes-header">
                <FileText className="w-5 h-5" />
                <h3>My Notes</h3>
                <span className="atv-notes-count">{notes.length}</span>
              </div>

              {/* Note Input */}
              <div className="atv-notes-input">
                <textarea
                  placeholder="Take notes while watching..."
                  value={newNote}
                  onChange={(e) => setNewNote(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                      saveNote();
                    }
                  }}
                  data-testid="note-input"
                />
                <button 
                  className="atv-notes-save" 
                  onClick={saveNote}
                  disabled={savingNote || !newNote.trim()}
                  data-testid="save-note-btn"
                >
                  {savingNote ? 'Saving...' : 'Save Note'}
                </button>
                <span className="atv-notes-hint">⌘/Ctrl + Enter to save</span>
              </div>

              {/* Notes List */}
              <div className="atv-notes-list">
                {notes.length === 0 ? (
                  <div className="atv-notes-empty">
                    <FileText className="w-8 h-8" />
                    <p>No notes yet</p>
                    <span>Start taking notes while you watch!</span>
                  </div>
                ) : (
                  notes.map((note) => (
                    <div key={note.id} className="atv-note-item" data-testid={`note-${note.id}`}>
                      <p className="atv-note-content">{note.content}</p>
                      <div className="atv-note-meta">
                        <span className="atv-note-date">
                          {new Date(note.created_at).toLocaleDateString('en-US', {
                            month: 'short',
                            day: 'numeric',
                            hour: 'numeric',
                            minute: '2-digit'
                          })}
                        </span>
                        <button 
                          className="atv-note-delete"
                          onClick={() => deleteNote(note.id)}
                          title="Delete note"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// SHARE MODAL - Personal sharing with pre-populated messages
// ═══════════════════════════════════════════════════════════════════════════════

const ShareModal = ({ isOpen, onClose, video, userName, churchName }) => {
  const [copied, setCopied] = useState(false);
  const [selectedMessage, setSelectedMessage] = useState(0);
  
  if (!isOpen || !video) return null;

  const videoUrl = `${window.location.origin}/watch/${video.id || video.youtubeId}`;
  const appUrl = `${window.location.origin}`;
  
  // Pre-populated sharing messages
  const shareMessages = [
    {
      id: 'personal',
      label: 'Personal Invite',
      message: `Hey! This is ${userName}. I just watched "${video.title}" and it really spoke to me. Thought you might enjoy it too! 🙏\n\n${videoUrl}\n\nJoin me Sunday for coffee & church if this impacts you! ☕\n\nDownload the ${churchName} app: ${appUrl}`
    },
    {
      id: 'encouraging',
      label: 'Encouraging',
      message: `Just sharing something that blessed me today - "${video.title}" with ${video.instructor}. Hope it encourages you! ❤️\n\n${videoUrl}\n\nGet more content like this on the ${churchName} app: ${appUrl}`
    },
    {
      id: 'invite',
      label: 'Sunday Invite',
      message: `Hey! Wanted to share this powerful message: "${video.title}"\n\n${videoUrl}\n\nWould love for you to join us this Sunday at ${churchName}! 🙌\n\nExplore more: ${appUrl}`
    },
    {
      id: 'simple',
      label: 'Simple Share',
      message: `Check out this video: "${video.title}" - ${video.instructor}\n\n${videoUrl}`
    }
  ];
  
  const currentMessage = shareMessages[selectedMessage];
  
  const copyToClipboard = () => {
    navigator.clipboard.writeText(currentMessage.message);
    setCopied(true);
    toast.success('Message copied! Ready to paste and share');
    setTimeout(() => setCopied(false), 2000);
  };
  
  const shareViaSMS = () => {
    const smsUrl = `sms:?body=${encodeURIComponent(currentMessage.message)}`;
    window.open(smsUrl, '_blank');
  };
  
  const shareViaEmail = () => {
    const subject = `${userName} shared: ${video.title}`;
    const emailUrl = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(currentMessage.message)}`;
    window.open(emailUrl, '_blank');
  };
  
  const shareViaWhatsApp = () => {
    const waUrl = `https://wa.me/?text=${encodeURIComponent(currentMessage.message)}`;
    window.open(waUrl, '_blank');
  };

  return (
    <motion.div
      className="share-modal-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        className="share-modal"
        initial={{ scale: 0.9, opacity: 0, y: 20 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        exit={{ scale: 0.9, opacity: 0, y: 20 }}
        onClick={(e) => e.stopPropagation()}
      >
        <button className="share-modal-close" onClick={onClose}>
          <X className="w-5 h-5" />
        </button>
        
        <div className="share-modal-header">
          <Share2 className="w-6 h-6" />
          <h2>Share This Video</h2>
        </div>
        
        <div className="share-video-preview">
          <img src={video.thumbnail} alt={video.title} />
          <div className="share-video-info">
            <h3>{video.title}</h3>
            <p>{video.instructor}</p>
          </div>
        </div>
        
        {/* Message Style Selector */}
        <div className="share-message-selector">
          <label>Choose your message style:</label>
          <div className="share-message-options">
            {shareMessages.map((msg, idx) => (
              <button
                key={msg.id}
                className={`share-message-option ${selectedMessage === idx ? 'active' : ''}`}
                onClick={() => setSelectedMessage(idx)}
              >
                {msg.label}
              </button>
            ))}
          </div>
        </div>
        
        {/* Message Preview */}
        <div className="share-message-preview">
          <label>Message preview:</label>
          <div className="share-message-text">
            {currentMessage.message}
          </div>
        </div>
        
        {/* Share Buttons */}
        <div className="share-buttons">
          <button className="share-btn sms" onClick={shareViaSMS}>
            <MessageCircle className="w-5 h-5" />
            <span>Text Message</span>
          </button>
          <button className="share-btn whatsapp" onClick={shareViaWhatsApp}>
            <Smartphone className="w-5 h-5" />
            <span>WhatsApp</span>
          </button>
          <button className="share-btn email" onClick={shareViaEmail}>
            <Mail className="w-5 h-5" />
            <span>Email</span>
          </button>
          <button className="share-btn copy" onClick={copyToClipboard}>
            {copied ? <Check className="w-5 h-5" /> : <Copy className="w-5 h-5" />}
            <span>{copied ? 'Copied!' : 'Copy Message'}</span>
          </button>
        </div>
        
        <div className="share-footer">
          <p>When you share, you're helping spread God's word and inviting others to join our community! 🙏</p>
        </div>
      </motion.div>
    </motion.div>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// NOTES PANEL - Masterclass-style notes with sharing
// ═══════════════════════════════════════════════════════════════════════════════

const NotesPanel = ({ video, user, isOpen, onClose }) => {
  const [notes, setNotes] = useState([]);
  const [newNote, setNewNote] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('my'); // 'my' or 'shared'
  const [editingNote, setEditingNote] = useState(null);
  const [shareModalNote, setShareModalNote] = useState(null);
  
  useEffect(() => {
    if (isOpen && video) {
      fetchNotes();
    }
  }, [isOpen, video?.id, activeTab]);
  
  const fetchNotes = async () => {
    if (!video?.id) return;
    setLoading(true);
    try {
      const endpoint = activeTab === 'shared' 
        ? `${API_URL}/portal/video-notes/shared`
        : `${API_URL}/portal/video-notes/video/${video.id}`;
      const res = await fetch(endpoint);
      if (res.ok) {
        const data = await res.json();
        // Ensure is_own is set for filtering
        const processedNotes = (data.notes || []).map(note => ({
          ...note,
          is_own: note.is_own !== undefined ? note.is_own : true  // Default to own if not specified
        }));
        setNotes(processedNotes);
      }
    } catch (error) {
      console.error('Failed to fetch notes:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const createNote = async () => {
    if (!newNote.trim()) return;
    
    try {
      const res = await fetch(`${API_URL}/portal/video-notes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        
        body: JSON.stringify({
          video_id: video.id,
          content: newNote.trim(),
          is_public: false
        })
      });
      
      if (res.ok) {
        toast.success('Note saved!');
        setNewNote('');
        fetchNotes();
      }
    } catch (error) {
      toast.error('Failed to save note');
    }
  };
  
  const updateNote = async (noteId, content) => {
    try {
      const res = await fetch(`${API_URL}/portal/video-notes/${noteId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        
        body: JSON.stringify({ content })
      });
      
      if (res.ok) {
        toast.success('Note updated');
        setEditingNote(null);
        fetchNotes();
      }
    } catch (error) {
      toast.error('Failed to update note');
    }
  };
  
  const deleteNote = async (noteId) => {
    if (!window.confirm('Delete this note?')) return;
    
    try {
      const res = await fetch(`${API_URL}/portal/video-notes/${noteId}`, {
        method: 'DELETE',
        
      });
      
      if (res.ok) {
        toast.success('Note deleted');
        fetchNotes();
      }
    } catch (error) {
      toast.error('Failed to delete note');
    }
  };
  
  if (!isOpen) return null;
  
  const myNotes = notes.filter(n => n.is_own);
  const sharedNotes = notes.filter(n => !n.is_own);
  const displayNotes = activeTab === 'my' ? myNotes : sharedNotes;
  
  return (
    <div
      className="notes-panel"
      style={{
        position: 'fixed',
        top: 0,
        right: 0,
        bottom: 0,
        width: '420px',
        maxWidth: '100%',
        background: '#ffffff',
        zIndex: 9999,
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '-8px 0 40px rgba(0, 0, 0, 0.2)'
      }}
    >
      <div className="notes-panel-header">
        <div className="notes-panel-title">
          <FileText className="w-5 h-5" />
          <h3>Notes</h3>
        </div>
        <button className="notes-panel-close" onClick={onClose}>
          <X className="w-5 h-5" />
        </button>
      </div>
      
      {/* Tabs */}
      <div className="notes-tabs">
        <button 
          className={`notes-tab ${activeTab === 'my' ? 'active' : ''}`}
          onClick={() => setActiveTab('my')}
        >
          <Lock className="w-4 h-4" />
          My Notes
        </button>
        <button 
          className={`notes-tab ${activeTab === 'shared' ? 'active' : ''}`}
          onClick={() => setActiveTab('shared')}
        >
          <Globe className="w-4 h-4" />
          Shared with Me
        </button>
      </div>
      
      {/* Video Info */}
      {video && (
        <div className="notes-video-info">
          <img 
            src={video.thumbnail} 
            alt={video.title}
            style={{ width: '60px', height: '36px', objectFit: 'cover', borderRadius: '4px', flexShrink: 0 }}
          />
          <div>
            <h4>{video.title}</h4>
            <p>{video.instructor}</p>
          </div>
        </div>
      )}
      
      {/* New Note Input */}
      {activeTab === 'my' && (
        <div className="notes-input-area">
          <textarea
            value={newNote}
            onChange={(e) => setNewNote(e.target.value)}
            placeholder="Take a note while watching..."
            rows={3}
          />
          <button 
            className="notes-save-btn"
            onClick={createNote}
            disabled={!newNote.trim()}
          >
            <Plus className="w-4 h-4" />
            Add Note
          </button>
        </div>
      )}
      
      {/* Notes List */}
      <div className="notes-list">
        {loading ? (
          <div className="notes-loading">Loading notes...</div>
        ) : displayNotes.length === 0 ? (
          <div className="notes-empty">
            {activeTab === 'my' ? (
              <>
                <FileText className="w-12 h-12" />
                <p>No notes yet</p>
                <span>Start taking notes while you watch!</span>
              </>
            ) : (
              <>
                <Users className="w-12 h-12" />
                <p>No shared notes</p>
                <span>Notes shared with you will appear here</span>
              </>
            )}
          </div>
        ) : (
          displayNotes.map((note) => (
            <NoteCard 
              key={note.id}
              note={note}
              isOwn={note.is_own}
              onEdit={() => setEditingNote(note)}
              onDelete={() => deleteNote(note.id)}
              onShare={() => setShareModalNote(note)}
            />
          ))
        )}
      </div>
      
      {/* Edit Modal */}
      <AnimatePresence>
        {editingNote && (
          <EditNoteModal
            note={editingNote}
            onSave={(content) => updateNote(editingNote.id, content)}
            onClose={() => setEditingNote(null)}
          />
        )}
      </AnimatePresence>
      
      {/* Share Note Modal */}
      <AnimatePresence>
        {shareModalNote && (
          <ShareNoteModal
            note={shareModalNote}
            onClose={() => setShareModalNote(null)}
            onShared={() => {
              setShareModalNote(null);
              fetchNotes();
            }}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

const NoteCard = ({ note, isOwn, onEdit, onDelete, onShare }) => {
  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };
  
  return (
    <div className={`note-card ${isOwn ? 'own' : 'shared'}`}>
      <div className="note-card-header">
        <div className="note-card-author">
          <div className="note-card-avatar">
            {note.author_name?.charAt(0) || 'U'}
          </div>
          <div>
            <span className="note-card-name">{note.author_name || 'Unknown'}</span>
            <span className="note-card-date">{formatDate(note.created_at)}</span>
          </div>
        </div>
        {isOwn && (
          <div className="note-card-actions">
            <button onClick={onShare} title="Share note">
              <Share2 className="w-4 h-4" />
            </button>
            <button onClick={onEdit} title="Edit note">
              <Edit3 className="w-4 h-4" />
            </button>
            <button onClick={onDelete} title="Delete note">
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
      
      {note.timestamp && (
        <div className="note-card-timestamp">
          <Clock className="w-3 h-3" />
          {note.timestamp}
        </div>
      )}
      
      <div className="note-card-content">
        {note.content}
      </div>
      
      {(note.is_public || (note.shared_with && note.shared_with.length > 0)) && (
        <div className="note-card-sharing">
          {note.is_public ? (
            <span className="note-sharing-badge public">
              <Globe className="w-3 h-3" /> Shared with church
            </span>
          ) : (
            <span className="note-sharing-badge private">
              <Users className="w-3 h-3" /> Shared privately
            </span>
          )}
        </div>
      )}
    </div>
  );
};

const EditNoteModal = ({ note, onSave, onClose }) => {
  const [content, setContent] = useState(note.content);
  
  return (
    <motion.div
      className="edit-note-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        className="edit-note-modal"
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
      >
        <h3>Edit Note</h3>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          rows={5}
        />
        <div className="edit-note-actions">
          <button className="btn-cancel" onClick={onClose}>Cancel</button>
          <button className="btn-save" onClick={() => onSave(content)}>
            Save Changes
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
};

const ShareNoteModal = ({ note, onClose, onShared }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [members, setMembers] = useState([]);
  const [selectedMembers, setSelectedMembers] = useState([]);
  const [shareWithChurch, setShareWithChurch] = useState(note.is_public || false);
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    fetchMembers();
  }, [searchQuery]);
  
  const fetchMembers = async () => {
    try {
      const url = searchQuery 
        ? `${API_URL}/portal/church-members?search=${encodeURIComponent(searchQuery)}`
        : `${API_URL}/portal/church-members`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setMembers(data.members || []);
      }
    } catch (error) {
      console.error('Failed to fetch members:', error);
    }
  };
  
  const toggleMember = (memberId) => {
    setSelectedMembers(prev => 
      prev.includes(memberId)
        ? prev.filter(id => id !== memberId)
        : [...prev, memberId]
    );
  };
  
  const shareNote = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/portal/video-notes/${note.id}/share`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        
        body: JSON.stringify({
          user_ids: selectedMembers,
          is_public: shareWithChurch
        })
      });
      
      if (res.ok) {
        toast.success('Note shared successfully!');
        onShared();
      }
    } catch (error) {
      toast.error('Failed to share note');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <motion.div
      className="share-note-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        className="share-note-modal"
        initial={{ scale: 0.9, opacity: 0, y: 20 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        exit={{ scale: 0.9, opacity: 0, y: 20 }}
        onClick={(e) => e.stopPropagation()}
      >
        <button className="share-note-close" onClick={onClose}>
          <X className="w-5 h-5" />
        </button>
        
        <div className="share-note-header">
          <UserPlus className="w-6 h-6" />
          <h3>Share Your Note</h3>
        </div>
        
        <div className="share-note-preview">
          <p>{note.content.length > 100 ? note.content.slice(0, 100) + '...' : note.content}</p>
        </div>
        
        {/* Share with entire church option */}
        <div className="share-note-option">
          <label className="share-option-checkbox">
            <input
              type="checkbox"
              checked={shareWithChurch}
              onChange={(e) => setShareWithChurch(e.target.checked)}
            />
            <Globe className="w-4 h-4" />
            <span>Share with entire church</span>
          </label>
          <p className="share-option-desc">All members of your church will be able to see this note</p>
        </div>
        
        <div className="share-note-divider">
          <span>or share with specific people</span>
        </div>
        
        {/* Search members */}
        <div className="share-note-search">
          <Search className="w-4 h-4" />
          <input
            type="text"
            placeholder="Search members by name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        
        {/* Members list */}
        <div className="share-note-members">
          {members.map(member => (
            <label key={member.user_id} className="share-member-item">
              <input
                type="checkbox"
                checked={selectedMembers.includes(member.user_id)}
                onChange={() => toggleMember(member.user_id)}
              />
              <div className="share-member-avatar">
                {member.name?.charAt(0) || 'U'}
              </div>
              <div className="share-member-info">
                <span className="share-member-name">{member.name}</span>
                <span className="share-member-email">{member.email}</span>
              </div>
            </label>
          ))}
        </div>
        
        <button 
          className="share-note-btn"
          onClick={shareNote}
          disabled={loading || (!shareWithChurch && selectedMembers.length === 0)}
        >
          {loading ? 'Sharing...' : 'Share Note'}
        </button>
      </motion.div>
    </motion.div>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// HERO SECTION
// ═══════════════════════════════════════════════════════════════════════════════

const HeroSection = ({ content, onPlay, onShare }) => {
  const [activeIndex, setActiveIndex] = useState(0);
  const featured = content.filter(c => c.featured).slice(0, 3);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveIndex((prev) => (prev + 1) % featured.length);
    }, 8000);
    return () => clearInterval(interval);
  }, [featured.length]);

  const current = featured[activeIndex];
  if (!current) return null;

  return (
    <section className="atv-hero">
      <AnimatePresence mode="wait">
        <motion.div
          key={current.id}
          className="atv-hero-bg"
          style={{ backgroundImage: `url(${current.thumbnail})` }}
          initial={{ opacity: 0, scale: 1.1 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 1 }}
        />
      </AnimatePresence>
      
      <div className="atv-hero-overlay" />
      
      <div className="atv-hero-content">
        <AnimatePresence mode="wait">
          <motion.div
            key={current.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.5 }}
          >
            {current.badge && <span className="atv-hero-badge">{current.badge}</span>}
            <h1 className="atv-hero-title">{current.title}</h1>
            <p className="atv-hero-instructor">With {current.instructor}</p>
            <p className="atv-hero-desc">{current.description}</p>
            <div className="atv-hero-meta">
              <Clock className="w-4 h-4" />
              <span>{current.duration}</span>
            </div>
            <div className="atv-hero-actions">
              <button className="atv-btn-primary" onClick={() => onPlay(current)} data-testid="hero-watch-btn">
                <Play className="w-5 h-5" fill="currentColor" />
                Watch Now
              </button>
              <button className="atv-btn-secondary">
                <Plus className="w-5 h-5" />
                My List
              </button>
              <button 
                className="atv-btn-share" 
                onClick={() => onShare(current)}
                data-testid="hero-share-btn"
              >
                <Share2 className="w-5 h-5" />
                Share
              </button>
            </div>
          </motion.div>
        </AnimatePresence>
        
        <div className="atv-hero-dots">
          {featured.map((_, i) => (
            <button
              key={i}
              className={`atv-dot ${activeIndex === i ? 'active' : ''}`}
              onClick={() => setActiveIndex(i)}
            />
          ))}
        </div>
      </div>
    </section>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// CONTENT CARD
// ═══════════════════════════════════════════════════════════════════════════════

const ContentCard = ({ item, onPlay, onShare, viewMode }) => {
  const [hovered, setHovered] = useState(false);

  return (
    <motion.article
      className={`atv-card ${viewMode}`}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -6 }}
      transition={{ duration: 0.3 }}
      data-testid={`video-card-${item.id}`}
    >
      <div className="atv-card-thumb">
        <img 
          src={item.thumbnail} 
          alt={item.title}
          onError={(e) => { e.target.src = `https://img.youtube.com/vi/${item.youtubeId}/hqdefault.jpg`; }}
        />
        {item.badge && <span className={`atv-card-badge ${item.badge.toLowerCase()}`}>{item.badge}</span>}
        <span className="atv-card-duration">{item.duration}</span>
        
        <AnimatePresence>
          {hovered && (
            <motion.div 
              className="atv-card-overlay"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <button className="atv-play-btn" onClick={() => onPlay(item)} data-testid={`play-btn-${item.id}`}>
                <Play className="w-6 h-6" fill="currentColor" />
              </button>
              <button className="atv-add-btn">
                <Plus className="w-5 h-5" />
              </button>
              <button 
                className="atv-share-btn" 
                onClick={(e) => { e.stopPropagation(); onShare(item); }}
                data-testid={`share-btn-${item.id}`}
              >
                <Share2 className="w-5 h-5" />
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
      
      <div className="atv-card-info">
        <div className="atv-card-info-top">
          <p className="atv-card-meta">{item.duration} • {item.category}</p>
          <button 
            className="atv-card-share-icon"
            onClick={(e) => { e.stopPropagation(); onShare(item); }}
            title="Share this video"
          >
            <Share2 className="w-4 h-4" />
          </button>
        </div>
        <h3 className="atv-card-title">{item.title}</h3>
        <p className="atv-card-instructor">With {item.instructor}</p>
        {hovered && item.description && (
          <motion.p 
            className="atv-card-desc"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
          >
            {item.description}
          </motion.p>
        )}
      </div>
    </motion.article>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// CAROUSEL ROW
// ═══════════════════════════════════════════════════════════════════════════════

const CarouselRow = ({ title, items, onPlay, onShare }) => {
  const scrollRef = useRef(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(true);

  const checkScroll = () => {
    if (scrollRef.current) {
      const { scrollLeft, scrollWidth, clientWidth } = scrollRef.current;
      setCanScrollLeft(scrollLeft > 0);
      setCanScrollRight(scrollLeft < scrollWidth - clientWidth - 10);
    }
  };

  const scroll = (dir) => {
    if (scrollRef.current) {
      scrollRef.current.scrollBy({ left: dir === 'left' ? -400 : 400, behavior: 'smooth' });
    }
  };

  useEffect(() => {
    checkScroll();
    const ref = scrollRef.current;
    if (ref) ref.addEventListener('scroll', checkScroll);
    return () => ref?.removeEventListener('scroll', checkScroll);
  }, []);

  if (!items.length) return null;

  return (
    <section className="atv-carousel">
      <div className="atv-carousel-header">
        <h2>{title}</h2>
        <div className="atv-carousel-nav">
          {canScrollLeft && (
            <button className="atv-nav-btn" onClick={() => scroll('left')}>
              <ChevronLeft />
            </button>
          )}
          {canScrollRight && (
            <button className="atv-nav-btn" onClick={() => scroll('right')}>
              <ChevronRight />
            </button>
          )}
        </div>
      </div>
      <div className="atv-carousel-track" ref={scrollRef}>
        {items.map((item) => (
          <ContentCard key={item.id} item={item} onPlay={onPlay} onShare={onShare} viewMode="carousel" />
        ))}
      </div>
    </section>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN COMPONENT - Now fetches from database
// ═══════════════════════════════════════════════════════════════════════════════

export default function PortalWatch() {
  const { user, tenant } = useOutletContext();
  const [viewMode, setViewMode] = useState('featured'); // 'featured' or 'browse'
  const [activeCategory, setActiveCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [videoModal, setVideoModal] = useState({ open: false, video: null });
  const [shareModal, setShareModal] = useState({ open: false, video: null });
  const [notesPanel, setNotesPanel] = useState({ open: false, video: null });
  const [allContent, setAllContent] = useState([]);
  const [loading, setLoading] = useState(true);

  // Fetch videos from database
  useEffect(() => {
    fetchVideos();
  }, []);

  const fetchVideos = async () => {
    try {
      const res = await fetch(`${API_URL}/portal/media/videos`);
      if (res.ok) {
        const data = await res.json();
        // Transform database format to UI format
        const transformed = (data.videos || []).map(v => ({
          id: v.id,
          title: v.title,
          instructor: v.instructor || 'Unknown Speaker',
          duration: v.duration || '',
          category: v.category_id || 'faith',
          badge: v.badge || null,
          youtubeId: v.youtube_id,
          thumbnail: v.thumbnail_url || `https://i.ytimg.com/vi/${v.youtube_id}/maxresdefault.jpg`,
          description: v.description || '',
          featured: v.is_featured || false
        }));
        setAllContent(transformed);
      }
    } catch (error) {
      console.error('Failed to fetch videos:', error);
    } finally {
      setLoading(false);
    }
  };

  // Filter content
  const filteredContent = allContent.filter(item => {
    const matchesCategory = activeCategory === 'all' || item.category === activeCategory;
    const matchesSearch = !searchQuery || 
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.instructor.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  // Group content for carousels
  const newContent = allContent.filter(c => c.badge === 'New');
  const popularContent = allContent.filter(c => c.badge === 'Popular' || c.badge === 'Featured' || c.featured);
  const faithContent = allContent.filter(c => c.category === 'faith');
  const growthContent = allContent.filter(c => c.category === 'growth');

  // Get church name for branding
  const churchName = tenant?.name || 'Church';
  const logoLetter = churchName.charAt(0);
  const userName = user?.name || 'A friend';

  // Handle share
  const handleShare = (video) => {
    setShareModal({ open: true, video });
  };

  // Handle notes
  const handleNotes = (video) => {
    setNotesPanel({ open: true, video });
  };

  if (loading) {
    return (
      <div className="atv-page" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
        <div style={{ textAlign: 'center', color: '#94a3b8' }}>
          <div style={{ fontSize: '24px', marginBottom: '8px' }}>Loading videos...</div>
        </div>
      </div>
    );
  }

  if (allContent.length === 0) {
    return (
      <div className="atv-page" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
        <div style={{ textAlign: 'center', color: '#94a3b8' }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>📺</div>
          <div style={{ fontSize: '20px', fontWeight: '600', marginBottom: '8px' }}>No videos available yet</div>
          <div style={{ fontSize: '14px' }}>Check back soon for sermon videos and more!</div>
        </div>
      </div>
    );
  }

  return (
    <div className="atv-page" data-testid="watch-page">
      {/* Cinema Red Bar */}
      <div className="atv-red-bar" />

      {/* Header */}
      <header className="atv-header">
        <div className="atv-logo">
          <span className="atv-logo-mark">{logoLetter}</span>
          <span className="atv-logo-text">Watch</span>
          <span className="atv-logo-tagline">Live. On Demand. Always in the Word.</span>
        </div>

        {/* MASTERCLASS-STYLE SEARCH - In header center */}
        <div className="atv-header-search">
          <Search className="atv-header-search-icon" />
          <input
            type="text"
            placeholder="Search Instructors, Classes, Topics and more"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="atv-header-search-input"
            data-testid="watch-search-header"
          />
          {searchQuery && (
            <button 
              className="atv-header-search-clear"
              onClick={() => setSearchQuery('')}
            >
              <X className="w-3 h-3" />
            </button>
          )}
        </div>

        <div className="atv-header-actions">
          <button 
            className="atv-notes-btn"
            onClick={() => setNotesPanel({ open: true, video: allContent[0] || null })}
            data-testid="my-notes-btn"
          >
            <FileText className="w-4 h-4" />
            My Notes
          </button>
          <div className="atv-view-toggle">
            <button 
              className={viewMode === 'featured' ? 'active' : ''}
              onClick={() => setViewMode('featured')}
            >
              <Rows3 className="w-4 h-4" />
              Featured
            </button>
            <button 
              className={viewMode === 'browse' ? 'active' : ''}
              onClick={() => setViewMode('browse')}
            >
              <LayoutGrid className="w-4 h-4" />
              Browse
            </button>
          </div>
          <div className="atv-user">
            <div className="atv-avatar">{user?.name?.charAt(0) || 'M'}</div>
          </div>
        </div>
      </header>

      {/* Category Pills */}
      <nav className="atv-categories">
        {CATEGORIES.map((cat) => {
          const Icon = cat.icon;
          return (
            <button
              key={cat.id}
              className={`atv-cat-pill ${activeCategory === cat.id ? 'active' : ''}`}
              onClick={() => setActiveCategory(cat.id)}
            >
              <Icon className="w-4 h-4" />
              {cat.label}
            </button>
          );
        })}
      </nav>

      {/* Main Content */}
      <main className="atv-main">
        {viewMode === 'featured' ? (
          <>
            {/* Hero */}
            <HeroSection 
              content={allContent} 
              onPlay={(v) => setVideoModal({ open: true, video: v })}
              onShare={handleShare}
            />
            
            {/* Carousels */}
            {newContent.length > 0 && <CarouselRow title="New This Week" items={newContent} onPlay={(v) => setVideoModal({ open: true, video: v })} onShare={handleShare} />}
            {popularContent.length > 0 && <CarouselRow title="Popular Series" items={popularContent} onPlay={(v) => setVideoModal({ open: true, video: v })} onShare={handleShare} />}
            {faithContent.length > 0 && <CarouselRow title="Faith & Spirituality" items={faithContent} onPlay={(v) => setVideoModal({ open: true, video: v })} onShare={handleShare} />}
            {growthContent.length > 0 && <CarouselRow title="Personal Growth" items={growthContent} onPlay={(v) => setVideoModal({ open: true, video: v })} onShare={handleShare} />}
          </>
        ) : (
          /* Browse Grid View */
          <div className="atv-browse">
            <div className="atv-browse-header">
              <h2>{activeCategory === 'all' ? 'All Sermons' : CATEGORIES.find(c => c.id === activeCategory)?.label}</h2>
              <span className="atv-browse-count">{filteredContent.length} videos</span>
            </div>
            <div className="atv-grid">
              {filteredContent.map((item) => (
                <ContentCard key={item.id} item={item} onPlay={(v) => setVideoModal({ open: true, video: v })} onShare={handleShare} viewMode="grid" />
              ))}
            </div>
            {filteredContent.length === 0 && (
              <div className="atv-empty">
                <Search className="w-16 h-16" />
                <h3>No videos found</h3>
                <p>Try a different category or search term</p>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Video Modal */}
      <AnimatePresence>
        {videoModal.open && (
          <VideoPlayer
            isOpen={videoModal.open}
            video={videoModal.video}
            onClose={() => setVideoModal({ open: false, video: null })}
            onShare={handleShare}
            user={user}
          />
        )}
      </AnimatePresence>

      {/* Share Modal */}
      <AnimatePresence>
        {shareModal.open && (
          <ShareModal
            isOpen={shareModal.open}
            video={shareModal.video}
            userName={userName}
            churchName={churchName}
            onClose={() => setShareModal({ open: false, video: null })}
          />
        )}
      </AnimatePresence>

      {/* Notes Panel */}
      {notesPanel.open && (
        <NotesPanel
          video={notesPanel.video}
          user={user}
          isOpen={notesPanel.open}
          onClose={() => setNotesPanel({ open: false, video: null })}
        />
      )}
    </div>
  );
}
