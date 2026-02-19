import { useState, useRef, useEffect } from 'react';
import { useOutletContext, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Search, ChevronDown, ChevronLeft, ChevronRight, Play, Plus, X,
  User, LayoutGrid, Sparkles, BookOpen, Utensils, Music, Pen, 
  Gamepad2, Palette, Briefcase, Cpu, Home, Users, Film
} from 'lucide-react';

// ═══════════════════════════════════════════════════════════════════════════════
// MASTERCLASS LIBRARY - Pixel-Perfect Recreation
// ═══════════════════════════════════════════════════════════════════════════════

// Category data with icons
const CATEGORIES = [
  { id: 'all', label: 'All Categories', icon: LayoutGrid },
  { id: 'food', label: 'Food', icon: Utensils },
  { id: 'arts', label: 'Arts & Entertainment', icon: Film },
  { id: 'music', label: 'Music', icon: Music },
  { id: 'writing', label: 'Writing', icon: Pen },
  { id: 'sports', label: 'Sports & Gaming', icon: Gamepad2 },
  { id: 'design', label: 'Design & Style', icon: Palette },
  { id: 'business', label: 'Business', icon: Briefcase },
  { id: 'science', label: 'Science & Tech', icon: Cpu },
  { id: 'home', label: 'Home & Lifestyle', icon: Home },
  { id: 'community', label: 'Community & Government', icon: Users },
];

// Sample course data
const COURSES = [
  { 
    id: 1, 
    title: "Rebuild Your Focus & Reclaim Your Time", 
    instructor: "Cal Newport", 
    format: "Class", 
    duration: "1h 26m", 
    category: "Business", 
    badge: "New", 
    thumbnail: "https://images.unsplash.com/photo-1516321497487-e288fb19713f?w=600&q=80",
    description: "Learn to cut through distraction and build deep work habits that transform your productivity and career trajectory."
  },
  { 
    id: 2, 
    title: "Dopamine: Take Your Brain Back", 
    instructor: "Dr. Anna Lembke", 
    format: "Class", 
    duration: "1h 1m", 
    category: "Wellness", 
    badge: "New", 
    thumbnail: "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=600&q=80",
    description: "Stanford psychiatrist reveals the science of addiction and pleasure, teaching you to reset your brain's reward system."
  },
  { 
    id: 3, 
    title: "The New Rules of Business", 
    instructor: "Kim Kardashian", 
    format: "Class", 
    duration: "1h 18m", 
    category: "Business", 
    thumbnail: "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=600&q=80",
    description: "From SKIMS to KKW Beauty, learn how to build a billion-dollar brand from the ground up."
  },
  { 
    id: 4, 
    title: "The Power Playbook: How to Win at Work", 
    instructor: "Professor Jeffrey Pfeffer", 
    format: "Class", 
    duration: "1h 9m", 
    category: "Business", 
    thumbnail: "https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=600&q=80",
    description: "Stanford professor shares proven methods for gaining workplace influence and navigating corporate politics."
  },
  { 
    id: 5, 
    title: "The Science of Parenting", 
    instructor: "Noted Experts", 
    format: "Series", 
    episodes: 3, 
    category: "Wellness", 
    thumbnail: "https://images.unsplash.com/photo-1536640712-4d4c36ff0e4e?w=600&q=80",
    description: "Evidence-based strategies from leading child development researchers and parenting specialists."
  },
  { 
    id: 6, 
    title: "Happy Clothes: A Film About Style", 
    instructor: "Patricia Field", 
    format: "Class", 
    duration: "1h 41m", 
    category: "Design & Style", 
    thumbnail: "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=600&q=80",
    description: "The legendary costume designer behind Sex and the City shares her philosophy on fashion as self-expression."
  },
  { 
    id: 7, 
    title: "Cooking Fundamentals", 
    instructor: "Gordon Ramsay", 
    format: "Class", 
    duration: "3h 54m", 
    category: "Food", 
    thumbnail: "https://images.unsplash.com/photo-1556910103-1c02745aae4d?w=600&q=80",
    description: "Master essential cooking techniques from one of the world's most acclaimed chefs."
  },
  { 
    id: 8, 
    title: "The Art of Negotiation", 
    instructor: "Chris Voss", 
    format: "Class", 
    duration: "2h 12m", 
    category: "Business", 
    badge: "New",
    thumbnail: "https://images.unsplash.com/photo-1450101499163-c8848c66ca85?w=600&q=80",
    description: "Former FBI hostage negotiator teaches tactical empathy and high-stakes communication."
  },
  { 
    id: 9, 
    title: "Filmmaking", 
    instructor: "Martin Scorsese", 
    format: "Class", 
    duration: "4h 30m", 
    category: "Arts & Entertainment", 
    thumbnail: "https://images.unsplash.com/photo-1485846234645-a62644f84728?w=600&q=80",
    description: "The legendary director shares his creative process, from storyboarding to final cut."
  },
  { 
    id: 10, 
    title: "Electronic Music Production", 
    instructor: "Deadmau5", 
    format: "Class", 
    duration: "5h 52m", 
    category: "Music", 
    thumbnail: "https://images.unsplash.com/photo-1511379938547-c1f69419868d?w=600&q=80",
    description: "From sound design to mixing, learn the complete production workflow from a genre pioneer."
  },
  { 
    id: 11, 
    title: "Creative Writing", 
    instructor: "Margaret Atwood", 
    format: "Class", 
    duration: "3h 18m", 
    category: "Writing", 
    thumbnail: "https://images.unsplash.com/photo-1455390582262-044cdead277a?w=600&q=80",
    description: "The Booker Prize winner guides you through the craft of storytelling and world-building."
  },
  { 
    id: 12, 
    title: "Chess Strategy", 
    instructor: "Garry Kasparov", 
    format: "Class", 
    duration: "2h 45m", 
    category: "Sports & Gaming", 
    thumbnail: "https://images.unsplash.com/photo-1529699211952-734e80c4d42b?w=600&q=80",
    description: "The greatest chess player of all time breaks down strategy, tactics, and competitive mindset."
  },
];

