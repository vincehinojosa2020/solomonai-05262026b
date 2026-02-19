import { useState, useRef, useEffect } from 'react';
import { useOutletContext, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Search, ChevronDown, ChevronLeft, ChevronRight, Play, Plus, X,
  User, LayoutGrid, Sparkles, Utensils, Music, Pen, 
  Gamepad2, Palette, Briefcase, Cpu, Home, Users, Film, Heart, Book
} from 'lucide-react';

// ═══════════════════════════════════════════════════════════════════════════════
// MASTERCLASS LIBRARY - Exact Clone with Abundant Church Videos
// ═══════════════════════════════════════════════════════════════════════════════

// Category data with icons - exactly like MasterClass
const CATEGORIES = [
  { id: 'all', label: 'All Categories', icon: LayoutGrid },
  { id: 'faith', label: 'Faith & Spirituality', icon: Heart },
  { id: 'family', label: 'Family & Relationships', icon: Users },
  { id: 'leadership', label: 'Leadership', icon: Briefcase },
  { id: 'worship', label: 'Worship', icon: Music },
  { id: 'growth', label: 'Personal Growth', icon: Book },
  { id: 'community', label: 'Community', icon: Home },
];

// Real Abundant Church YouTube Videos
const COURSES = [
  { 
    id: 1, 
    title: "Community With a Purpose", 
    instructor: "Pastor Charles Nieman", 
    format: "Class", 
    duration: "40:45", 
    category: "Community",
    badge: "New",
    youtubeId: "FoPI3hMbXvw",
    thumbnail: "https://i.ytimg.com/vi/FoPI3hMbXvw/maxresdefault.jpg",
    description: "Discover how the church is God's purposeful community - not a club but a family with divine purpose."
  },
  { 
    id: 2, 
    title: "Blessing & Healing Through Humility", 
    instructor: "Pastor Charles Nieman", 
    format: "Class", 
    duration: "38:30", 
    category: "Faith & Spirituality",
    badge: "New",
    youtubeId: "pzpbbibEWPE",
    thumbnail: "https://i.ytimg.com/vi/pzpbbibEWPE/maxresdefault.jpg",
    description: "Learn how humility unlocks God's blessings and healing in your life."
  },
  { 
    id: 3, 
    title: "Building Your Life", 
    instructor: "Pastor Charles Nieman", 
    format: "Class", 
    duration: "45:00", 
    category: "Personal Growth",
    youtubeId: "Lnj6vMvOLME",
    thumbnail: "https://i.ytimg.com/vi/Lnj6vMvOLME/maxresdefault.jpg",
    description: "Build your life on God's Word - biblical principles for personal spiritual development."
  },
  { 
    id: 4, 
    title: "The Missing Peace", 
    instructor: "Pastor Charles Nieman", 
    format: "Class", 
    duration: "38:30", 
    category: "Faith & Spirituality",
    youtubeId: "OjhMsB6czxc",
    thumbnail: "https://i.ytimg.com/vi/OjhMsB6czxc/maxresdefault.jpg",
    description: "Find God's inner peace through grace and righteousness."
  },
  { 
    id: 5, 
    title: "The Laws of Life", 
    instructor: "Pastor Charles Nieman", 
    format: "Class", 
    duration: "37:57", 
    category: "Personal Growth",
    youtubeId: "WQy48ANpj5c",
    thumbnail: "https://i.ytimg.com/vi/WQy48ANpj5c/maxresdefault.jpg",
    description: "Your thoughts and beliefs shape your outcomes - learn the laws that govern life."
  },
  { 
    id: 6, 
    title: "The Story Behind the Story", 
    instructor: "Pastor Charles Nieman", 
    format: "Class", 
    duration: "37:30", 
    category: "Faith & Spirituality",
    youtubeId: "wCjwUQMhCIY",
    thumbnail: "https://i.ytimg.com/vi/wCjwUQMhCIY/maxresdefault.jpg",
    description: "Discover the deeper meaning of Christmas and God's plan through Jesus' birth."
  },
  { 
    id: 7, 
    title: "Managing Your Emotions", 
    instructor: "Pastor Charles Nieman", 
    format: "Class", 
    duration: "42:00", 
    category: "Personal Growth",
    badge: "Popular",
    youtubeId: "0grr2E0kuFg",
    thumbnail: "https://i.ytimg.com/vi/0grr2E0kuFg/maxresdefault.jpg",
    description: "Biblical wisdom on understanding and handling your emotions effectively."
  },
  { 
    id: 8, 
    title: "Worship In Spirit & In Truth", 
    instructor: "Pastor Jared Nieman", 
    format: "Class", 
    duration: "35:00", 
    category: "Worship",
    youtubeId: "uwkmP6sDihI",
    thumbnail: "https://i.ytimg.com/vi/uwkmP6sDihI/maxresdefault.jpg",
    description: "Experience authentic worship that transforms your relationship with God."
  },
  { 
    id: 9, 
    title: "Vision Sunday 2025", 
    instructor: "Pastor Jared Nieman", 
    format: "Class", 
    duration: "48:00", 
    category: "Leadership",
    youtubeId: "O0WfS3Ma2XM",
    thumbnail: "https://i.ytimg.com/vi/O0WfS3Ma2XM/maxresdefault.jpg",
    description: "The church's vision and community outreach efforts for the year ahead."
  },
  { 
    id: 10, 
    title: "Abundant Conference 2025", 
    instructor: "Pastor Marcos Witt", 
    format: "Session", 
    duration: "1:20:00", 
    category: "Worship",
    badge: "Featured",
    youtubeId: "kGXOOO6hHUk",
    thumbnail: "https://i.ytimg.com/vi/kGXOOO6hHUk/maxresdefault.jpg",
    description: "Night 2 of the Abundant Conference featuring worship and powerful teaching."
  },
  { 
    id: 11, 
    title: "We Are Abundant: Blessed to Be a Blessing", 
    instructor: "Pastor Charles Nieman", 
    format: "Class", 
    duration: "40:00", 
    category: "Community",
    youtubeId: "rMmIcJCDsaU",
    thumbnail: "https://i.ytimg.com/vi/rMmIcJCDsaU/maxresdefault.jpg",
    description: "Understanding our calling to be a blessing to others in our community."
  },
  { 
    id: 12, 
    title: "Faith That Moves Mountains", 
    instructor: "Pastor Charles Nieman", 
    format: "Class", 
    duration: "36:00", 
    category: "Faith & Spirituality",
    youtubeId: "Lnj6vMvOLME",
    thumbnail: "https://i.ytimg.com/vi/Lnj6vMvOLME/maxresdefault.jpg",
    description: "Discover the kind of faith that can move any mountain in your life."
  },
];

