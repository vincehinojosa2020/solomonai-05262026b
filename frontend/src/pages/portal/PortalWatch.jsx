import { useState, useEffect, useRef } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Play, ChevronLeft, ChevronRight, Clock, BookOpen, Award } from 'lucide-react';

// Sermon/Course data
const FEATURED_COURSE = {
  id: 'featured-1',
  instructorName: 'Pastor David Rivera',
  courseTitle: 'Teaches Faith in the Storm',
  thumbnailUrl: 'https://images.unsplash.com/photo-1507692049790-de58290a4334?w=1920&q=80',
  subtitle: 'Building unshakeable faith through life\'s greatest challenges',
  teaser: 'Learn to stand firm when everything around you is uncertain. Discover the ancient principles that have sustained believers for generations.',
  lessonCount: 24,
  durationMinutes: 370,
  category: 'FEATURED SERIES',
};

const COURSES = {
  foundations: [
    { id: '1', instructorName: 'Pastor David Rivera', courseTitle: 'Foundations of Faith', thumbnailUrl: 'https://images.unsplash.com/photo-1504052434569-70ad5836ab65?w=800&q=80', lessonCount: 12, durationMinutes: 180, badge: 'POPULAR', category: 'Faith', level: 'Beginner' },
    { id: '2', instructorName: 'Pastor Maria Santos', courseTitle: 'The Heart of Worship', thumbnailUrl: 'https://images.unsplash.com/photo-1510915361894-db8b60106cb1?w=800&q=80', lessonCount: 8, durationMinutes: 120, category: 'Worship', level: 'Beginner' },
    { id: '3', instructorName: 'Pastor David Rivera', courseTitle: 'Prayer That Moves Mountains', thumbnailUrl: 'https://images.unsplash.com/photo-1506157786151-b8491531f063?w=800&q=80', lessonCount: 10, durationMinutes: 150, badge: 'NEW', category: 'Prayer', level: 'Beginner' },
    { id: '4', instructorName: 'Pastor Maria Santos', courseTitle: 'Understanding Scripture', thumbnailUrl: 'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=800&q=80', lessonCount: 16, durationMinutes: 240, category: 'Bible Study', level: 'Beginner' },
    { id: '5', instructorName: 'Pastor David Rivera', courseTitle: 'The Grace of God', thumbnailUrl: 'https://images.unsplash.com/photo-1445445290350-18a3b86e0b5a?w=800&q=80', lessonCount: 6, durationMinutes: 90, category: 'Theology', level: 'Beginner' },
    { id: '6', instructorName: 'Pastor Maria Santos', courseTitle: 'Walking in the Spirit', thumbnailUrl: 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=800&q=80', lessonCount: 8, durationMinutes: 120, category: 'Spiritual Growth', level: 'Beginner' },
  ],
  trending: [
    { id: '7', instructorName: 'Pastor David Rivera', courseTitle: 'Leading with Purpose', thumbnailUrl: 'https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?w=800&q=80', lessonCount: 14, durationMinutes: 210, badge: 'POPULAR', category: 'Leadership', level: 'Intermediate' },
    { id: '8', instructorName: 'Pastor Maria Santos', courseTitle: 'Marriage God\'s Way', thumbnailUrl: 'https://images.unsplash.com/photo-1511895426328-dc8714191300?w=800&q=80', lessonCount: 10, durationMinutes: 150, category: 'Family', level: 'Intermediate' },
    { id: '9', instructorName: 'Pastor David Rivera', courseTitle: 'Financial Stewardship', thumbnailUrl: 'https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=800&q=80', lessonCount: 8, durationMinutes: 120, category: 'Finance', level: 'Intermediate' },
    { id: '10', instructorName: 'Pastor Maria Santos', courseTitle: 'Raising Godly Children', thumbnailUrl: 'https://images.unsplash.com/photo-1536640712-4d4c36ff0e4e?w=800&q=80', lessonCount: 12, durationMinutes: 180, badge: 'NEW', category: 'Family', level: 'Intermediate' },
    { id: '11', instructorName: 'Pastor David Rivera', courseTitle: 'Overcoming Anxiety', thumbnailUrl: 'https://images.unsplash.com/photo-1499209974431-9dddcece7f88?w=800&q=80', lessonCount: 6, durationMinutes: 90, category: 'Mental Health', level: 'Beginner' },
    { id: '12', instructorName: 'Pastor Maria Santos', courseTitle: 'Finding Your Calling', thumbnailUrl: 'https://images.unsplash.com/photo-1478147427282-58a87a120781?w=800&q=80', lessonCount: 8, durationMinutes: 120, category: 'Purpose', level: 'Intermediate' },
  ],
  quickWins: [
    { id: '13', instructorName: 'Pastor David Rivera', courseTitle: 'Morning Devotions', thumbnailUrl: 'https://images.unsplash.com/photo-1470252649378-9c29740c9fa8?w=800&q=80', lessonCount: 5, durationMinutes: 25, category: 'Devotional', level: 'Beginner' },
    { id: '14', instructorName: 'Pastor Maria Santos', courseTitle: 'Quick Prayer Guide', thumbnailUrl: 'https://images.unsplash.com/photo-1473172707857-f9e276582ab6?w=800&q=80', lessonCount: 4, durationMinutes: 20, category: 'Prayer', level: 'Beginner' },
    { id: '15', instructorName: 'Pastor David Rivera', courseTitle: 'Scripture Memory', thumbnailUrl: 'https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=800&q=80', lessonCount: 6, durationMinutes: 28, badge: 'NEW', category: 'Bible Study', level: 'Beginner' },
    { id: '16', instructorName: 'Pastor Maria Santos', courseTitle: 'Gratitude Practice', thumbnailUrl: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=80', lessonCount: 3, durationMinutes: 15, category: 'Spiritual Growth', level: 'Beginner' },
    { id: '17', instructorName: 'Pastor David Rivera', courseTitle: 'Daily Declarations', thumbnailUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800&q=80', lessonCount: 5, durationMinutes: 22, category: 'Faith', level: 'Beginner' },
    { id: '18', instructorName: 'Pastor Maria Santos', courseTitle: 'Worship Moments', thumbnailUrl: 'https://images.unsplash.com/photo-1415201364774-f6f0bb35f28f?w=800&q=80', lessonCount: 4, durationMinutes: 18, category: 'Worship', level: 'Beginner' },
  ],
  deepDives: [
    { id: '19', instructorName: 'Pastor David Rivera', courseTitle: 'Book of Romans Study', thumbnailUrl: 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=800&q=80', lessonCount: 32, durationMinutes: 480, category: 'Bible Study', level: 'Advanced' },
    { id: '20', instructorName: 'Pastor Maria Santos', courseTitle: 'Theology of Suffering', thumbnailUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800&q=80', lessonCount: 20, durationMinutes: 300, badge: 'FEATURED', category: 'Theology', level: 'Advanced' },
    { id: '21', instructorName: 'Pastor David Rivera', courseTitle: 'Church History', thumbnailUrl: 'https://images.unsplash.com/photo-1461360228754-6e81c478b882?w=800&q=80', lessonCount: 24, durationMinutes: 360, category: 'History', level: 'Advanced' },
    { id: '22', instructorName: 'Pastor Maria Santos', courseTitle: 'Hebrew Foundations', thumbnailUrl: 'https://images.unsplash.com/photo-1432821596592-e2c18b78144f?w=800&q=80', lessonCount: 18, durationMinutes: 270, category: 'Languages', level: 'Advanced' },
    { id: '23', instructorName: 'Pastor David Rivera', courseTitle: 'Apologetics Masterclass', thumbnailUrl: 'https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=800&q=80', lessonCount: 28, durationMinutes: 420, badge: 'POPULAR', category: 'Apologetics', level: 'Advanced' },
    { id: '24', instructorName: 'Pastor Maria Santos', courseTitle: 'Prophetic Literature', thumbnailUrl: 'https://images.unsplash.com/photo-1516979187457-637abb4f9353?w=800&q=80', lessonCount: 22, durationMinutes: 330, category: 'Bible Study', level: 'Advanced' },
  ],
};

const CATEGORIES = ['All', 'Faith', 'Worship', 'Prayer', 'Family', 'Leadership', 'Bible Study', 'Theology'];

const formatDuration = (minutes) => {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
};

// Carousel Component
const Carousel = ({ title, courses, goldTitle = false }) => {
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
      const scrollAmount = 280 * 3;
      scrollRef.current.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
        behavior: 'smooth'
      });
    }
  };

  return (
    <div className="mc2-carousel-section">
      <div className="mc2-carousel-header">
        <h3 className={`mc2-carousel-title ${goldTitle ? 'gold' : ''}`}>{title}</h3>
        <a href="#" className="mc2-see-all">See All</a>
      </div>
      <div className="mc2-carousel-wrapper">
        {canScrollLeft && (
          <button className="mc2-carousel-btn left" onClick={() => scroll('left')}>
            <ChevronLeft className="w-5 h-5" />
          </button>
        )}
        <div 
          className="mc2-carousel-track" 
          ref={scrollRef} 
          onScroll={checkScroll}
        >
          {courses.map((course) => (
            <CourseCard key={course.id} course={course} />
          ))}
        </div>
        {canScrollRight && (
          <button className="mc2-carousel-btn right" onClick={() => scroll('right')}>
            <ChevronRight className="w-5 h-5" />
          </button>
        )}
      </div>
    </div>
  );
};

// Course Card Component
const CourseCard = ({ course }) => {
  return (
    <div className="mc2-card" data-testid={`course-card-${course.id}`}>
      <div className="mc2-card-image">
        <img src={course.thumbnailUrl} alt={course.courseTitle} loading="lazy" />
        <div className="mc2-card-gradient" />
        {course.badge && (
          <span className={`mc2-card-badge ${course.badge.toLowerCase()}`}>
            {course.badge}
          </span>
        )}
        <div className="mc2-card-play">
          <Play className="w-6 h-6" />
        </div>
      </div>
      <div className="mc2-card-content">
        <span className="mc2-card-instructor">{course.instructorName}</span>
        <h4 className="mc2-card-title">{course.courseTitle}</h4>
        <span className="mc2-card-meta">
          {course.lessonCount} lessons · {formatDuration(course.durationMinutes)}
        </span>
      </div>
    </div>
  );
};

export default function PortalWatch() {
  const { user } = useOutletContext();
  const [activeCategory, setActiveCategory] = useState('All');
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 80);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="mc2-page" data-testid="masterclass-watch">
      {/* Hero Section */}
      <section className="mc2-hero" style={{ backgroundImage: `url(${FEATURED_COURSE.thumbnailUrl})` }}>
        <div className="mc2-hero-overlay" />
        <div className="mc2-hero-content">
          <span className="mc2-hero-category">{FEATURED_COURSE.category}</span>
          <h1 className="mc2-hero-title">{FEATURED_COURSE.instructorName}</h1>
          <p className="mc2-hero-subtitle">{FEATURED_COURSE.courseTitle}</p>
          <p className="mc2-hero-teaser">{FEATURED_COURSE.teaser}</p>
          <div className="mc2-hero-buttons">
            <button className="mc2-btn-primary">
              <Play className="w-4 h-4" /> Start Learning
            </button>
            <button className="mc2-btn-secondary">Preview</button>
          </div>
        </div>
        <div className="mc2-hero-meta">
          <Clock className="w-4 h-4" />
          {FEATURED_COURSE.lessonCount} lessons · {formatDuration(FEATURED_COURSE.durationMinutes)}
        </div>
      </section>

      {/* Sticky Category Bar */}
      <nav className={`mc2-category-bar ${isScrolled ? 'scrolled' : ''}`}>
        <div className="mc2-category-track">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              className={`mc2-category-pill ${activeCategory === cat ? 'active' : ''}`}
              onClick={() => setActiveCategory(cat)}
            >
              {cat}
            </button>
          ))}
        </div>
      </nav>

      {/* Content */}
      <main className="mc2-content">
        <Carousel title="START HERE — FOUNDATIONS" courses={COURSES.foundations} />
        <Carousel title="TRENDING THIS WEEK" courses={COURSES.trending} />
        
        {/* Instructor Spotlight */}
        <section className="mc2-spotlight">
          <div className="mc2-spotlight-image">
            <img src="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=800&q=80" alt="Pastor David Rivera" />
          </div>
          <div className="mc2-spotlight-content">
            <span className="mc2-spotlight-label">INSTRUCTOR SPOTLIGHT</span>
            <h2 className="mc2-spotlight-name">Pastor David Rivera</h2>
            <p className="mc2-spotlight-bio">
              With over 25 years of ministry experience, Pastor David has helped thousands 
              discover deeper faith and purpose. His teaching style combines theological 
              depth with practical application.
            </p>
            <a href="#" className="mc2-spotlight-link">
              Explore His Classes <ChevronRight className="w-4 h-4" />
            </a>
          </div>
        </section>

        <Carousel title="QUICK WINS · UNDER 30 MIN" courses={COURSES.quickWins} />
        <Carousel title="DEEP DIVES" courses={COURSES.deepDives} goldTitle />
      </main>

      {/* Footer CTA */}
      <footer className="mc2-footer-cta">
        <div className="mc2-footer-noise" />
        <h2 className="mc2-footer-title">Every Lesson. Every Teacher. All Access.</h2>
        <p className="mc2-footer-subtitle">Join Abundant Church's learning community today.</p>
        <button className="mc2-btn-gold">Get Started</button>
      </footer>
    </div>
  );
}