// Filter options
const FILTER_OPTIONS = {
  format: ['Class', 'Series', 'Session', 'Note'],
  myContent: ['Saved', 'In Progress', 'Completed'],
  duration: ['Under 1 hour', '1-2 hours', '2-4 hours', '4+ hours'],
};

// ═══════════════════════════════════════════════════════════════════════════════
// COMPONENTS
// ═══════════════════════════════════════════════════════════════════════════════

// Top Navigation Bar
const TopNav = ({ user, searchQuery, setSearchQuery }) => {
  return (
    <nav className="mc-lib-nav" data-testid="library-nav">
      {/* Logo */}
      <div className="mc-lib-logo">
        <div className="mc-lib-logo-icon">
          <svg viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6">
            <path d="M12 2L2 7v10l10 5 10-5V7L12 2zm0 2.18l6.9 3.45L12 11.09 5.1 7.63 12 4.18zM4 8.82l7 3.5v7.36l-7-3.5V8.82zm9 10.86v-7.36l7-3.5v7.36l-7 3.5z"/>
          </svg>
        </div>
        <span className="mc-lib-logo-text">Abundant</span>
      </div>

      {/* Search Bar */}
      <div className="mc-lib-search">
        <Search className="mc-lib-search-icon" />
        <input 
          type="text"
          placeholder="Search Instructors, Classes, Topics and more"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="mc-lib-search-input"
        />
      </div>

      {/* Nav Links */}
      <div className="mc-lib-nav-links">
        <a href="#" className="mc-lib-nav-link">
          <User className="w-4 h-4" />
          <span>My Progress</span>
        </a>
        <a href="#" className="mc-lib-nav-link active">
          <LayoutGrid className="w-4 h-4" />
          <span>Library</span>
        </a>
        <a href="#" className="mc-lib-nav-link">
          <Sparkles className="w-4 h-4" />
          <span>Class TA</span>
          <span className="mc-lib-beta-badge">BETA</span>
        </a>
        <div className="mc-lib-user">
          <div className="mc-lib-avatar">
            {user?.name?.charAt(0) || 'U'}
          </div>
          <span>{user?.name?.split(' ')[0] || 'User'}</span>
          <ChevronDown className="w-4 h-4" />
        </div>
      </div>
    </nav>
  );
};

