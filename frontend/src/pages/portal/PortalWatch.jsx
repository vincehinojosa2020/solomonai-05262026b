import { useState, useRef, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Play, ChevronLeft, ChevronRight, Clock, Search, Plus, X,
  BookmarkPlus, Info, LayoutGrid, Rows3, User, Sparkles,
  Heart, Users, Briefcase, Music, Book, Home, ChevronDown
} from 'lucide-react';

// ═══════════════════════════════════════════════════════════════════════════════
// ABUNDANT TV - Unified Watch & Library Experience
// Best of MasterClass: Hero + Carousels + Grid + Filters
// ═══════════════════════════════════════════════════════════════════════════════

// Categories
const CATEGORIES = [
  { id: 'all', label: 'All', icon: LayoutGrid },
  { id: 'faith', label: 'Faith', icon: Heart },
  { id: 'family', label: 'Family', icon: Users },
  { id: 'leadership', label: 'Leadership', icon: Briefcase },
  { id: 'worship', label: 'Worship', icon: Music },
  { id: 'growth', label: 'Growth', icon: Book },
  { id: 'community', label: 'Community', icon: Home },
];

// Real Abundant Church YouTube Videos
const ALL_CONTENT = [
  { 
    id: 1, 
    title: "Community With a Purpose", 
    instructor: "Pastor Charles Nieman", 
    duration: "40:45", 
    category: "community",
    badge: "New",
    youtubeId: "FoPI3hMbXvw",
    thumbnail: "https://i.ytimg.com/vi/FoPI3hMbXvw/maxresdefault.jpg",
    description: "Discover how the church is God's purposeful community - not a club but a family with divine purpose.",
    featured: true,
  },
  { 
    id: 2, 
    title: "Blessing & Healing Through Humility", 
    instructor: "Pastor Charles Nieman", 
    duration: "38:30", 
    category: "faith",
    badge: "New",
    youtubeId: "pzpbbibEWPE",
    thumbnail: "https://i.ytimg.com/vi/pzpbbibEWPE/maxresdefault.jpg",
    description: "Learn how humility unlocks God's blessings and healing in your life.",
    featured: true,
  },
  { 
    id: 3, 
    title: "Building Your Life", 
    instructor: "Pastor Charles Nieman", 
    duration: "45:00", 
    category: "growth",
    youtubeId: "Lnj6vMvOLME",
    thumbnail: "https://i.ytimg.com/vi/Lnj6vMvOLME/maxresdefault.jpg",
    description: "Build your life on God's Word - biblical principles for personal spiritual development.",
  },
  { 
    id: 4, 
    title: "The Missing Peace", 
    instructor: "Pastor Charles Nieman", 
    duration: "38:30", 
    category: "faith",
    youtubeId: "OjhMsB6czxc",
    thumbnail: "https://i.ytimg.com/vi/OjhMsB6czxc/maxresdefault.jpg",
    description: "Find God's inner peace through grace and righteousness.",
    featured: true,
  },
  { 
    id: 5, 
    title: "The Laws of Life", 
    instructor: "Pastor Charles Nieman", 
    duration: "37:57", 
    category: "growth",
    youtubeId: "WQy48ANpj5c",
    thumbnail: "https://i.ytimg.com/vi/WQy48ANpj5c/maxresdefault.jpg",
    description: "Your thoughts and beliefs shape your outcomes - learn the laws that govern life.",
  },
  { 
    id: 6, 
    title: "The Story Behind the Story", 
    instructor: "Pastor Charles Nieman", 
    duration: "37:30", 
    category: "faith",
    youtubeId: "wCjwUQMhCIY",
    thumbnail: "https://i.ytimg.com/vi/wCjwUQMhCIY/maxresdefault.jpg",
    description: "Discover the deeper meaning of Christmas and God's plan through Jesus' birth.",
  },
  { 
    id: 7, 
    title: "Managing Your Emotions", 
    instructor: "Pastor Charles Nieman", 
    duration: "42:00", 
    category: "growth",
    badge: "Popular",
    youtubeId: "0grr2E0kuFg",
    thumbnail: "https://i.ytimg.com/vi/0grr2E0kuFg/maxresdefault.jpg",
    description: "Biblical wisdom on understanding and handling your emotions effectively.",
  },
  { 
    id: 8, 
    title: "Worship In Spirit & In Truth", 
    instructor: "Pastor Jared Nieman", 
    duration: "35:00", 
    category: "worship",
    youtubeId: "uwkmP6sDihI",
    thumbnail: "https://i.ytimg.com/vi/uwkmP6sDihI/maxresdefault.jpg",
    description: "Experience authentic worship that transforms your relationship with God.",
  },
  { 
    id: 9, 
    title: "Vision Sunday 2025", 
    instructor: "Pastor Jared Nieman", 
    duration: "48:00", 
    category: "leadership",
    youtubeId: "O0WfS3Ma2XM",
    thumbnail: "https://i.ytimg.com/vi/O0WfS3Ma2XM/maxresdefault.jpg",
    description: "The church's vision and community outreach efforts for the year ahead.",
  },
  { 
    id: 10, 
    title: "Abundant Conference 2025", 
    instructor: "Pastor Marcos Witt", 
    duration: "1:20:00", 
    category: "worship",
    badge: "Featured",
    youtubeId: "kGXOOO6hHUk",
    thumbnail: "https://i.ytimg.com/vi/kGXOOO6hHUk/maxresdefault.jpg",
    description: "Night 2 of the Abundant Conference featuring worship and powerful teaching.",
    featured: true,
  },
  { 
    id: 11, 
    title: "We Are Abundant", 
    instructor: "Pastor Charles Nieman", 
    duration: "40:00", 
    category: "community",
    youtubeId: "rMmIcJCDsaU",
    thumbnail: "https://i.ytimg.com/vi/rMmIcJCDsaU/maxresdefault.jpg",
    description: "Understanding our calling to be a blessing to others in our community.",
  },
  { 
    id: 12, 
    title: "Faith That Moves Mountains", 
    instructor: "Pastor Charles Nieman", 
    duration: "36:00", 
    category: "faith",
    youtubeId: "Lnj6vMvOLME",
    thumbnail: "https://i.ytimg.com/vi/Lnj6vMvOLME/maxresdefault.jpg",
    description: "Discover the kind of faith that can move any mountain in your life.",
  },
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
// MAIN COMPONENT
// ═══════════════════════════════════════════════════════════════════════════════

export default function PortalWatch() {
  const { user } = useOutletContext();
  const [viewMode, setViewMode] = useState('featured'); // 'featured' or 'browse'
  const [activeCategory, setActiveCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [videoModal, setVideoModal] = useState({ open: false, video: null });

  // Filter content
  const filteredContent = ALL_CONTENT.filter(item => {
    const matchesCategory = activeCategory === 'all' || item.category === activeCategory;
    const matchesSearch = !searchQuery || 
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.instructor.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  // Group content for carousels
  const newContent = ALL_CONTENT.filter(c => c.badge === 'New');
  const popularContent = ALL_CONTENT.filter(c => c.badge === 'Popular' || c.badge === 'Featured');
  const faithContent = ALL_CONTENT.filter(c => c.category === 'faith');
  const growthContent = ALL_CONTENT.filter(c => c.category === 'growth');

  return (
    <div className="atv-page" data-testid="watch-page">
      {/* Cinema Red Bar */}
      <div className="atv-red-bar" />

      {/* Header */}
      <header className="atv-header">
        <div className="atv-logo">
          <span className="atv-logo-mark">A</span>
          <span className="atv-logo-text">Abundant TV</span>
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
            <HeroSection content={ALL_CONTENT} onPlay={(v) => setVideoModal({ open: true, video: v })} />
            
            {/* Carousels */}
            <CarouselRow title="New This Week" items={newContent} onPlay={(v) => setVideoModal({ open: true, video: v })} />
            <CarouselRow title="Popular Series" items={popularContent} onPlay={(v) => setVideoModal({ open: true, video: v })} />
            <CarouselRow title="Faith & Spirituality" items={faithContent} onPlay={(v) => setVideoModal({ open: true, video: v })} />
            <CarouselRow title="Personal Growth" items={growthContent} onPlay={(v) => setVideoModal({ open: true, video: v })} />
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
