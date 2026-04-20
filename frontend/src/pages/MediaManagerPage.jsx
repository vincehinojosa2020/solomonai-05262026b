import { useState, useEffect, useCallback } from 'react';
import { 
  Video, Plus, Search, Filter, MoreVertical, Edit, Trash2, 
  Star, Eye, EyeOff, ExternalLink, Play, Upload, Grid, List,
  Youtube, CheckCircle, AlertCircle, Loader2, X, Image,
  ChevronDown, GripVertical
} from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';
import { safeImgSrc } from '@/utils/sanitize';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';

// ═══════════════════════════════════════════════════════════════════════════════
// MEDIA MANAGER - Church Admin Video Library
// Design Principles Applied:
// - Don Norman: Clear affordances, immediate feedback
// - Steve Krug: Don't make me think - obvious actions
// - Refactoring UI: Visual hierarchy, spacing, polish
// - Laws of UX: Hick's Law (fewer choices), familiar patterns
// ═══════════════════════════════════════════════════════════════════════════════

const CATEGORIES = [
  { id: 'faith', name: 'Faith', icon: '🙏' },
  { id: 'family', name: 'Family', icon: '👨‍👩‍👧‍👦' },
  { id: 'leadership', name: 'Leadership', icon: '🎯' },
  { id: 'worship', name: 'Worship', icon: '🎵' },
  { id: 'growth', name: 'Growth', icon: '🌱' },
  { id: 'community', name: 'Community', icon: '🤝' },
];

