import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Play, Clock, ChevronRight, Search, X, Volume2, VolumeX } from 'lucide-react';

// Demo sermon data for Abundant Church - Masterclass style
const FEATURED_SERMONS = [
  {
    id: 'featured-1',
    title: 'Standing Strong in the Storm',
    subtitle: 'Building faith that weathers any trial',
    speaker: 'Pastor David Rivera',
    speakerTitle: 'Lead Pastor, Abundant Church',
    speakerImage: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=200&q=80',
    thumbnail: 'https://images.unsplash.com/photo-1507692049790-de58290a4334?w=1200&q=80',
    duration: '42 min',
    lessons: 6,
    series: 'Unshakeable Faith'
  },
  {
    id: 'featured-2',
    title: 'The Heart of Worship',
    subtitle: 'Discovering authentic praise',
    speaker: 'Pastor Maria Santos',
    speakerTitle: 'Worship Pastor',
    speakerImage: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=200&q=80',
    thumbnail: 'https://images.unsplash.com/photo-1478147427282-58a87a120781?w=1200&q=80',
    duration: '36 min',
    lessons: 4,
    series: 'Worship Series'
  },
  {
    id: 'featured-3',
    title: 'Purpose Driven Life',
    subtitle: 'Finding your calling in God\'s plan',
    speaker: 'Pastor David Rivera',
    speakerTitle: 'Lead Pastor, Abundant Church',
    speakerImage: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=200&q=80',
    thumbnail: 'https://images.unsplash.com/photo-1499209974431-9dddcece7f88?w=1200&q=80',
    duration: '48 min',
    lessons: 8,
    series: 'Purpose Series'
  }
];

const CATEGORIES = [
  { id: 'all', name: 'All Messages' },
  { id: 'faith', name: 'Faith & Trust' },
  { id: 'worship', name: 'Worship' },
  { id: 'family', name: 'Family' },
  { id: 'leadership', name: 'Leadership' },
  { id: 'prayer', name: 'Prayer' },
];

const ALL_SERMONS = [
  {
    id: 'sermon-1',
    title: 'When Fear Meets Faith',
    speaker: 'Pastor David Rivera',
    speakerImage: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=200&q=80',
    thumbnail: 'https://images.unsplash.com/photo-1504052434569-70ad5836ab65?w=800&q=80',
    duration: '38 min',
    lessons: 1,
    category: 'faith'
  },
  {
    id: 'sermon-2',
    title: 'Songs of the Heart',
    speaker: 'Pastor Maria Santos',
    speakerImage: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=200&q=80',
    thumbnail: 'https://images.unsplash.com/photo-1510915361894-db8b60106cb1?w=800&q=80',
    duration: '41 min',
    lessons: 1,
    category: 'worship'
  },
  {
    id: 'sermon-3',
    title: 'Building Strong Families',
    speaker: 'Pastor David Rivera',
    speakerImage: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=200&q=80',
    thumbnail: 'https://images.unsplash.com/photo-1511895426328-dc8714191300?w=800&q=80',
    duration: '44 min',
    lessons: 5,
    category: 'family'
  },
  {
    id: 'sermon-4',
    title: 'The Foundation That Never Fails',
    speaker: 'Pastor David Rivera',
    speakerImage: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=200&q=80',
    thumbnail: 'https://images.unsplash.com/photo-1445445290350-18a3b86e0b5a?w=800&q=80',
    duration: '45 min',
    lessons: 1,
    category: 'faith'
  },
  {
    id: 'sermon-5',
    title: 'Leading with Integrity',
    speaker: 'Pastor David Rivera',
    speakerImage: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=200&q=80',
    thumbnail: 'https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?w=800&q=80',
    duration: '39 min',
    lessons: 4,
    category: 'leadership'
  },
  {
    id: 'sermon-6',
    title: 'The Power of Prayer',
    speaker: 'Pastor Maria Santos',
    speakerImage: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=200&q=80',
    thumbnail: 'https://images.unsplash.com/photo-1506157786151-b8491531f063?w=800&q=80',
    duration: '35 min',
    lessons: 3,
    category: 'prayer'
  },
  {
    id: 'sermon-7',
    title: 'Created to Worship',
    speaker: 'Pastor Maria Santos',
    speakerImage: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=200&q=80',
    thumbnail: 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=800&q=80',
    duration: '42 min',
    lessons: 1,
    category: 'worship'
  },
  {
    id: 'sermon-8',
    title: 'Raising Godly Children',
    speaker: 'Pastor David Rivera',
    speakerImage: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=200&q=80',
    thumbnail: 'https://images.unsplash.com/photo-1536640712-4d4c36ff0e4e?w=800&q=80',
    duration: '47 min',
    lessons: 1,
    category: 'family'
  }
];

