import { useState, useEffect, useRef } from 'react';
import { useOutletContext } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Play, ChevronLeft, ChevronRight, Clock, Search, 
  BookmarkPlus, Share2, Volume2, VolumeX, Pause,
  ChevronDown, X, Info
} from 'lucide-react';

// ═══════════════════════════════════════════════════════════════════════════════
// MASTERCLASS-STYLE ABUNDANT TV - Premium Dark Cinematic Experience
// ═══════════════════════════════════════════════════════════════════════════════

// Featured hero content (rotating)
const HERO_CONTENT = [
  {
    id: 'hero-1',
    instructor: 'Pastor David Rivera',
    instructorTitle: 'Lead Pastor, Abundant Church',
    instructorImg: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=200&q=80',
    title: 'Teaches Faith in the Storm',
    subtitle: 'Building unshakeable faith through life\'s greatest challenges',
    backgroundImg: 'https://images.unsplash.com/photo-1507692049790-de58290a4334?w=1920&q=80',
    lessons: 24,
    duration: '6h 10m',
  },
  {
    id: 'hero-2',
    instructor: 'Pastor Maria Santos',
    instructorTitle: 'Worship Director',
    instructorImg: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=200&q=80',
    title: 'The Heart of Worship',
    subtitle: 'Transform your understanding of worship and encounter God\'s presence',
    backgroundImg: 'https://images.unsplash.com/photo-1510915361894-db8b60106cb1?w=1920&q=80',
    lessons: 18,
    duration: '4h 30m',
  },
  {
    id: 'hero-3',
    instructor: 'Pastor David Rivera',
    instructorTitle: 'Lead Pastor, Abundant Church',
    instructorImg: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=200&q=80',
    title: 'Prayer That Moves Mountains',
    subtitle: 'Unlock the power of persistent, faith-filled prayer in your life',
    backgroundImg: 'https://images.unsplash.com/photo-1506157786151-b8491531f063?w=1920&q=80',
    lessons: 16,
    duration: '3h 45m',
  },
];