// Category Bar
const CategoryBar = ({ activeCategory, setActiveCategory }) => {
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

  const scroll = (direction) => {
    if (scrollRef.current) {
      scrollRef.current.scrollBy({
        left: direction === 'left' ? -200 : 200,
        behavior: 'smooth'
      });
    }
  };

  useEffect(() => {
    checkScroll();
    const ref = scrollRef.current;
    if (ref) {
      ref.addEventListener('scroll', checkScroll);
      window.addEventListener('resize', checkScroll);
    }
    return () => {
      if (ref) ref.removeEventListener('scroll', checkScroll);
      window.removeEventListener('resize', checkScroll);
    };
  }, []);

  return (
    <div className="mc-lib-category-bar" data-testid="category-bar">
      <div className="mc-lib-category-header">
        <h2 className="mc-lib-category-title">Categories</h2>
        <div className="mc-lib-category-arrows">
          <button 
            className={`mc-lib-arrow-btn ${!canScrollLeft ? 'disabled' : ''}`}
            onClick={() => scroll('left')}
            disabled={!canScrollLeft}
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <button 
            className={`mc-lib-arrow-btn ${!canScrollRight ? 'disabled' : ''}`}
            onClick={() => scroll('right')}
            disabled={!canScrollRight}
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      </div>
      <div className="mc-lib-category-scroll" ref={scrollRef}>
        {CATEGORIES.map((cat) => {
          const Icon = cat.icon;
          return (
            <button
              key={cat.id}
              className={`mc-lib-category-tile ${activeCategory === cat.id ? 'active' : ''}`}
              onClick={() => setActiveCategory(cat.id)}
              data-testid={`category-${cat.id}`}
            >
              <Icon className="mc-lib-category-icon" />
              <span className="mc-lib-category-label">{cat.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};

// Filter Sidebar
const FilterSidebar = ({ filters, setFilters }) => {
  const [openAccordions, setOpenAccordions] = useState({});

  const toggleAccordion = (key) => {
    setOpenAccordions(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const toggleFilter = (category, value) => {
    setFilters(prev => {
      const current = prev[category] || [];
      if (current.includes(value)) {
        return { ...prev, [category]: current.filter(v => v !== value) };
      }
      return { ...prev, [category]: [...current, value] };
    });
  };

  return (
    <aside className="mc-lib-sidebar" data-testid="filter-sidebar">
      <h3 className="mc-lib-sidebar-title">Filters</h3>
      
      {Object.entries(FILTER_OPTIONS).map(([key, options]) => (
        <div key={key} className="mc-lib-accordion">
          <button 
            className="mc-lib-accordion-header"
            onClick={() => toggleAccordion(key)}
          >
            <span>{key === 'myContent' ? 'My Content' : key.charAt(0).toUpperCase() + key.slice(1)}</span>
            <ChevronDown className={`mc-lib-accordion-chevron ${openAccordions[key] ? 'open' : ''}`} />
          </button>
          <AnimatePresence>
            {openAccordions[key] && (
              <motion.div
                className="mc-lib-accordion-content"
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
              >
                {options.map((option) => (
                  <label key={option} className="mc-lib-checkbox-label">
                    <input 
                      type="checkbox"
                      checked={(filters[key] || []).includes(option)}
                      onChange={() => toggleFilter(key, option)}
                      className="mc-lib-checkbox"
                    />
                    <span className="mc-lib-checkbox-custom" />
                    <span>{option}</span>
                  </label>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      ))}
    </aside>
  );
};

// Course Card
const CourseCard = ({ course, onPlay }) => {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <motion.article 
      className="mc-lib-card"
      data-testid={`course-card-${course.id}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {/* Thumbnail */}
      <div className="mc-lib-card-image">
        <img 
          src={course.thumbnail} 
          alt={course.title}
          loading="lazy"
        />
        
        {/* Badges */}
        {course.badge && (
          <span className="mc-lib-badge-new">{course.badge}</span>
        )}
        <span className="mc-lib-badge-duration">
          {course.duration || `${course.episodes} episodes`}
        </span>

        {/* Hover Overlay */}
        <AnimatePresence>
          {isHovered && (
            <motion.div 
              className="mc-lib-card-overlay"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.15 }}
            >
              <div className="mc-lib-card-buttons">
                <button 
                  className="mc-lib-play-btn"
                  onClick={() => onPlay(course)}
                  data-testid={`play-btn-${course.id}`}
                >
                  <Play className="w-5 h-5" fill="currentColor" />
                </button>
                <button className="mc-lib-add-btn">
                  <Plus className="w-5 h-5" />
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Card Content */}
      <div className="mc-lib-card-content">
        <p className="mc-lib-card-meta">
          {course.format} • {course.duration || `${course.episodes} episodes`} • {course.category}
        </p>
        <h3 className="mc-lib-card-title">{course.title}</h3>
        <p className="mc-lib-card-instructor">With {course.instructor}</p>
      </div>

      {/* Hover Expansion */}
      <AnimatePresence>
        {isHovered && course.description && (
          <motion.div 
            className="mc-lib-card-expand"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
          >
            <p className="mc-lib-card-description">{course.description}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.article>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ═══════════════════════════════════════════════════════════════════════════════

export default function PortalLibrary() {
  const { user } = useOutletContext();
  const navigate = useNavigate();
  
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState('all');
  const [filters, setFilters] = useState({});
  const [filteredCourses, setFilteredCourses] = useState(COURSES);

  // Filter courses based on search, category, and filters
  useEffect(() => {
    let result = COURSES;

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(c => 
        c.title.toLowerCase().includes(query) ||
        c.instructor.toLowerCase().includes(query) ||
        c.category.toLowerCase().includes(query)
      );
    }

    // Category filter
    if (activeCategory !== 'all') {
      const categoryMap = {
        'food': 'Food',
        'arts': 'Arts & Entertainment',
        'music': 'Music',
        'writing': 'Writing',
        'sports': 'Sports & Gaming',
        'design': 'Design & Style',
        'business': 'Business',
        'science': 'Science & Tech',
        'home': 'Home & Lifestyle',
        'community': 'Community & Government',
      };
      const catLabel = categoryMap[activeCategory];
      if (catLabel) {
        result = result.filter(c => c.category === catLabel);
      }
    }

    // Format filter
    if (filters.format?.length) {
      result = result.filter(c => filters.format.includes(c.format));
    }

    // Duration filter
    if (filters.duration?.length) {
      result = result.filter(c => {
        if (!c.duration) return false;
        const hours = parseFloat(c.duration.split('h')[0]);
        return filters.duration.some(d => {
          if (d === 'Under 1 hour') return hours < 1;
          if (d === '1-2 hours') return hours >= 1 && hours < 2;
          if (d === '2-4 hours') return hours >= 2 && hours < 4;
          if (d === '4+ hours') return hours >= 4;
          return false;
        });
      });
    }

    setFilteredCourses(result);
  }, [searchQuery, activeCategory, filters]);

  // Handle play course
  const handlePlayCourse = (course) => {
    // Navigate to watch page with course data
    navigate('/portal/watch', { state: { course } });
  };

  return (
    <div className="mc-lib-page" data-testid="library-page">
      {/* Cinematic Vignette Effect */}
      <div className="mc-lib-vignette" />

      {/* Top Navigation */}
      <TopNav 
        user={user} 
        searchQuery={searchQuery} 
        setSearchQuery={setSearchQuery} 
      />

      {/* Category Bar */}
      <CategoryBar 
        activeCategory={activeCategory} 
        setActiveCategory={setActiveCategory} 
      />

      {/* Main Content Area */}
      <div className="mc-lib-main">
        {/* Filter Sidebar */}
        <FilterSidebar filters={filters} setFilters={setFilters} />

        {/* Course Grid */}
        <main className="mc-lib-grid-container">
          {filteredCourses.length > 0 ? (
            <div className="mc-lib-grid">
              {filteredCourses.map((course) => (
                <CourseCard 
                  key={course.id} 
                  course={course} 
                  onPlay={handlePlayCourse}
                />
              ))}
            </div>
          ) : (
            <div className="mc-lib-empty">
              <BookOpen className="w-16 h-16 mb-4 opacity-30" />
              <h3>No courses found</h3>
              <p>Try adjusting your filters or search terms</p>
            </div>
          )}

          {/* Load More Button */}
          {filteredCourses.length > 0 && (
            <button className="mc-lib-load-more">
              Load More
            </button>
          )}
        </main>
      </div>
    </div>
  );
}
