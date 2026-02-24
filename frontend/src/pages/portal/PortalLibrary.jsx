import { useState, useRef, useEffect, useCallback } from 'react';
import { useOutletContext, useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Search, ChevronDown, ChevronLeft, ChevronRight, Play, Plus, X, Clock,
  User, LayoutGrid, Sparkles, Music, ArrowRight, CheckCircle, RotateCcw,
  Briefcase, Home, Users, Heart, Book, Volume2, Bookmark, DollarSign, Calendar, Tv
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

// ═══════════════════════════════════════════════════════════════════════════════
// PORTAL NAVIGATION - Premium Dark Theme
// ═══════════════════════════════════════════════════════════════════════════════

const PORTAL_NAV = [
  { name: 'Home', path: '/portal', icon: Home },
  { name: 'Watch', path: '/portal/library', icon: Tv },
  { name: 'Give', path: '/portal/give', icon: DollarSign },
  { name: 'Groups', path: '/portal/groups', icon: Users },
  { name: 'Events', path: '/portal/events', icon: Calendar },
  { name: 'Me', path: '/portal/me', icon: User },
];

// ═══════════════════════════════════════════════════════════════════════════════
// ABUNDANT MEDIA - Premium Cinematic Experience
// Inspired by MasterClass + Prada + Eden-X.io + Netflix Continue Watching
// ═══════════════════════════════════════════════════════════════════════════════

const CATEGORIES = [
  { id: 'all', label: 'All', icon: LayoutGrid },
  { id: 'faith', label: 'Faith', icon: Heart },
  { id: 'family', label: 'Family', icon: Users },
  { id: 'leadership', label: 'Leadership', icon: Briefcase },
  { id: 'worship', label: 'Worship', icon: Music },
  { id: 'growth', label: 'Growth', icon: Book },
  { id: 'community', label: 'Community', icon: Home },
];

// Helper to parse duration string to seconds
const parseDuration = (duration) => {
  if (!duration) return 0;
  const parts = duration.split(':').map(Number);
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
  if (parts.length === 2) return parts[0] * 60 + parts[1];
  return 0;
};

// Videos will be fetched from database - no hardcoded content

// ═══════════════════════════════════════════════════════════════════════════════
// VIDEO PLAYER MODAL - With Progress Tracking
// ═══════════════════════════════════════════════════════════════════════════════

const VideoPlayerModal = ({ isOpen, onClose, course, onProgressUpdate, initialPosition = 0 }) => {
  const iframeRef = useRef(null);
  const progressInterval = useRef(null);
  const [currentTime, setCurrentTime] = useState(initialPosition);

  useEffect(() => {
    if (isOpen && course) {
      // Start tracking progress every 10 seconds
      progressInterval.current = setInterval(() => {
        // Increment simulated time (since we can't get exact time from YouTube iframe without API)
        setCurrentTime(prev => {
          const newTime = prev + 10;
          // Save progress
          onProgressUpdate(course, newTime);
          return newTime;
        });
      }, 10000);
    }

    return () => {
      if (progressInterval.current) {
        clearInterval(progressInterval.current);
      }
    };
  }, [isOpen, course, onProgressUpdate]);

  const handleClose = () => {
    // Save final progress on close
    if (course && currentTime > 0) {
      onProgressUpdate(course, currentTime);
    }
    onClose();
  };

  if (!isOpen || !course) return null;

  // Calculate start time for YouTube
  const startTime = initialPosition > 0 ? `&start=${Math.floor(initialPosition)}` : '';

  return (
    <motion.div
      className="prem-modal"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={handleClose}
      data-testid="video-player-modal"
    >
      <motion.div
        className="prem-modal-content"
        initial={{ scale: 0.95, opacity: 0, y: 20 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        exit={{ scale: 0.95, opacity: 0, y: 20 }}
        transition={{ duration: 0.3, ease: [0.23, 1, 0.32, 1] }}
        onClick={(e) => e.stopPropagation()}
      >
        <button className="prem-modal-close" onClick={handleClose} data-testid="video-close-btn">
          <X className="w-5 h-5" />
        </button>
        <div className="prem-modal-header">
          <span className="prem-modal-label">Now Playing</span>
          <h2>{course.title}</h2>
          <p>{course.instructor}</p>
        </div>
        <div className="prem-modal-video">
          <iframe
            ref={iframeRef}
            src={`https://www.youtube.com/embed/${course.youtubeId}?autoplay=1&rel=0&modestbranding=1${startTime}&enablejsapi=1`}
            title={course.title}
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          />
        </div>
      </motion.div>
    </motion.div>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// CONTINUE WATCHING SECTION - Netflix-style
// ═══════════════════════════════════════════════════════════════════════════════

const ContinueWatchingSection = ({ items, onPlay, onRemove }) => {
  const scrollRef = useRef(null);

  if (!items || items.length === 0) return null;

  const scroll = (direction) => {
    if (scrollRef.current) {
      const amount = direction === 'left' ? -400 : 400;
      scrollRef.current.scrollBy({ left: amount, behavior: 'smooth' });
    }
  };

  return (
    <section className="prem-continue" data-testid="continue-watching-section">
      <div className="prem-continue-header">
        <div className="prem-continue-title">
          <RotateCcw className="w-5 h-5" />
          <h2>Continue Watching</h2>
        </div>
        <span className="prem-continue-count">{items.length} in progress</span>
      </div>
      
      <div className="prem-continue-wrapper">
        <button className="prem-scroll-btn left" onClick={() => scroll('left')}>
          <ChevronLeft className="w-5 h-5" />
        </button>
        
        <div className="prem-continue-scroll" ref={scrollRef}>
          {items.map((item, index) => (
            <motion.div
              key={item.video_id}
              className="prem-continue-card"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              data-testid={`continue-card-${item.video_id}`}
            >
              <div className="prem-continue-thumb" onClick={() => onPlay(item)}>
                <img src={item.thumbnail} alt={item.title} />
                <div className="prem-continue-overlay">
                  <Play className="w-10 h-10" fill="currentColor" />
                </div>
                <div className="prem-progress-bar">
                  <div 
                    className="prem-progress-fill"
                    style={{ width: `${item.progress_percent}%` }}
                  />
                </div>
              </div>
              <div className="prem-continue-info">
                <h4>{item.title}</h4>
                <p>{item.instructor}</p>
                <span className="prem-continue-time">
                  {Math.round(item.progress_percent)}% • {Math.floor((item.duration_seconds - item.position_seconds) / 60)} min left
                </span>
              </div>
            </motion.div>
          ))}
        </div>
        
        <button className="prem-scroll-btn right" onClick={() => scroll('right')}>
          <ChevronRight className="w-5 h-5" />
        </button>
      </div>
    </section>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// HERO SECTION - Prada-style Cinematic Hero
// ═══════════════════════════════════════════════════════════════════════════════

const HeroSection = ({ content, onPlay, watchProgress }) => {
  const [activeIndex, setActiveIndex] = useState(0);
  const featured = content.filter(c => c.featured).slice(0, 4);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveIndex((prev) => (prev + 1) % featured.length);
    }, 7000);
    return () => clearInterval(interval);
  }, [featured.length]);

  const current = featured[activeIndex];
  if (!current) return null;

  // Check if hero video has progress
  const progress = watchProgress[current.id];

  return (
    <section className="prem-hero" data-testid="hero-section">
      <AnimatePresence mode="wait">
        <motion.div
          key={current.id}
          className="prem-hero-bg"
          style={{ backgroundImage: `url(${current.thumbnail})` }}
          initial={{ opacity: 0, scale: 1.05 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 1.2, ease: [0.23, 1, 0.32, 1] }}
        />
      </AnimatePresence>
      
      <div className="prem-hero-overlay" />
      <div className="prem-hero-grain" />
      
      <div className="prem-hero-content">
        <AnimatePresence mode="wait">
          <motion.div
            key={current.id}
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            {current.badge && (
              <motion.span 
                className="prem-hero-badge"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 }}
              >
                {current.badge}
              </motion.span>
            )}
            <h1 className="prem-hero-title">{current.title}</h1>
            <p className="prem-hero-instructor">{current.instructor}</p>
            <p className="prem-hero-desc">{current.description}</p>
            <div className="prem-hero-meta">
              <span><Clock className="w-4 h-4" /> {current.duration}</span>
              <span className="prem-meta-dot">•</span>
              <span>{current.category}</span>
              {progress && progress.progress_percent > 0 && (
                <>
                  <span className="prem-meta-dot">•</span>
                  <span className="prem-hero-progress">{Math.round(progress.progress_percent)}% watched</span>
                </>
              )}
            </div>
            <div className="prem-hero-actions">
              <motion.button 
                className="prem-btn-play"
                onClick={() => onPlay(current)}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                data-testid="hero-play-btn"
              >
                <Play className="w-5 h-5" fill="currentColor" />
                {progress && progress.progress_percent > 0 ? 'Resume' : 'Watch Now'}
              </motion.button>
              <motion.button 
                className="prem-btn-save"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Bookmark className="w-5 h-5" />
              </motion.button>
            </div>
          </motion.div>
        </AnimatePresence>
        
        <div className="prem-hero-nav">
          {featured.map((_, i) => (
            <button
              key={i}
              className={`prem-nav-dot ${activeIndex === i ? 'active' : ''}`}
              onClick={() => setActiveIndex(i)}
            />
          ))}
        </div>
      </div>
    </section>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// COURSE CARD - Premium Glass Card with Progress
// ═══════════════════════════════════════════════════════════════════════════════

const CourseCard = ({ course, onPlay, index, progress }) => {
  const [isHovered, setIsHovered] = useState(false);
  const hasProgress = progress && progress.progress_percent > 0;
  const isCompleted = progress && progress.completed;

  return (
    <motion.article 
      className={`prem-card ${isCompleted ? 'completed' : ''}`}
      data-testid={`course-card-${course.id}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: index * 0.05, ease: [0.23, 1, 0.32, 1] }}
      whileHover={{ y: -8 }}
    >
      <div className="prem-card-thumb">
        <motion.img 
          src={course.thumbnail} 
          alt={course.title}
          loading="lazy"
          animate={{ scale: isHovered ? 1.08 : 1 }}
          transition={{ duration: 0.6, ease: [0.23, 1, 0.32, 1] }}
          onError={(e) => {
            e.target.src = `https://img.youtube.com/vi/${course.youtubeId}/hqdefault.jpg`;
          }}
        />
        
        {isCompleted && (
          <span className="prem-badge completed">
            <CheckCircle className="w-3 h-3" /> Watched
          </span>
        )}
        
        {!isCompleted && course.badge && (
          <span className={`prem-badge ${course.badge.toLowerCase()}`}>
            {course.badge}
          </span>
        )}
        
        <span className="prem-duration">
          <Clock className="w-3 h-3" />
          {course.duration}
        </span>

        {/* Progress bar */}
        {hasProgress && !isCompleted && (
          <div className="prem-card-progress">
            <div 
              className="prem-card-progress-fill"
              style={{ width: `${progress.progress_percent}%` }}
            />
          </div>
        )}

        <AnimatePresence>
          {isHovered && (
            <motion.div 
              className="prem-card-overlay"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              <motion.button 
                className="prem-card-play"
                onClick={(e) => { e.stopPropagation(); onPlay(course); }}
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.8, opacity: 0 }}
                transition={{ delay: 0.1 }}
                whileHover={{ scale: 1.1 }}
                data-testid={`play-btn-${course.id}`}
              >
                <Play className="w-6 h-6" fill="currentColor" />
              </motion.button>
              <motion.button 
                className="prem-card-save"
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.8, opacity: 0 }}
                transition={{ delay: 0.15 }}
                whileHover={{ scale: 1.1 }}
              >
                <Plus className="w-5 h-5" />
              </motion.button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <div className="prem-card-info">
        <p className="prem-card-meta">
          {course.format} • {course.category}
          {hasProgress && !isCompleted && (
            <span className="prem-card-progress-text"> • {Math.round(progress.progress_percent)}%</span>
          )}
        </p>
        <h3 className="prem-card-title">{course.title}</h3>
        <p className="prem-card-instructor">{course.instructor}</p>
      </div>

      <AnimatePresence>
        {isHovered && course.description && (
          <motion.div 
            className="prem-card-desc"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
          >
            <p>{course.description}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.article>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN LIBRARY PAGE
// ═══════════════════════════════════════════════════════════════════════════════

export default function PortalLibrary() {
  const { user } = useOutletContext();
  const navigate = useNavigate();
  const location = useLocation();
  
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState('all');
  const [allCourses, setAllCourses] = useState([]);
  const [filteredCourses, setFilteredCourses] = useState([]);
  const [videoModal, setVideoModal] = useState({ open: false, course: null, startPosition: 0 });
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const [loading, setLoading] = useState(true);
  
  // Watch progress state
  const [continueWatching, setContinueWatching] = useState([]);
  const [watchProgress, setWatchProgress] = useState({});
  const [completedCount, setCompletedCount] = useState(0);

  // Fetch videos from database
  useEffect(() => {
    const fetchVideos = async () => {
      try {
        const res = await fetch(`${API_URL}/api/portal/media/videos`, {
          credentials: 'include'
        });
        if (res.ok) {
          const data = await res.json();
          // Transform database format to UI format
          const transformed = (data.videos || []).map(v => ({
            id: v.id,
            title: v.title,
            instructor: v.instructor || 'Unknown Speaker',
            format: 'Class',
            duration: v.duration || '30:00',
            durationSeconds: parseDuration(v.duration) || 1800,
            category: v.category_id || 'faith',
            badge: v.badge || (v.is_featured ? 'Featured' : null),
            youtubeId: v.youtube_id,
            thumbnail: v.thumbnail_url || `https://i.ytimg.com/vi/${v.youtube_id}/maxresdefault.jpg`,
            description: v.description || '',
            featured: v.is_featured || false
          }));
          setAllCourses(transformed);
          setFilteredCourses(transformed);
        }
      } catch (err) {
        console.error('Error fetching videos:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchVideos();
  }, []);

  // Fetch watch progress on mount
  useEffect(() => {
    const fetchProgress = async () => {
      try {
        const res = await fetch(`${API_URL}/api/portal/watch/progress`, {
          credentials: 'include'
        });
        if (res.ok) {
          const data = await res.json();
          setContinueWatching(data.continue_watching || []);
          setCompletedCount(data.total_watched || 0);
          
          // Build progress map by video_id
          const progressMap = {};
          [...(data.continue_watching || []), ...(data.completed || [])].forEach(p => {
            progressMap[p.video_id] = p;
          });
          setWatchProgress(progressMap);
        }
      } catch (err) {
        console.error('Error fetching watch progress:', err);
      }
    };
    fetchProgress();
  }, []);

  // Save progress to backend
  const saveProgress = useCallback(async (course, positionSeconds) => {
    try {
      await fetch(`${API_URL}/api/portal/watch/progress`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          video_id: String(course.id),
          youtube_id: course.youtubeId,
          position_seconds: Math.floor(positionSeconds),
          duration_seconds: course.durationSeconds || parseDuration(course.duration),
          title: course.title,
          thumbnail: course.thumbnail,
          instructor: course.instructor
        })
      });
      
      // Update local state
      const progressPercent = (positionSeconds / (course.durationSeconds || parseDuration(course.duration))) * 100;
      setWatchProgress(prev => ({
        ...prev,
        [course.id]: {
          ...prev[course.id],
          video_id: String(course.id),
          position_seconds: positionSeconds,
          progress_percent: progressPercent,
          completed: progressPercent >= 90
        }
      }));
    } catch (err) {
      console.error('Error saving progress:', err);
    }
  }, []);

  // Handle playing a video (from Continue Watching or regular)
  const handlePlay = useCallback((item) => {
    // Find the full course data from fetched courses
    const course = allCourses.find(c => String(c.id) === String(item.id || item.video_id)) || item;
    const startPosition = item.position_seconds || watchProgress[course.id]?.position_seconds || 0;
    
    setVideoModal({ 
      open: true, 
      course: { ...course, ...item },
      startPosition 
    });
  }, [watchProgress, allCourses]);

  // Filter courses based on search and category
  useEffect(() => {
    let result = [...allCourses];

    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      result = result.filter(c => 
        c.title?.toLowerCase().includes(q) ||
        c.instructor?.toLowerCase().includes(q) ||
        c.category?.toLowerCase().includes(q)
      );
    }

    if (activeCategory !== 'all') {
      const catMap = {
        'faith': 'Faith & Spirituality',
        'family': 'Family & Relationships',
        'leadership': 'Leadership',
        'worship': 'Worship',
        'growth': 'Personal Growth',
        'community': 'Community',
      };
      result = result.filter(c => c.category === catMap[activeCategory] || c.category === activeCategory);
    }

    setFilteredCourses(result);
  }, [searchQuery, activeCategory, allCourses]);

  return (
    <div className="prem-page" data-testid="library-page">
      {/* Ambient Light Effect */}
      <div className="prem-ambient" />
      
      {/* Premium Header */}
      <header className="prem-header">
        <motion.div 
          className="prem-logo"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6 }}
          onClick={() => navigate('/portal')}
          style={{ cursor: 'pointer' }}
        >
          <span className="prem-logo-mark">A</span>
          <span className="prem-logo-text">ABUNDANT</span>
        </motion.div>

        {/* Portal Navigation */}
        <nav className="prem-nav" data-testid="portal-nav">
          {PORTAL_NAV.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path || 
              (item.path === '/portal/library' && location.pathname === '/portal/library');
            return (
              <motion.button
                key={item.path}
                className={`prem-nav-item ${isActive ? 'active' : ''}`}
                onClick={() => navigate(item.path)}
                whileHover={{ y: -2 }}
                whileTap={{ scale: 0.98 }}
                data-testid={`nav-${item.name.toLowerCase()}`}
              >
                <Icon className="w-4 h-4" />
                <span>{item.name}</span>
              </motion.button>
            );
          })}
        </nav>

        <motion.div 
          className="prem-user"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.4, delay: 0.3 }}
        >
          {completedCount > 0 && (
            <span className="prem-user-stats">
              <CheckCircle className="w-4 h-4" />
              {completedCount}
            </span>
          )}
          <div className="prem-avatar">{user?.name?.charAt(0) || 'M'}</div>
          <span className="prem-user-name">{user?.name?.split(' ')[0] || 'Member'}</span>
        </motion.div>
      </header>

      {/* Cinematic Red Line */}
      <div className="prem-cinema-line" />

      {/* Hero Section */}
      <HeroSection 
        content={COURSES} 
        onPlay={handlePlay}
        watchProgress={watchProgress}
      />

      {/* Continue Watching Section */}
      <ContinueWatchingSection 
        items={continueWatching}
        onPlay={handlePlay}
      />

      {/* Category Pills + Search */}
      <motion.nav 
        className="prem-categories"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.4 }}
      >
        <div className="prem-categories-row">
          <div className="prem-categories-inner">
            {CATEGORIES.map((cat, i) => {
              const Icon = cat.icon;
              return (
                <motion.button
                  key={cat.id}
                  className={`prem-cat ${activeCategory === cat.id ? 'active' : ''}`}
                  onClick={() => setActiveCategory(cat.id)}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5 + i * 0.05 }}
                  whileHover={{ y: -2 }}
                  whileTap={{ scale: 0.98 }}
                  data-testid={`category-${cat.id}`}
                >
                  <Icon className="w-4 h-4" />
                  {cat.label}
                </motion.button>
              );
            })}
          </div>
          
          {/* Search in categories row */}
          <div className={`prem-search ${isSearchFocused ? 'focused' : ''}`}>
            <Search className="prem-search-icon" />
            <input 
              type="text"
              placeholder="Search sermons..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onFocus={() => setIsSearchFocused(true)}
              onBlur={() => setIsSearchFocused(false)}
              data-testid="search-input"
            />
          </div>
        </div>
      </motion.nav>

      {/* Content Grid */}
      <main className="prem-main">
        <motion.div 
          className="prem-section-header"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
        >
          <h2>
            {activeCategory === 'all' ? 'All Sermons' : CATEGORIES.find(c => c.id === activeCategory)?.label}
          </h2>
          <span className="prem-count">{filteredCourses.length} classes</span>
        </motion.div>

        {loading ? (
          <motion.div 
            className="prem-empty"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <div className="animate-spin w-8 h-8 border-2 border-white/20 border-t-white rounded-full" />
            <p>Loading content...</p>
          </motion.div>
        ) : allCourses.length === 0 ? (
          <motion.div 
            className="prem-empty"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <Tv className="w-12 h-12" />
            <h3>No videos available yet</h3>
            <p>Check back soon for new content from your church</p>
          </motion.div>
        ) : filteredCourses.length > 0 ? (
          <div className="prem-grid">
            {filteredCourses.map((course, index) => (
              <CourseCard 
                key={course.id} 
                course={course} 
                index={index}
                progress={watchProgress[course.id]}
                onPlay={handlePlay}
              />
            ))}
          </div>
        ) : (
          <motion.div 
            className="prem-empty"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <Search className="w-12 h-12" />
            <h3>No results found</h3>
            <p>Try adjusting your search or filters</p>
          </motion.div>
        )}
      </main>

      {/* Footer CTA */}
      <motion.footer 
        className="prem-footer"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
      >
        <div className="prem-footer-content">
          <div className="prem-footer-text">
            <h3>Experience Sunday Live</h3>
            <p>Join us every Sunday at 9am & 11am for live worship</p>
          </div>
          <button className="prem-footer-btn">
            Watch Live
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </motion.footer>

      {/* Video Modal */}
      <AnimatePresence>
        {videoModal.open && (
          <VideoPlayerModal 
            isOpen={videoModal.open}
            course={videoModal.course}
            initialPosition={videoModal.startPosition}
            onClose={() => setVideoModal({ open: false, course: null, startPosition: 0 })}
            onProgressUpdate={saveProgress}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