// Sermon/Course catalog
const COURSES = {
  popular: [
    { id: '1', instructor: 'Pastor David Rivera', instructorImg: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&q=80', title: 'Foundations of Faith', image: 'https://images.unsplash.com/photo-1504052434569-70ad5836ab65?w=800&q=80', lessons: 12, duration: '3h', badge: 'POPULAR' },
    { id: '2', instructor: 'Pastor Maria Santos', instructorImg: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&q=80', title: 'The Heart of Worship', image: 'https://images.unsplash.com/photo-1510915361894-db8b60106cb1?w=800&q=80', lessons: 8, duration: '2h' },
    { id: '3', instructor: 'Pastor David Rivera', instructorImg: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&q=80', title: 'Prayer That Moves Mountains', image: 'https://images.unsplash.com/photo-1506157786151-b8491531f063?w=800&q=80', lessons: 10, duration: '2h 30m', badge: 'NEW' },
    { id: '4', instructor: 'Pastor Maria Santos', instructorImg: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&q=80', title: 'Understanding Scripture', image: 'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=800&q=80', lessons: 16, duration: '4h' },
    { id: '5', instructor: 'Pastor David Rivera', instructorImg: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&q=80', title: 'The Grace of God', image: 'https://images.unsplash.com/photo-1445445290350-18a3b86e0b5a?w=800&q=80', lessons: 6, duration: '1h 30m' },
    { id: '6', instructor: 'Pastor Maria Santos', instructorImg: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&q=80', title: 'Walking in the Spirit', image: 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=800&q=80', lessons: 8, duration: '2h' },
  ],
  trending: [
    { id: '7', instructor: 'Pastor David Rivera', instructorImg: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&q=80', title: 'Leading with Purpose', image: 'https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?w=800&q=80', lessons: 14, duration: '3h 30m', badge: 'TRENDING' },
    { id: '8', instructor: 'Pastor Maria Santos', instructorImg: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&q=80', title: 'Marriage God\'s Way', image: 'https://images.unsplash.com/photo-1511895426328-dc8714191300?w=800&q=80', lessons: 10, duration: '2h 30m' },
    { id: '9', instructor: 'Pastor David Rivera', instructorImg: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&q=80', title: 'Financial Stewardship', image: 'https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=800&q=80', lessons: 8, duration: '2h' },
    { id: '10', instructor: 'Pastor Maria Santos', instructorImg: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&q=80', title: 'Raising Godly Children', image: 'https://images.unsplash.com/photo-1536640712-4d4c36ff0e4e?w=800&q=80', lessons: 12, duration: '3h', badge: 'NEW' },
    { id: '11', instructor: 'Pastor David Rivera', instructorImg: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&q=80', title: 'Overcoming Anxiety', image: 'https://images.unsplash.com/photo-1499209974431-9dddcece7f88?w=800&q=80', lessons: 6, duration: '1h 30m' },
    { id: '12', instructor: 'Pastor Maria Santos', instructorImg: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&q=80', title: 'Finding Your Calling', image: 'https://images.unsplash.com/photo-1478147427282-58a87a120781?w=800&q=80', lessons: 8, duration: '2h' },
  ],
  newReleases: [
    { id: '13', instructor: 'Pastor David Rivera', instructorImg: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&q=80', title: 'Morning Devotions', image: 'https://images.unsplash.com/photo-1470252649378-9c29740c9fa8?w=800&q=80', lessons: 5, duration: '25m', badge: 'NEW' },
    { id: '14', instructor: 'Pastor Maria Santos', instructorImg: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&q=80', title: 'Quick Prayer Guide', image: 'https://images.unsplash.com/photo-1473172707857-f9e276582ab6?w=800&q=80', lessons: 4, duration: '20m', badge: 'NEW' },
    { id: '15', instructor: 'Pastor David Rivera', instructorImg: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&q=80', title: 'Scripture Memory', image: 'https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=800&q=80', lessons: 6, duration: '28m', badge: 'NEW' },
    { id: '16', instructor: 'Pastor Maria Santos', instructorImg: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&q=80', title: 'Gratitude Practice', image: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=80', lessons: 3, duration: '15m', badge: 'NEW' },
    { id: '17', instructor: 'Pastor David Rivera', instructorImg: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&q=80', title: 'Daily Declarations', image: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800&q=80', lessons: 5, duration: '22m', badge: 'NEW' },
    { id: '18', instructor: 'Pastor Maria Santos', instructorImg: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&q=80', title: 'Worship Moments', image: 'https://images.unsplash.com/photo-1415201364774-f6f0bb35f28f?w=800&q=80', lessons: 4, duration: '18m', badge: 'NEW' },
  ],
  deepStudies: [
    { id: '19', instructor: 'Pastor David Rivera', instructorImg: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&q=80', title: 'Book of Romans Study', image: 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=800&q=80', lessons: 32, duration: '8h' },
    { id: '20', instructor: 'Pastor Maria Santos', instructorImg: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&q=80', title: 'Theology of Suffering', image: 'https://images.unsplash.com/photo-1532012197267-da84d127e765?w=800&q=80', lessons: 20, duration: '5h', badge: 'FEATURED' },
    { id: '21', instructor: 'Pastor David Rivera', instructorImg: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&q=80', title: 'Church History', image: 'https://images.unsplash.com/photo-1461360228754-6e81c478b882?w=800&q=80', lessons: 24, duration: '6h' },
    { id: '22', instructor: 'Pastor Maria Santos', instructorImg: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&q=80', title: 'Hebrew Foundations', image: 'https://images.unsplash.com/photo-1432821596592-e2c18b78144f?w=800&q=80', lessons: 18, duration: '4h 30m' },
    { id: '23', instructor: 'Pastor David Rivera', instructorImg: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&q=80', title: 'Apologetics Masterclass', image: 'https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=800&q=80', lessons: 28, duration: '7h', badge: 'POPULAR' },
    { id: '24', instructor: 'Pastor Maria Santos', instructorImg: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&q=80', title: 'Prophetic Literature', image: 'https://images.unsplash.com/photo-1516979187457-637abb4f9353?w=800&q=80', lessons: 22, duration: '5h 30m' },
  ],
};

const CATEGORIES = ['All Classes', 'Faith', 'Worship', 'Prayer', 'Family', 'Leadership', 'Bible Study'];

// ═══════════════════════════════════════════════════════════════════════════════
// COMPONENTS
// ═══════════════════════════════════════════════════════════════════════════════

// Horizontal Carousel Component
const Carousel = ({ title, subtitle, courses, goldAccent = false }) => {
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
      const cardWidth = 300;
      const scrollAmount = cardWidth * 2;
      scrollRef.current.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
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
    <section className="mc-carousel-section">
      <div className="mc-carousel-header">
        <div>
          <h3 className={`mc-carousel-title ${goldAccent ? 'gold' : ''}`}>{title}</h3>
          {subtitle && <p className="mc-carousel-subtitle">{subtitle}</p>}
        </div>
        <button className="mc-see-all">Explore All</button>
      </div>
      
      <div className="mc-carousel-container">
        <AnimatePresence>
          {canScrollLeft && (
            <motion.button 
              className="mc-carousel-nav left"
              onClick={() => scroll('left')}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
            >
              <ChevronLeft className="w-6 h-6" />
            </motion.button>
          )}
        </AnimatePresence>
        
        <div className="mc-carousel-track" ref={scrollRef}>
          {courses.map((course, index) => (
            <CourseCard key={course.id} course={course} index={index} />
          ))}
        </div>
        
        <AnimatePresence>
          {canScrollRight && (
            <motion.button 
              className="mc-carousel-nav right"
              onClick={() => scroll('right')}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
            >
              <ChevronRight className="w-6 h-6" />
            </motion.button>
          )}
        </AnimatePresence>
      </div>
    </section>
  );
};

// Course Card Component
const CourseCard = ({ course, index }) => {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <motion.div 
      className="mc-course-card"
      data-testid={`course-card-${course.id}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.4 }}
      whileHover={{ y: -8, transition: { duration: 0.2 } }}
    >
      <div className="mc-card-image-wrapper">
        <img 
          src={course.image} 
          alt={course.title} 
          className="mc-card-image"
          loading="lazy"
        />
        <div className="mc-card-gradient" />
        
        {course.badge && (
          <span className={`mc-card-badge ${course.badge.toLowerCase()}`}>
            {course.badge}
          </span>
        )}
        
        <motion.div 
          className="mc-card-play-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: isHovered ? 1 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <motion.button 
            className="mc-play-button"
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
          >
            <Play className="w-7 h-7" fill="currentColor" />
          </motion.button>
        </motion.div>
        
        <div className="mc-card-duration">
          <Clock className="w-3 h-3" />
          <span>{course.duration}</span>
        </div>
      </div>
      
      <div className="mc-card-content">
        <div className="mc-card-instructor">
          <img 
            src={course.instructorImg} 
            alt={course.instructor}
            className="mc-instructor-avatar"
          />
          <span>{course.instructor}</span>
        </div>
        <h4 className="mc-card-title">{course.title}</h4>
        <p className="mc-card-lessons">{course.lessons} lessons</p>
      </div>
    </motion.div>
  );
};

// Instructor Spotlight Component
const InstructorSpotlight = () => {
  return (
    <motion.section 
      className="mc-spotlight"
      initial={{ opacity: 0, y: 40 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-100px" }}
      transition={{ duration: 0.6 }}
    >
      <div className="mc-spotlight-image">
        <img 
          src="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=800&q=80" 
          alt="Pastor David Rivera"
        />
        <div className="mc-spotlight-gradient" />
      </div>
      <div className="mc-spotlight-content">
        <span className="mc-spotlight-label">INSTRUCTOR SPOTLIGHT</span>
        <h2 className="mc-spotlight-name">Pastor David Rivera</h2>
        <p className="mc-spotlight-bio">
          With over 25 years of ministry experience, Pastor David has helped thousands 
          discover deeper faith and purpose. His teaching style combines theological 
          depth with practical application, making complex biblical concepts accessible 
          to everyone.
        </p>
        <div className="mc-spotlight-stats">
          <div className="mc-stat">
            <span className="mc-stat-value">12</span>
            <span className="mc-stat-label">Classes</span>
          </div>
          <div className="mc-stat">
            <span className="mc-stat-value">156</span>
            <span className="mc-stat-label">Lessons</span>
          </div>
          <div className="mc-stat">
            <span className="mc-stat-value">40h+</span>
            <span className="mc-stat-label">Content</span>
          </div>
        </div>
        <motion.button 
          className="mc-spotlight-btn"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          Explore His Classes
          <ChevronRight className="w-4 h-4" />
        </motion.button>
      </div>
    </motion.section>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ═══════════════════════════════════════════════════════════════════════════════

export default function PortalWatch() {
  const { user } = useOutletContext();
  const [activeHero, setActiveHero] = useState(0);
  const [activeCategory, setActiveCategory] = useState('All Classes');
  const [isScrolled, setIsScrolled] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Auto-rotate hero
  useEffect(() => {
    const interval = setInterval(() => {
      setActiveHero((prev) => (prev + 1) % HERO_CONTENT.length);
    }, 8000);
    return () => clearInterval(interval);
  }, []);

  // Scroll detection for sticky nav
  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 100);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const currentHero = HERO_CONTENT[activeHero];

  return (
    <div className="mc-page" data-testid="masterclass-watch">
      {/* ═══ HERO SECTION ═══ */}
      <section className="mc-hero">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentHero.id}
            className="mc-hero-bg"
            style={{ backgroundImage: `url(${currentHero.backgroundImg})` }}
            initial={{ opacity: 0, scale: 1.1 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 1 }}
          />
        </AnimatePresence>
        
        <div className="mc-hero-overlay" />
        
        {/* Hero Content */}
        <div className="mc-hero-container">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentHero.id}
              className="mc-hero-content"
              initial={{ opacity: 0, x: -30 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 30 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              <motion.div 
                className="mc-hero-instructor"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
              >
                <img 
                  src={currentHero.instructorImg} 
                  alt={currentHero.instructor}
                  className="mc-hero-instructor-img"
                />
                <div>
                  <p className="mc-hero-instructor-name">{currentHero.instructor}</p>
                  <p className="mc-hero-instructor-title">{currentHero.instructorTitle}</p>
                </div>
              </motion.div>
              
              <motion.h1 
                className="mc-hero-title"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
              >
                {currentHero.title}
              </motion.h1>
              
              <motion.p 
                className="mc-hero-subtitle"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
              >
                {currentHero.subtitle}
              </motion.p>
              
              <motion.div 
                className="mc-hero-meta"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6 }}
              >
                <span>{currentHero.lessons} lessons</span>
                <span className="mc-meta-dot">·</span>
                <span>{currentHero.duration} total</span>
              </motion.div>
              
              <motion.div 
                className="mc-hero-actions"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.7 }}
              >
                <motion.button 
                  className="mc-btn-primary"
                  whileHover={{ scale: 1.03 }}
                  whileTap={{ scale: 0.98 }}
                  data-testid="hero-start-btn"
                >
                  <Play className="w-5 h-5" fill="currentColor" />
                  Start Watching
                </motion.button>
                <motion.button 
                  className="mc-btn-ghost"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <BookmarkPlus className="w-5 h-5" />
                </motion.button>
                <motion.button 
                  className="mc-btn-ghost"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Info className="w-5 h-5" />
                </motion.button>
              </motion.div>
            </motion.div>
          </AnimatePresence>
          
          {/* Hero Navigation Dots */}
          <div className="mc-hero-dots">
            {HERO_CONTENT.map((_, index) => (
              <button
                key={index}
                className={`mc-hero-dot ${activeHero === index ? 'active' : ''}`}
                onClick={() => setActiveHero(index)}
                aria-label={`Go to slide ${index + 1}`}
              />
            ))}
          </div>
        </div>
      </section>

      {/* ═══ STICKY CATEGORY BAR ═══ */}
      <nav className={`mc-category-bar ${isScrolled ? 'scrolled' : ''}`}>
        <div className="mc-category-container">
          <div className="mc-category-track">
            {CATEGORIES.map((cat) => (
              <button
                key={cat}
                className={`mc-category-pill ${activeCategory === cat ? 'active' : ''}`}
                onClick={() => setActiveCategory(cat)}
              >
                {cat}
              </button>
            ))}
          </div>
          
          <div className="mc-category-actions">
            <motion.button 
              className="mc-search-toggle"
              onClick={() => setSearchOpen(!searchOpen)}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Search className="w-5 h-5" />
            </motion.button>
          </div>
        </div>
        
        {/* Search Overlay */}
        <AnimatePresence>
          {searchOpen && (
            <motion.div 
              className="mc-search-bar"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
            >
              <div className="mc-search-inner">
                <Search className="w-5 h-5 mc-search-icon" />
                <input 
                  type="text"
                  placeholder="Search classes, topics, instructors..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="mc-search-input"
                  autoFocus
                />
                <button 
                  className="mc-search-close"
                  onClick={() => { setSearchOpen(false); setSearchQuery(''); }}
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </nav>

      {/* ═══ MAIN CONTENT ═══ */}
      <main className="mc-main">
        {/* Popular Classes */}
        <Carousel 
          title="Popular Classes" 
          subtitle="Where most members start their journey"
          courses={COURSES.popular} 
        />
        
        {/* Trending Now */}
        <Carousel 
          title="Trending This Week" 
          courses={COURSES.trending} 
        />
        
        {/* Instructor Spotlight */}
        <InstructorSpotlight />
        
        {/* New Releases */}
        <Carousel 
          title="New Releases" 
          subtitle="Fresh content just added"
          courses={COURSES.newReleases} 
        />
        
        {/* Deep Studies */}
        <Carousel 
          title="Deep Dives" 
          subtitle="In-depth explorations for serious students"
          courses={COURSES.deepStudies}
          goldAccent
        />

        {/* ═══ FOOTER CTA ═══ */}
        <motion.section 
          className="mc-footer-cta"
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <div className="mc-cta-pattern" />
          <div className="mc-cta-content">
            <h2 className="mc-cta-title">Every Lesson. Every Teacher. All Access.</h2>
            <p className="mc-cta-subtitle">
              Join thousands of members growing in their faith journey
            </p>
            <motion.button 
              className="mc-cta-btn"
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.98 }}
            >
              Start Your Journey
            </motion.button>
          </div>
        </motion.section>
      </main>
    </div>
  );
}