export default function MediaManagerPage() {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState('grid'); // grid | list
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingVideo, setEditingVideo] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [stats, setStats] = useState({ total: 0, published: 0, featured: 0 });

  // Fetch videos on mount
  useEffect(() => {
    fetchVideos();
  }, [selectedCategory, searchQuery]);

  const fetchVideos = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (selectedCategory && selectedCategory !== 'all') {
        params.append('category_id', selectedCategory);
      }
      if (searchQuery) {
        params.append('search', searchQuery);
      }
      
      const res = await fetch(`${API_URL}/admin/media/videos?${params}`, {
        
      });
      
      if (res.ok) {
        const data = await res.json();
        setVideos(data.videos || []);
        setStats({
          total: data.total || 0,
          published: (data.videos || []).filter(v => v.is_published).length,
          featured: (data.videos || []).filter(v => v.is_featured).length
        });
      } else {
        toast.error('Failed to load videos');
      }
    } catch (error) {
      console.error('Error fetching videos:', error);
      toast.error('Failed to load videos');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteVideo = async (videoId) => {
    if (!confirm('Are you sure you want to delete this video?')) return;
    
    try {
      const res = await fetch(`${API_URL}/admin/media/videos/${videoId}`, {
        method: 'DELETE',
        
      });
      
      if (res.ok) {
        toast.success('Video deleted');
        fetchVideos();
      } else {
        toast.error('Failed to delete video');
      }
    } catch (error) {
      toast.error('Failed to delete video');
    }
  };

  const handleToggleFeatured = async (videoId) => {
    try {
      const res = await fetch(`${API_URL}/admin/media/videos/${videoId}/feature`, {
        method: 'POST',
        
      });
      
      if (res.ok) {
        const data = await res.json();
        toast.success(data.message);
        fetchVideos();
      }
    } catch (error) {
      toast.error('Failed to update video');
    }
  };

  const handleTogglePublished = async (video) => {
    try {
      const res = await fetch(`${API_URL}/admin/media/videos/${video.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        
        body: JSON.stringify({ is_published: !video.is_published })
      });
      
      if (res.ok) {
        toast.success(video.is_published ? 'Video unpublished' : 'Video published');
        fetchVideos();
      }
    } catch (error) {
      toast.error('Failed to update video');
    }
  };

  return (
    <div className="media-manager" data-testid="media-manager">
      {/* Page Header - Clear hierarchy (Refactoring UI) */}
      <div className="media-manager-header">
        <div className="media-manager-title-row">
          <div>
            <h1 className="media-manager-title">
              <Video className="w-7 h-7 text-purple-600" />
              Media Library
            </h1>
            <p className="media-manager-subtitle">
              Manage videos that appear in your member portal
            </p>
          </div>
          
          {/* Primary Action - High affordance (Don Norman) */}
          <Button 
            onClick={() => setShowAddModal(true)}
            className="media-add-btn"
            data-testid="add-video-btn"
          >
            <Plus className="w-4 h-4" />
            Add Video
          </Button>
        </div>

        {/* Stats Row - Visual feedback (Don Norman) */}
        <div className="media-stats-row">
          <div className="media-stat">
            <span className="media-stat-value">{stats.total}</span>
            <span className="media-stat-label">Total Videos</span>
          </div>
          <div className="media-stat">
            <span className="media-stat-value text-green-600">{stats.published}</span>
            <span className="media-stat-label">Published</span>
          </div>
          <div className="media-stat">
            <span className="media-stat-value text-amber-600">{stats.featured}</span>
            <span className="media-stat-label">Featured</span>
          </div>
        </div>
      </div>

      {/* Filters Bar - Hick's Law: Limited choices */}
      <div className="media-filters-bar">
        <div className="media-search">
          <Search className="w-4 h-4 text-slate-400" />
          <Input
            type="text"
            placeholder="Search videos..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="media-search-input"
            data-testid="video-search-input"
          />
        </div>

        <div className="media-filter-group">
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="media-category-select"
            data-testid="category-filter"
          >
            <option value="all">All Categories</option>
            {CATEGORIES.map(cat => (
              <option key={cat.id} value={cat.id}>{cat.icon} {cat.name}</option>
            ))}
          </select>

          <div className="media-view-toggle">
            <button 
              className={`view-btn ${viewMode === 'grid' ? 'active' : ''}`}
              onClick={() => setViewMode('grid')}
              title="Grid view"
            >
              <Grid className="w-4 h-4" />
            </button>
            <button 
              className={`view-btn ${viewMode === 'list' ? 'active' : ''}`}
              onClick={() => setViewMode('list')}
              title="List view"
            >
              <List className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Video Grid/List */}
      {loading ? (
        <div className="media-loading">
          <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
          <p>Loading your videos...</p>
        </div>
      ) : videos.length === 0 ? (
        <EmptyState onAddClick={() => setShowAddModal(true)} />
      ) : viewMode === 'grid' ? (
        <div className="media-grid" data-testid="video-grid">
          {videos.map(video => (
            <VideoCard 
              key={video.id} 
              video={video}
              onEdit={() => setEditingVideo(video)}
              onDelete={() => handleDeleteVideo(video.id)}
              onToggleFeatured={() => handleToggleFeatured(video.id)}
              onTogglePublished={() => handleTogglePublished(video)}
            />
          ))}
        </div>
      ) : (
        <div className="media-list" data-testid="video-list">
          {videos.map(video => (
            <VideoListItem 
              key={video.id} 
              video={video}
              onEdit={() => setEditingVideo(video)}
              onDelete={() => handleDeleteVideo(video.id)}
              onToggleFeatured={() => handleToggleFeatured(video.id)}
              onTogglePublished={() => handleTogglePublished(video)}
            />
          ))}
        </div>
      )}

      {/* Add Video Modal */}
      <AddVideoModal 
        open={showAddModal} 
        onClose={() => setShowAddModal(false)}
        onSuccess={() => {
          setShowAddModal(false);
          fetchVideos();
        }}
      />

      {/* Edit Video Modal */}
      {editingVideo && (
        <EditVideoModal 
          video={editingVideo}
          open={!!editingVideo} 
          onClose={() => setEditingVideo(null)}
          onSuccess={() => {
            setEditingVideo(null);
            fetchVideos();
          }}
        />
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// VIDEO CARD COMPONENT - Grid View
// ═══════════════════════════════════════════════════════════════════════════════

function VideoCard({ video, onEdit, onDelete, onToggleFeatured, onTogglePublished }) {
  const [showActions, setShowActions] = useState(false);

  return (
    <div 
      className={`video-card ${video.is_featured ? 'featured' : ''}`}
      data-testid={`video-card-${video.id}`}
    >
      {/* Thumbnail with overlay */}
      <div className="video-card-thumbnail">
        <img 
          src={video.thumbnail_url || `https://i.ytimg.com/vi/${video.youtube_id}/maxresdefault.jpg`}
          alt={video.title}
          loading="lazy"
        />
        
        {/* Play overlay */}
        <a 
          href={`https://youtube.com/watch?v=${video.youtube_id}`}
          target="_blank"
          rel="noopener noreferrer"
          className="video-play-overlay"
        >
          <Play className="w-10 h-10" />
        </a>

        {/* Status badges */}
        <div className="video-badges">
          {video.is_featured && (
            <span className="badge featured">
              <Star className="w-3 h-3" /> Featured
            </span>
          )}
          {video.badge && (
            <span className="badge new">{video.badge}</span>
          )}
          {!video.is_published && (
            <span className="badge draft">Draft</span>
          )}
        </div>

        {/* Duration */}
        {video.duration && (
          <span className="video-duration">{video.duration}</span>
        )}
      </div>

      {/* Card Content */}
      <div className="video-card-content">
        <h3 className="video-card-title">{video.title}</h3>
        {video.instructor && (
          <p className="video-card-instructor">{video.instructor}</p>
        )}
        
        {/* Quick Actions - Always visible (Don't make me think) */}
        <div className="video-card-actions">
          <button
            onClick={onToggleFeatured}
            className={`action-btn ${video.is_featured ? 'active' : ''}`}
            title={video.is_featured ? 'Remove from featured' : 'Make featured'}
          >
            <Star className="w-4 h-4" />
          </button>
          <button
            onClick={onTogglePublished}
            className={`action-btn ${video.is_published ? 'active' : ''}`}
            title={video.is_published ? 'Unpublish' : 'Publish'}
          >
            {video.is_published ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
          </button>
          <button onClick={onEdit} className="action-btn" title="Edit">
            <Edit className="w-4 h-4" />
          </button>
          <button onClick={onDelete} className="action-btn danger" title="Delete">
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// VIDEO LIST ITEM - List View
// ═══════════════════════════════════════════════════════════════════════════════

function VideoListItem({ video, onEdit, onDelete, onToggleFeatured, onTogglePublished }) {
  return (
    <div className={`video-list-item ${video.is_featured ? 'featured' : ''}`}>
      <div className="video-list-thumbnail">
        <img 
          src={video.thumbnail_url || `https://i.ytimg.com/vi/${video.youtube_id}/maxresdefault.jpg`}
          alt={video.title}
        />
        {video.duration && <span className="video-duration">{video.duration}</span>}
      </div>
      
      <div className="video-list-info">
        <h3 className="video-list-title">{video.title}</h3>
        <p className="video-list-meta">
          {video.instructor && <span>{video.instructor}</span>}
          {video.view_count > 0 && <span> • {video.view_count} views</span>}
        </p>
      </div>

      <div className="video-list-status">
        {video.is_featured && <span className="badge featured"><Star className="w-3 h-3" /> Featured</span>}
        {video.is_published ? (
          <span className="status-pill published">Published</span>
        ) : (
          <span className="status-pill draft">Draft</span>
        )}
      </div>

      <div className="video-list-actions">
        <button onClick={onToggleFeatured} className={`action-btn ${video.is_featured ? 'active' : ''}`}>
          <Star className="w-4 h-4" />
        </button>
        <button onClick={onTogglePublished} className={`action-btn ${video.is_published ? 'active' : ''}`}>
          {video.is_published ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
        </button>
        <button onClick={onEdit} className="action-btn"><Edit className="w-4 h-4" /></button>
        <button onClick={onDelete} className="action-btn danger"><Trash2 className="w-4 h-4" /></button>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// EMPTY STATE - Clear call to action (Krug)
// ═══════════════════════════════════════════════════════════════════════════════

function EmptyState({ onAddClick }) {
  return (
    <div className="media-empty-state" data-testid="empty-state">
      <div className="empty-icon">
        <Youtube className="w-16 h-16 text-slate-300" />
      </div>
      <h2>No videos yet</h2>
      <p>Add YouTube videos to your library and they'll appear in your member portal.</p>
      <Button onClick={onAddClick} className="media-add-btn">
        <Plus className="w-4 h-4" />
        Add Your First Video
      </Button>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// ADD VIDEO MODAL - Clear, focused form (Hick's Law)
// ═══════════════════════════════════════════════════════════════════════════════

function AddVideoModal({ open, onClose, onSuccess }) {
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [title, setTitle] = useState('');
  const [instructor, setInstructor] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('');
  const [isFeatured, setIsFeatured] = useState(false);
  const [badge, setBadge] = useState('');
  const [loading, setLoading] = useState(false);
  const [previewData, setPreviewData] = useState(null);

  // Extract YouTube ID and show preview
  useEffect(() => {
    const extractId = (url) => {
      const patterns = [
        /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})/,
        /^([a-zA-Z0-9_-]{11})$/
      ];
      for (const pattern of patterns) {
        const match = url.match(pattern);
        if (match) return match[1];
      }
      return null;
    };

    const id = extractId(youtubeUrl);
    if (id) {
      setPreviewData({
        id,
        thumbnail: `https://i.ytimg.com/vi/${id}/maxresdefault.jpg`
      });
    } else {
      setPreviewData(null);
    }
  }, [youtubeUrl]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!youtubeUrl || !title) {
      toast.error('Please enter a YouTube URL and title');
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/admin/media/videos`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        
        body: JSON.stringify({
          youtube_url: youtubeUrl,
          title,
          instructor,
          description,
          category_id: category || null,
          is_featured: isFeatured,
          badge: badge || null
        })
      });

      if (res.ok) {
        toast.success('Video added successfully!');
        onSuccess();
        // Reset form
        setYoutubeUrl('');
        setTitle('');
        setInstructor('');
        setDescription('');
        setCategory('');
        setIsFeatured(false);
        setBadge('');
      } else {
        const data = await res.json();
        toast.error(data.detail || 'Failed to add video');
      }
    } catch (error) {
      toast.error('Failed to add video');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="add-video-modal">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Youtube className="w-5 h-5 text-red-500" />
            Add YouTube Video
          </DialogTitle>
          <DialogDescription>
            Paste a YouTube URL to add a video to your library
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="add-video-form">
          {/* YouTube URL - Primary input with immediate feedback */}
          <div className="form-group">
            <label>YouTube URL *</label>
            <Input
              type="text"
              placeholder="https://youtube.com/watch?v=..."
              value={youtubeUrl}
              onChange={(e) => setYoutubeUrl(e.target.value)}
              className="youtube-url-input"
              data-testid="youtube-url-input"
            />
            
            {/* Preview - Immediate visual feedback (Don Norman) */}
            {previewData && (
              <div className="video-preview">
                <img src={safeImgSrc(previewData.thumbnail)} alt="Video preview" />
                <CheckCircle className="w-5 h-5 text-green-500" />
                <span>Valid YouTube video detected</span>
              </div>
            )}
          </div>

          {/* Title & Instructor - Most important metadata */}
          <div className="form-row">
            <div className="form-group">
              <label>Title *</label>
              <Input
                type="text"
                placeholder="Sermon title or video name"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                data-testid="video-title-input"
              />
            </div>
            <div className="form-group">
              <label>Speaker/Instructor</label>
              <Input
                type="text"
                placeholder="Pastor name"
                value={instructor}
                onChange={(e) => setInstructor(e.target.value)}
              />
            </div>
          </div>

          {/* Category & Badge - Secondary options */}
          <div className="form-row">
            <div className="form-group">
              <label>Category</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="form-select"
              >
                <option value="">Select category...</option>
                {CATEGORIES.map(cat => (
                  <option key={cat.id} value={cat.id}>{cat.icon} {cat.name}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Badge</label>
              <select
                value={badge}
                onChange={(e) => setBadge(e.target.value)}
                className="form-select"
              >
                <option value="">No badge</option>
                <option value="New">New</option>
                <option value="Popular">Popular</option>
                <option value="Staff Pick">Staff Pick</option>
              </select>
            </div>
          </div>

          {/* Description - Optional, less prominent */}
          <div className="form-group">
            <label>Description (optional)</label>
            <textarea
              placeholder="Brief description of the video..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="form-textarea"
              rows={2}
            />
          </div>

          {/* Featured toggle */}
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={isFeatured}
              onChange={(e) => setIsFeatured(e.target.checked)}
            />
            <Star className="w-4 h-4 text-amber-500" />
            Feature this video (shows as hero in portal)
          </label>

          {/* Actions */}
          <div className="modal-actions">
            <Button type="button" variant="ghost" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading || !youtubeUrl || !title}>
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
              Add Video
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// EDIT VIDEO MODAL
// ═══════════════════════════════════════════════════════════════════════════════

function EditVideoModal({ video, open, onClose, onSuccess }) {
  const [title, setTitle] = useState(video.title || '');
  const [instructor, setInstructor] = useState(video.instructor || '');
  const [description, setDescription] = useState(video.description || '');
  const [category, setCategory] = useState(video.category_id || '');
  const [badge, setBadge] = useState(video.badge || '');
  const [duration, setDuration] = useState(video.duration || '');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/admin/media/videos/${video.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        
        body: JSON.stringify({
          title,
          instructor,
          description,
          category_id: category || null,
          badge: badge || null,
          duration
        })
      });

      if (res.ok) {
        toast.success('Video updated!');
        onSuccess();
      } else {
        toast.error('Failed to update video');
      }
    } catch (error) {
      toast.error('Failed to update video');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="edit-video-modal">
        <DialogHeader>
          <DialogTitle>Edit Video</DialogTitle>
        </DialogHeader>

        {/* Video preview */}
        <div className="edit-video-preview">
          <img 
            src={video.thumbnail_url || `https://i.ytimg.com/vi/${video.youtube_id}/maxresdefault.jpg`}
            alt={video.title}
          />
        </div>

        <form onSubmit={handleSubmit} className="edit-video-form">
          <div className="form-group">
            <label>Title</label>
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Speaker</label>
              <Input
                value={instructor}
                onChange={(e) => setInstructor(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Duration</label>
              <Input
                placeholder="45:30"
                value={duration}
                onChange={(e) => setDuration(e.target.value)}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Category</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="form-select"
              >
                <option value="">None</option>
                {CATEGORIES.map(cat => (
                  <option key={cat.id} value={cat.id}>{cat.icon} {cat.name}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Badge</label>
              <select
                value={badge}
                onChange={(e) => setBadge(e.target.value)}
                className="form-select"
              >
                <option value="">None</option>
                <option value="New">New</option>
                <option value="Popular">Popular</option>
                <option value="Staff Pick">Staff Pick</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label>Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="form-textarea"
              rows={3}
            />
          </div>

          <div className="modal-actions">
            <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
            <Button type="submit" disabled={loading}>
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Save Changes'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
