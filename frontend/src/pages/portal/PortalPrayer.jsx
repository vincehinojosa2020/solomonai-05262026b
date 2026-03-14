import { useState, useEffect, useCallback } from 'react';
import { useOutletContext } from 'react-router-dom';
import { usePolling } from '@/hooks/usePolling';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Heart, Send, Plus, X, Filter, Check, Clock,
  MessageCircle, Users, Globe, Lock, ChevronDown
} from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

const CATEGORIES = [
  { id: 'general', name: 'General', icon: '🙏' },
  { id: 'healing', name: 'Healing', icon: '💚' },
  { id: 'family', name: 'Family', icon: '👨‍👩‍👧‍👦' },
  { id: 'financial', name: 'Financial', icon: '💰' },
  { id: 'guidance', name: 'Guidance', icon: '🧭' },
  { id: 'thanksgiving', name: 'Thanksgiving', icon: '🙌' },
  { id: 'salvation', name: 'Salvation', icon: '✝️' },
  { id: 'relationships', name: 'Relationships', icon: '❤️' },
];

export default function PortalPrayer() {
  const { user, tenant } = useOutletContext();
  const [activeTab, setActiveTab] = useState('wall'); // 'wall' or 'my'
  const [prayerWall, setPrayerWall] = useState([]);
  const [myRequests, setMyRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showNewRequest, setShowNewRequest] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [prayedFor, setPrayedFor] = useState(new Set());

  // New request form
  const [newRequest, setNewRequest] = useState({
    category: 'general',
    title: '',
    content: '',
    is_public: false,
    is_anonymous: false
  });

  useEffect(() => {
    fetchData();
  }, [activeTab, selectedCategory]);

  // Real-time polling every 30 seconds
  usePolling(useCallback(() => fetchData(), [activeTab, selectedCategory]), 30000);

  const fetchData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'wall') {
        const url = selectedCategory === 'all' 
          ? `${API_URL}/portal/prayer/wall`
          : `${API_URL}/portal/prayer/wall?category=${selectedCategory}`;
        const res = await fetch(url, { credentials: 'include' });
        if (res.ok) {
          const data = await res.json();
          setPrayerWall(data.requests || []);
        }
      } else {
        const res = await fetch(`${API_URL}/portal/prayer/requests`, { credentials: 'include' });
        if (res.ok) {
          const data = await res.json();
          setMyRequests(data.requests || []);
        }
      }
    } catch (error) {
      console.error('Failed to fetch prayer requests:', error);
    } finally {
      setLoading(false);
    }
  };

  const submitRequest = async () => {
    if (!newRequest.title.trim()) {
      toast.error('Please enter a title for your prayer request');
      return;
    }
    if (!newRequest.content.trim()) {
      toast.error('Please describe your prayer request');
      return;
    }

    try {
      const res = await fetch(`${API_URL}/portal/prayer/requests`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(newRequest)
      });

      if (res.ok) {
        toast.success('Prayer request submitted! 🙏');
        setShowNewRequest(false);
        setNewRequest({
          category: 'general',
          title: '',
          content: '',
          is_public: false,
          is_anonymous: false
        });
        fetchData();
      } else {
        toast.error('Failed to submit prayer request');
      }
    } catch (error) {
      toast.error('Error submitting prayer request');
    }
  };

  const prayForRequest = async (requestId) => {
    if (prayedFor.has(requestId)) {
      toast.info('Already prayed for this request');
      return;
    }

    try {
      const res = await fetch(`${API_URL}/portal/prayer/requests/${requestId}/pray`, {
        method: 'POST',
        credentials: 'include'
      });

      if (res.ok) {
        toast.success('Prayer recorded! God bless you 🙏');
        setPrayedFor(prev => new Set([...prev, requestId]));
        // Update local count
        setPrayerWall(prev => prev.map(req => 
          req.id === requestId 
            ? { ...req, prayer_count: (req.prayer_count || 0) + 1 }
            : req
        ));
      }
    } catch (error) {
      toast.error('Error recording prayer');
    }
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now - date;
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffHours < 1) return 'Just now';
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'answered':
        return <span className="prayer-status answered">✓ Answered</span>;
      case 'closed':
        return <span className="prayer-status closed">Closed</span>;
      default:
        return <span className="prayer-status active">Active</span>;
    }
  };

  return (
    <div className="portal-prayer" data-testid="portal-prayer">
      {/* Header */}
      <div className="prayer-header">
        <div className="prayer-header-content">
          <h1>Prayer Requests</h1>
          <p>Share your requests and pray for our church family</p>
        </div>
        <button 
          className="prayer-new-btn"
          onClick={() => setShowNewRequest(true)}
          data-testid="new-prayer-request-btn"
        >
          <Plus className="w-5 h-5" />
          New Prayer Request
        </button>
      </div>

      {/* Tabs */}
      <div className="prayer-tabs">
        <button
          className={`prayer-tab ${activeTab === 'wall' ? 'active' : ''}`}
          onClick={() => setActiveTab('wall')}
          data-testid="prayer-wall-tab"
        >
          <Globe className="w-4 h-4" />
          Prayer Wall
        </button>
        <button
          className={`prayer-tab ${activeTab === 'my' ? 'active' : ''}`}
          onClick={() => setActiveTab('my')}
          data-testid="my-prayers-tab"
        >
          <Lock className="w-4 h-4" />
          My Requests
        </button>
      </div>

      {/* Category Filter (Wall only) */}
      {activeTab === 'wall' && (
        <div className="prayer-categories">
          <button
            className={`prayer-category ${selectedCategory === 'all' ? 'active' : ''}`}
            onClick={() => setSelectedCategory('all')}
          >
            All
          </button>
          {CATEGORIES.map(cat => (
            <button
              key={cat.id}
              className={`prayer-category ${selectedCategory === cat.id ? 'active' : ''}`}
              onClick={() => setSelectedCategory(cat.id)}
            >
              {cat.icon} {cat.name}
            </button>
          ))}
        </div>
      )}

      {/* Content */}
      <div className="prayer-content">
        {loading ? (
          <div className="prayer-loading">
            <Heart className="w-8 h-8 animate-pulse" />
            <p>Loading prayers...</p>
          </div>
        ) : activeTab === 'wall' ? (
          /* Prayer Wall */
          prayerWall.length === 0 ? (
            <div className="prayer-empty">
              <Heart className="w-12 h-12" />
              <h3>No prayer requests yet</h3>
              <p>Be the first to share a prayer request with our community</p>
              <button onClick={() => setShowNewRequest(true)} className="prayer-empty-btn">
                Share a Prayer Request
              </button>
            </div>
          ) : (
            <div className="prayer-wall-grid">
              {prayerWall.map(request => (
                <motion.div
                  key={request.id}
                  className="prayer-card"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  data-testid={`prayer-card-${request.id}`}
                >
                  <div className="prayer-card-header">
                    <span className="prayer-card-category">
                      {CATEGORIES.find(c => c.id === request.category)?.icon} {request.category}
                    </span>
                    <span className="prayer-card-time">{formatDate(request.created_at)}</span>
                  </div>
                  <h3 className="prayer-card-title">{request.title}</h3>
                  <p className="prayer-card-content">{request.content}</p>
                  <div className="prayer-card-footer">
                    <span className="prayer-card-author">
                      {request.is_anonymous ? 'Anonymous' : request.user_name}
                    </span>
                    <button
                      className={`prayer-card-pray ${prayedFor.has(request.id) ? 'prayed' : ''}`}
                      onClick={() => prayForRequest(request.id)}
                      data-testid={`pray-btn-${request.id}`}
                    >
                      {prayedFor.has(request.id) ? (
                        <>
                          <Check className="w-4 h-4" />
                          Prayed
                        </>
                      ) : (
                        <>
                          <Heart className="w-4 h-4" />
                          Pray
                        </>
                      )}
                      <span className="prayer-count">{request.prayer_count || 0}</span>
                    </button>
                  </div>
                </motion.div>
              ))}
            </div>
          )
        ) : (
          /* My Requests */
          myRequests.length === 0 ? (
            <div className="prayer-empty">
              <MessageCircle className="w-12 h-12" />
              <h3>No prayer requests</h3>
              <p>You haven't submitted any prayer requests yet</p>
              <button onClick={() => setShowNewRequest(true)} className="prayer-empty-btn">
                Submit Your First Request
              </button>
            </div>
          ) : (
            <div className="prayer-my-list">
              {myRequests.map(request => (
                <motion.div
                  key={request.id}
                  className="prayer-my-card"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  data-testid={`my-prayer-${request.id}`}
                >
                  <div className="prayer-my-header">
                    <span className="prayer-card-category">
                      {CATEGORIES.find(c => c.id === request.category)?.icon} {request.category}
                    </span>
                    {getStatusBadge(request.status)}
                  </div>
                  <h3 className="prayer-my-title">{request.title}</h3>
                  <p className="prayer-my-content">{request.content}</p>
                  <div className="prayer-my-footer">
                    <span className="prayer-my-date">
                      <Clock className="w-4 h-4" />
                      {formatDate(request.created_at)}
                    </span>
                    <div className="prayer-my-meta">
                      {request.is_public && (
                        <span className="prayer-visibility public">
                          <Globe className="w-3 h-3" /> Public
                        </span>
                      )}
                      {request.is_anonymous && (
                        <span className="prayer-visibility anonymous">Anonymous</span>
                      )}
                      <span className="prayer-count-badge">
                        🙏 {request.prayer_count || 0} prayers
                      </span>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )
        )}
      </div>

      {/* New Request Modal */}
      <AnimatePresence>
        {showNewRequest && (
          <motion.div
            className="prayer-modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowNewRequest(false)}
          >
            <motion.div
              className="prayer-modal"
              initial={{ scale: 0.9, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.9, opacity: 0, y: 20 }}
              onClick={(e) => e.stopPropagation()}
              data-testid="prayer-modal"
            >
              <button 
                className="prayer-modal-close"
                onClick={() => setShowNewRequest(false)}
              >
                <X className="w-5 h-5" />
              </button>

              <div className="prayer-modal-header">
                <Heart className="w-6 h-6 text-rose-500" />
                <h2>Submit Prayer Request</h2>
              </div>

              <div className="prayer-modal-form">
                {/* Category */}
                <div className="prayer-form-group">
                  <label>Category</label>
                  <div className="prayer-category-select">
                    {CATEGORIES.map(cat => (
                      <button
                        key={cat.id}
                        type="button"
                        className={`prayer-cat-btn ${newRequest.category === cat.id ? 'active' : ''}`}
                        onClick={() => setNewRequest(prev => ({ ...prev, category: cat.id }))}
                      >
                        {cat.icon} {cat.name}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Title */}
                <div className="prayer-form-group">
                  <label>Title</label>
                  <input
                    type="text"
                    placeholder="Brief title for your request"
                    value={newRequest.title}
                    onChange={(e) => setNewRequest(prev => ({ ...prev, title: e.target.value }))}
                    data-testid="prayer-title-input"
                  />
                </div>

                {/* Content */}
                <div className="prayer-form-group">
                  <label>Your Prayer Request</label>
                  <textarea
                    placeholder="Share what's on your heart..."
                    rows={4}
                    value={newRequest.content}
                    onChange={(e) => setNewRequest(prev => ({ ...prev, content: e.target.value }))}
                    data-testid="prayer-content-input"
                  />
                </div>

                {/* Options */}
                <div className="prayer-form-options">
                  <label className="prayer-checkbox">
                    <input
                      type="checkbox"
                      checked={newRequest.is_public}
                      onChange={(e) => setNewRequest(prev => ({ ...prev, is_public: e.target.checked }))}
                    />
                    <Globe className="w-4 h-4" />
                    <span>Share on Prayer Wall</span>
                  </label>
                  {newRequest.is_public && (
                    <label className="prayer-checkbox sub">
                      <input
                        type="checkbox"
                        checked={newRequest.is_anonymous}
                        onChange={(e) => setNewRequest(prev => ({ ...prev, is_anonymous: e.target.checked }))}
                      />
                      <span>Post anonymously</span>
                    </label>
                  )}
                </div>

                <button 
                  className="prayer-submit-btn"
                  onClick={submitRequest}
                  data-testid="submit-prayer-btn"
                >
                  <Send className="w-5 h-5" />
                  Submit Prayer Request
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