// Filter options - exactly like MasterClass
const FILTER_OPTIONS = {
  format: ['Class', 'Session', 'Series'],
  myContent: ['Saved', 'In Progress', 'Completed'],
  duration: ['Under 30 min', '30-45 min', '45+ min'],
};

// ═══════════════════════════════════════════════════════════════════════════════
// VIDEO PLAYER MODAL - Fullscreen Cinema Experience
// ═══════════════════════════════════════════════════════════════════════════════

const VideoPlayerModal = ({ isOpen, onClose, course }) => {
  if (!isOpen || !course) return null;

  return (
    <motion.div
      className="mcl-video-modal"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        className="mcl-video-container"
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
      >
        <button className="mcl-video-close" onClick={onClose}>
          <X className="w-6 h-6" />
        </button>
        <div className="mcl-video-header">
          <h2>{course.title}</h2>
          <p>{course.instructor}</p>
        </div>
        <div className="mcl-video-player">
          <iframe
            src={`https://www.youtube.com/embed/${course.youtubeId}?autoplay=1&rel=0&modestbranding=1`}
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
// COURSE CARD - Exact MasterClass Style
// ═══════════════════════════════════════════════════════════════════════════════

const CourseCard = ({ course, onPlay }) => {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <motion.article 
      className="mcl-card"
      data-testid={`course-card-${course.id}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      {/* Thumbnail - Sharp corners, no padding */}
      <div className="mcl-card-thumb">
        <img 
          src={course.thumbnail} 
          alt={course.title}
          loading="lazy"
          onError={(e) => {
            e.target.src = `https://img.youtube.com/vi/${course.youtubeId}/hqdefault.jpg`;
          }}
        />
        
        {/* NEW/Popular Badge - Red, top right */}
        {course.badge && (
          <span className={`mcl-badge ${course.badge.toLowerCase()}`}>
            {course.badge}
          </span>
        )}
        
        {/* Duration - Bottom right */}
        <span className="mcl-duration">{course.duration}</span>

        {/* Hover Overlay with Play/Add Buttons */}
        <AnimatePresence>
          {isHovered && (
            <motion.div 
              className="mcl-card-hover"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <div className="mcl-card-btns">
                <button 
                  className="mcl-btn-play"
                  onClick={(e) => { e.stopPropagation(); onPlay(course); }}
                >
                  <Play className="w-5 h-5" fill="currentColor" />
                </button>
                <button className="mcl-btn-add">
                  <Plus className="w-5 h-5" />
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Card Info */}
      <div className="mcl-card-info">
        <p className="mcl-card-meta">
          {course.format} • {course.duration} • {course.category}
        </p>
        <h3 className="mcl-card-title">{course.title}</h3>
        <p className="mcl-card-instructor">With {course.instructor}</p>
      </div>

      {/* Hover Expansion - Description */}
      <AnimatePresence>
        {isHovered && course.description && (
          <motion.div 
            className="mcl-card-desc"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
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
  
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState('all');
  const [filters, setFilters] = useState({});
  const [filteredCourses, setFilteredCourses] = useState(COURSES);
  const [openAccordion, setOpenAccordion] = useState(null);
  const [videoModal, setVideoModal] = useState({ open: false, course: null });
  
  const categoryScrollRef = useRef(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(true);

  // Category scroll handlers
  const checkCategoryScroll = () => {
    if (categoryScrollRef.current) {
      const { scrollLeft, scrollWidth, clientWidth } = categoryScrollRef.current;
      setCanScrollLeft(scrollLeft > 0);
      setCanScrollRight(scrollLeft < scrollWidth - clientWidth - 10);
    }
  };

  const scrollCategories = (dir) => {
    if (categoryScrollRef.current) {
      categoryScrollRef.current.scrollBy({
        left: dir === 'left' ? -200 : 200,
        behavior: 'smooth'
      });
    }
  };

  useEffect(() => {
    checkCategoryScroll();
    const ref = categoryScrollRef.current;
    if (ref) {
      ref.addEventListener('scroll', checkCategoryScroll);
      window.addEventListener('resize', checkCategoryScroll);
    }
    return () => {
      if (ref) ref.removeEventListener('scroll', checkCategoryScroll);
      window.removeEventListener('resize', checkCategoryScroll);
    };
  }, []);

  // Filter courses
  useEffect(() => {
    let result = COURSES;

    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      result = result.filter(c => 
        c.title.toLowerCase().includes(q) ||
        c.instructor.toLowerCase().includes(q) ||
        c.category.toLowerCase().includes(q)
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
      result = result.filter(c => c.category === catMap[activeCategory]);
    }

    if (filters.format?.length) {
      result = result.filter(c => filters.format.includes(c.format));
    }

    setFilteredCourses(result);
  }, [searchQuery, activeCategory, filters]);

  const toggleFilter = (cat, val) => {
    setFilters(prev => {
      const curr = prev[cat] || [];
      if (curr.includes(val)) {
        return { ...prev, [cat]: curr.filter(v => v !== val) };
      }
      return { ...prev, [cat]: [...curr, val] };
    });
  };

  return (
    <div className="mcl-page" data-testid="library-page">
      {/* Vignette */}
      <div className="mcl-vignette" />

      {/* Top Nav - Exact MasterClass style */}
      <header className="mcl-header">
        <div className="mcl-header-left">
          <div className="mcl-logo">
            <span className="mcl-logo-mark">A</span>
            <span className="mcl-logo-text">Abundant</span>
          </div>
        </div>

        <div className="mcl-header-center">
          <div className="mcl-search">
            <Search className="mcl-search-icon" />
            <input 
              type="text"
              placeholder="Search Instructors, Classes, Topics and more"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>

        <div className="mcl-header-right">
          <a href="#" className="mcl-nav-link">
            <User className="w-4 h-4" />
            <span>My Progress</span>
          </a>
          <a href="#" className="mcl-nav-link active">
            <LayoutGrid className="w-4 h-4" />
            <span>Library</span>
          </a>
          <a href="#" className="mcl-nav-link">
            <Sparkles className="w-4 h-4" />
            <span>Class TA</span>
            <span className="mcl-beta">BETA</span>
          </a>
          <div className="mcl-user">
            <div className="mcl-avatar">{user?.name?.charAt(0) || 'M'}</div>
            <span className="mcl-user-name">{user?.name?.split(' ')[0] || 'Member'}</span>
            <ChevronDown className="w-4 h-4" />
          </div>
        </div>
      </header>

      {/* Red Gradient Bar - Cinema Curtain Effect */}
      <div className="mcl-red-bar" />

      {/* Categories Section - Exact MasterClass style */}
      <section className="mcl-categories">
        <div className="mcl-categories-head">
          <h2>Categories</h2>
          <div className="mcl-categories-nav">
            <button 
              className={`mcl-arrow ${!canScrollLeft ? 'disabled' : ''}`}
              onClick={() => scrollCategories('left')}
              disabled={!canScrollLeft}
            >
              <ChevronLeft />
            </button>
            <button 
              className={`mcl-arrow ${!canScrollRight ? 'disabled' : ''}`}
              onClick={() => scrollCategories('right')}
              disabled={!canScrollRight}
            >
              <ChevronRight />
            </button>
          </div>
        </div>
        <div className="mcl-categories-scroll" ref={categoryScrollRef}>
          {CATEGORIES.map((cat) => {
            const Icon = cat.icon;
            return (
              <button
                key={cat.id}
                className={`mcl-cat-tile ${activeCategory === cat.id ? 'active' : ''}`}
                onClick={() => setActiveCategory(cat.id)}
              >
                <Icon className="mcl-cat-icon" />
                <span>{cat.label}</span>
              </button>
            );
          })}
        </div>
      </section>

      {/* Main Content */}
      <div className="mcl-main">
        {/* Filter Sidebar */}
        <aside className="mcl-sidebar">
          <h3>Filters</h3>
          
          {Object.entries(FILTER_OPTIONS).map(([key, options]) => (
            <div key={key} className="mcl-filter">
              <button 
                className="mcl-filter-head"
                onClick={() => setOpenAccordion(openAccordion === key ? null : key)}
              >
                <span>{key === 'myContent' ? 'My Content' : key.charAt(0).toUpperCase() + key.slice(1)}</span>
                <ChevronDown className={`mcl-filter-chevron ${openAccordion === key ? 'open' : ''}`} />
              </button>
              <AnimatePresence>
                {openAccordion === key && (
                  <motion.div
                    className="mcl-filter-opts"
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                  >
                    {options.map((opt) => (
                      <label key={opt} className="mcl-checkbox">
                        <input 
                          type="checkbox"
                          checked={(filters[key] || []).includes(opt)}
                          onChange={() => toggleFilter(key, opt)}
                        />
                        <span className="mcl-check-box" />
                        <span>{opt}</span>
                      </label>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ))}
        </aside>

        {/* Course Grid */}
        <main className="mcl-grid-wrap">
          {filteredCourses.length > 0 ? (
            <div className="mcl-grid">
              {filteredCourses.map((course) => (
                <CourseCard 
                  key={course.id} 
                  course={course} 
                  onPlay={(c) => setVideoModal({ open: true, course: c })}
                />
              ))}
            </div>
          ) : (
            <div className="mcl-empty">
              <Book className="w-16 h-16" />
              <h3>No classes found</h3>
              <p>Try adjusting your filters or search terms</p>
            </div>
          )}

          {filteredCourses.length > 0 && (
            <button className="mcl-load-more">Load More</button>
          )}
        </main>
      </div>

      {/* Video Modal */}
      <AnimatePresence>
        {videoModal.open && (
          <VideoPlayerModal 
            isOpen={videoModal.open}
            course={videoModal.course}
            onClose={() => setVideoModal({ open: false, course: null })}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