export default function PortalWatch() {
  const { user } = useOutletContext();
  const [currentSlide, setCurrentSlide] = useState(0);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [isMuted, setIsMuted] = useState(true);

  // Auto-rotate featured sermons
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % FEATURED_SERMONS.length);
    }, 8000);
    return () => clearInterval(timer);
  }, []);

  const filteredSermons = ALL_SERMONS.filter(sermon => {
    const matchesCategory = selectedCategory === 'all' || sermon.category === selectedCategory;
    const matchesSearch = !searchQuery || 
      sermon.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      sermon.speaker.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const featured = FEATURED_SERMONS[currentSlide];

  return (
    <div className="mc-watch" data-testid="portal-watch-masterclass">
      {/* Hero Section - Full width background */}
      <div className="mc-hero" style={{ backgroundImage: `url(${featured.thumbnail})` }}>
        <div className="mc-hero-overlay" />
        
        {/* Top Navigation */}
        <div className="mc-nav">
          <div className="mc-logo">
            <span className="mc-logo-text">ABUNDANT</span>
            <span className="mc-logo-tv">TV</span>
          </div>
          
          <div className="mc-nav-links">
            {CATEGORIES.slice(0, 5).map((cat) => (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className={`mc-nav-link ${selectedCategory === cat.id ? 'active' : ''}`}
              >
                {cat.name}
              </button>
            ))}
          </div>

          <div className="mc-nav-actions">
            {searchOpen ? (
              <div className="mc-search-box">
                <Search className="w-4 h-4" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search messages..."
                  autoFocus
                  className="mc-search-input"
                />
                <button onClick={() => { setSearchOpen(false); setSearchQuery(''); }}>
                  <X className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button onClick={() => setSearchOpen(true)} className="mc-search-btn">
                <Search className="w-5 h-5" />
              </button>
            )}
          </div>
        </div>

        {/* Hero Content */}
        <div className="mc-hero-content">
          <div className="mc-hero-speaker">
            <img src={featured.speakerImage} alt={featured.speaker} className="mc-speaker-img" />
            <div>
              <h3 className="mc-speaker-name">{featured.speaker}</h3>
              <p className="mc-speaker-title">{featured.speakerTitle}</p>
            </div>
          </div>
          
          <h1 className="mc-hero-title">{featured.title}</h1>
          <p className="mc-hero-subtitle">{featured.subtitle}</p>
          
          <div className="mc-hero-meta">
            <span>{featured.lessons} {featured.lessons === 1 ? 'Message' : 'Messages'}</span>
            <span className="mc-meta-dot">•</span>
            <span>{featured.duration}</span>
          </div>

          <div className="mc-hero-actions">
            <button className="mc-btn-primary" data-testid="watch-trailer-btn">
              <Play className="w-5 h-5" /> Watch Trailer
            </button>
            <button 
              className="mc-btn-icon"
              onClick={() => setIsMuted(!isMuted)}
            >
              {isMuted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Slide Indicators */}
        <div className="mc-hero-dots">
          {FEATURED_SERMONS.map((_, idx) => (
            <button
              key={idx}
              onClick={() => setCurrentSlide(idx)}
              className={`mc-dot ${idx === currentSlide ? 'active' : ''}`}
            />
          ))}
        </div>
      </div>

      {/* Content Section */}
      <div className="mc-content">
        {/* Category Pills - Mobile */}
        <div className="mc-categories-mobile">
          {CATEGORIES.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`mc-category-pill ${selectedCategory === cat.id ? 'active' : ''}`}
            >
              {cat.name}
            </button>
          ))}
        </div>

        {/* Section Title */}
        <div className="mc-section-header">
          <h2 className="mc-section-title">
            {selectedCategory === 'all' ? 'All Messages' : CATEGORIES.find(c => c.id === selectedCategory)?.name}
          </h2>
          <span className="mc-section-count">{filteredSermons.length} available</span>
        </div>

        {/* Sermon Grid */}
        <div className="mc-grid">
          {filteredSermons.map((sermon) => (
            <div key={sermon.id} className="mc-card" data-testid={`mc-card-${sermon.id}`}>
              <div className="mc-card-img-wrapper">
                <img src={sermon.thumbnail} alt={sermon.title} className="mc-card-img" />
                <div className="mc-card-overlay">
                  <button className="mc-card-play">
                    <Play className="w-8 h-8" />
                  </button>
                </div>
                <div className="mc-card-duration">
                  <Clock className="w-3 h-3" />
                  {sermon.duration}
                </div>
              </div>
              <div className="mc-card-content">
                <div className="mc-card-speaker">
                  <img src={sermon.speakerImage} alt={sermon.speaker} className="mc-card-speaker-img" />
                  <span>{sermon.speaker}</span>
                </div>
                <h3 className="mc-card-title">{sermon.title}</h3>
                <p className="mc-card-lessons">
                  {sermon.lessons} {sermon.lessons === 1 ? 'message' : 'messages'}
                </p>
              </div>
            </div>
          ))}
        </div>

        {filteredSermons.length === 0 && (
          <div className="mc-no-results">
            <p>No messages found. Try a different search or category.</p>
          </div>
        )}

        {/* Bottom CTA */}
        <div className="mc-cta">
          <div className="mc-cta-content">
            <h3>Join us this Sunday</h3>
            <p>Experience worship live at 9:00 AM & 11:00 AM</p>
          </div>
          <button className="mc-btn-outline">
            Set Reminder <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
