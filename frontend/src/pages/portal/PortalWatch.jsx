import { useState, useRef, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Play, ChevronLeft, ChevronRight, Clock, Search, Plus, X,
  BookmarkPlus, Info, LayoutGrid, Rows3, User, Sparkles,
  Heart, Users, Briefcase, Music, Book, Home, ChevronDown
} from 'lucide-react';
import { API_URL } from '@/lib/utils';

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
// VIDEO PLAYER MODAL
// ═══════════════════════════════════════════════════════════════════════════════

const VideoPlayer = ({ isOpen, onClose, video }) => {
  if (!isOpen || !video) return null;

  return (
    <motion.div
      className="atv-modal"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        className="atv-modal-content"
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
      >
        <button className="atv-modal-close" onClick={onClose}>
          <X className="w-6 h-6" />
        </button>
        <div className="atv-modal-header">
          <h2>{video.title}</h2>
          <p>With {video.instructor}</p>
        </div>
        <div className="atv-modal-video">
          <iframe
            src={`https://www.youtube.com/embed/${video.youtubeId}?autoplay=1&rel=0&modestbranding=1`}
            title={video.title}
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          />
        </div>
      </motion.div>
    </motion.div>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// HERO SECTION
// ═══════════════════════════════════════════════════════════════════════════════

const HeroSection = ({ content, onPlay }) => {
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
              <button className="atv-btn-primary" onClick={() => onPlay(current)}>
                <Play className="w-5 h-5" fill="currentColor" />
                Watch Now
              </button>
              <button className="atv-btn-secondary">
                <Plus className="w-5 h-5" />
                My List
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

const ContentCard = ({ item, onPlay, viewMode }) => {
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
              <button className="atv-play-btn" onClick={() => onPlay(item)}>
                <Play className="w-6 h-6" fill="currentColor" />
              </button>
              <button className="atv-add-btn">
                <Plus className="w-5 h-5" />
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
      
      <div className="atv-card-info">
        <p className="atv-card-meta">{item.duration} • {item.category}</p>
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

const CarouselRow = ({ title, items, onPlay }) => {
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
          <ContentCard key={item.id} item={item} onPlay={onPlay} viewMode="carousel" />
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
  const [allContent, setAllContent] = useState([]);
  const [loading, setLoading] = useState(true);

  // Fetch videos from database
  useEffect(() => {
    fetchVideos();
  }, []);

  const fetchVideos = async () => {
    try {
      const res = await fetch(`${API_URL}/portal/media/videos`, { credentials: 'include' });
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
          <span className="atv-logo-text">{churchName} TV</span>
        </div>

        <div className="atv-search">
          <Search className="w-4 h-4" />
          <input
            type="text"
            placeholder="Search sermons, topics, speakers..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="atv-header-actions">
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
            <HeroSection content={allContent} onPlay={(v) => setVideoModal({ open: true, video: v })} />
            
            {/* Carousels */}
            {newContent.length > 0 && <CarouselRow title="New This Week" items={newContent} onPlay={(v) => setVideoModal({ open: true, video: v })} />}
            {popularContent.length > 0 && <CarouselRow title="Popular Series" items={popularContent} onPlay={(v) => setVideoModal({ open: true, video: v })} />}
            {faithContent.length > 0 && <CarouselRow title="Faith & Spirituality" items={faithContent} onPlay={(v) => setVideoModal({ open: true, video: v })} />}
            {growthContent.length > 0 && <CarouselRow title="Personal Growth" items={growthContent} onPlay={(v) => setVideoModal({ open: true, video: v })} />}
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
                <ContentCard key={item.id} item={item} onPlay={(v) => setVideoModal({ open: true, video: v })} viewMode="grid" />
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
          />
        )}
      </AnimatePresence>
    </div>
  );
}
