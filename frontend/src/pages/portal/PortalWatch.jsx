import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Play, Clock, Calendar, Search, ChevronRight, Tv, BookOpen, Heart } from 'lucide-react';
import { API_URL } from '@/lib/utils';

// Demo sermon data for Abundant Church
const SERMON_SERIES = [
  {
    id: 'series-1',
    title: 'Unshakeable Faith',
    description: 'Building a foundation that lasts through every storm',
    thumbnail: 'https://images.unsplash.com/photo-1507692049790-de58290a4334?w=800&q=80',
    sermonCount: 6,
    year: 2026
  },
  {
    id: 'series-2', 
    title: 'The Heart of Worship',
    description: 'Discovering true worship in spirit and truth',
    thumbnail: 'https://images.unsplash.com/photo-1478147427282-58a87a120781?w=800&q=80',
    sermonCount: 4,
    year: 2026
  },
  {
    id: 'series-3',
    title: 'Family Matters',
    description: 'Strengthening the bonds that matter most',
    thumbnail: 'https://images.unsplash.com/photo-1511895426328-dc8714191300?w=800&q=80',
    sermonCount: 5,
    year: 2025
  },
  {
    id: 'series-4',
    title: 'Purpose Driven',
    description: 'Finding your calling and living it out',
    thumbnail: 'https://images.unsplash.com/photo-1499209974431-9dddcece7f88?w=800&q=80',
    sermonCount: 8,
    year: 2025
  }
];

const RECENT_SERMONS = [
  {
    id: 'sermon-1',
    title: 'Standing Strong in the Storm',
    speaker: 'Pastor David Rivera',
    date: 'Feb 16, 2026',
    duration: '42:18',
    series: 'Unshakeable Faith',
    thumbnail: 'https://images.unsplash.com/photo-1507692049790-de58290a4334?w=800&q=80',
    videoUrl: '#',
    views: 1247
  },
  {
    id: 'sermon-2',
    title: 'When Fear Meets Faith',
    speaker: 'Pastor David Rivera',
    date: 'Feb 9, 2026',
    duration: '38:45',
    series: 'Unshakeable Faith',
    thumbnail: 'https://images.unsplash.com/photo-1504052434569-70ad5836ab65?w=800&q=80',
    videoUrl: '#',
    views: 982
  },
  {
    id: 'sermon-3',
    title: 'The Foundation That Never Fails',
    speaker: 'Pastor David Rivera',
    date: 'Feb 2, 2026',
    duration: '45:12',
    series: 'Unshakeable Faith',
    thumbnail: 'https://images.unsplash.com/photo-1445445290350-18a3b86e0b5a?w=800&q=80',
    videoUrl: '#',
    views: 1456
  },
  {
    id: 'sermon-4',
    title: 'Songs of the Heart',
    speaker: 'Pastor Maria Santos',
    date: 'Jan 26, 2026',
    duration: '36:30',
    series: 'The Heart of Worship',
    thumbnail: 'https://images.unsplash.com/photo-1478147427282-58a87a120781?w=800&q=80',
    videoUrl: '#',
    views: 873
  },
  {
    id: 'sermon-5',
    title: 'Created to Worship',
    speaker: 'Pastor David Rivera',
    date: 'Jan 19, 2026',
    duration: '41:55',
    series: 'The Heart of Worship',
    thumbnail: 'https://images.unsplash.com/photo-1510915361894-db8b60106cb1?w=800&q=80',
    videoUrl: '#',
    views: 1102
  },
  {
    id: 'sermon-6',
    title: 'Building Strong Families',
    speaker: 'Pastor David Rivera',
    date: 'Jan 12, 2026',
    duration: '44:20',
    series: 'Family Matters',
    thumbnail: 'https://images.unsplash.com/photo-1511895426328-dc8714191300?w=800&q=80',
    videoUrl: '#',
    views: 1328
  }
];

export default function PortalWatch() {
  const { user } = useOutletContext();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSeries, setSelectedSeries] = useState(null);
  const [featuredSermon, setFeaturedSermon] = useState(RECENT_SERMONS[0]);

  const filteredSermons = RECENT_SERMONS.filter(sermon => {
    const matchesSearch = !searchQuery || 
      sermon.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      sermon.speaker.toLowerCase().includes(searchQuery.toLowerCase()) ||
      sermon.series.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesSeries = !selectedSeries || sermon.series === selectedSeries;
    return matchesSearch && matchesSeries;
  });

  return (
    <div className="portal-watch" data-testid="portal-watch">
      {/* Header */}
      <div className="watch-header">
        <div className="watch-header-content">
          <div className="watch-logo">
            <Tv className="w-8 h-8 text-blue-500" />
            <div>
              <h1 className="watch-title">Abundant TV</h1>
              <p className="watch-subtitle">Sermons & Messages from Abundant Church</p>
            </div>
          </div>
          
          {/* Search */}
          <div className="watch-search">
            <Search className="w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search sermons..."
              className="watch-search-input"
              data-testid="watch-search"
            />
          </div>
        </div>
      </div>

      {/* Featured Sermon */}
      <div className="watch-featured" data-testid="featured-sermon">
        <div className="watch-featured-video">
          <img 
            src={featuredSermon.thumbnail} 
            alt={featuredSermon.title}
            className="watch-featured-img"
          />
          <div className="watch-featured-overlay">
            <button className="watch-play-btn" data-testid="play-featured">
              <Play className="w-8 h-8" />
            </button>
          </div>
          <div className="watch-featured-badge">Latest Message</div>
        </div>
        <div className="watch-featured-info">
          <span className="watch-featured-series">{featuredSermon.series}</span>
          <h2 className="watch-featured-title">{featuredSermon.title}</h2>
          <p className="watch-featured-speaker">{featuredSermon.speaker}</p>
          <div className="watch-featured-meta">
            <span><Calendar className="w-4 h-4" /> {featuredSermon.date}</span>
            <span><Clock className="w-4 h-4" /> {featuredSermon.duration}</span>
          </div>
          <div className="watch-featured-actions">
            <button className="watch-btn primary" data-testid="watch-now-btn">
              <Play className="w-4 h-4" /> Watch Now
            </button>
            <button className="watch-btn secondary">
              <Heart className="w-4 h-4" /> Save
            </button>
            <button className="watch-btn secondary">
              <BookOpen className="w-4 h-4" /> Notes
            </button>
          </div>
        </div>
      </div>

      {/* Series Section */}
      <div className="watch-section">
        <div className="watch-section-header">
          <h3 className="watch-section-title">Sermon Series</h3>
          <button className="watch-view-all">View All →</button>
        </div>
        <div className="watch-series-grid" data-testid="series-grid">
          {SERMON_SERIES.map((series) => (
            <div 
              key={series.id} 
              className={`watch-series-card ${selectedSeries === series.title ? 'active' : ''}`}
              onClick={() => setSelectedSeries(selectedSeries === series.title ? null : series.title)}
              data-testid={`series-${series.id}`}
            >
              <div className="watch-series-img-wrapper">
                <img src={series.thumbnail} alt={series.title} className="watch-series-img" />
                <div className="watch-series-overlay">
                  <span className="watch-series-count">{series.sermonCount} Messages</span>
                </div>
              </div>
              <div className="watch-series-info">
                <h4 className="watch-series-title">{series.title}</h4>
                <p className="watch-series-desc">{series.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Sermons */}
      <div className="watch-section">
        <div className="watch-section-header">
          <h3 className="watch-section-title">
            {selectedSeries ? `${selectedSeries} Series` : 'Recent Messages'}
          </h3>
          {selectedSeries && (
            <button 
              className="watch-clear-filter"
              onClick={() => setSelectedSeries(null)}
            >
              Clear Filter ✕
            </button>
          )}
        </div>
        <div className="watch-sermons-grid" data-testid="sermons-grid">
          {filteredSermons.map((sermon) => (
            <div key={sermon.id} className="watch-sermon-card" data-testid={`sermon-${sermon.id}`}>
              <div className="watch-sermon-thumbnail">
                <img src={sermon.thumbnail} alt={sermon.title} />
                <div className="watch-sermon-duration">{sermon.duration}</div>
                <div className="watch-sermon-play">
                  <Play className="w-6 h-6" />
                </div>
              </div>
              <div className="watch-sermon-info">
                <span className="watch-sermon-series">{sermon.series}</span>
                <h4 className="watch-sermon-title">{sermon.title}</h4>
                <p className="watch-sermon-speaker">{sermon.speaker}</p>
                <div className="watch-sermon-meta">
                  <span>{sermon.date}</span>
                  <span>•</span>
                  <span>{sermon.views.toLocaleString()} views</span>
                </div>
              </div>
            </div>
          ))}
        </div>
        
        {filteredSermons.length === 0 && (
          <div className="watch-no-results">
            <p>No sermons found matching your search.</p>
          </div>
        )}
      </div>

      {/* Live Service Banner */}
      <div className="watch-live-banner" data-testid="live-banner">
        <div className="watch-live-content">
          <div className="watch-live-indicator">
            <span className="watch-live-dot"></span>
            LIVE
          </div>
          <div>
            <h3>Join Us This Sunday</h3>
            <p>Live stream at 9:00 AM & 11:00 AM</p>
          </div>
        </div>
        <button className="watch-btn primary">
          Set Reminder
        </button>
      </div>
    </div>
  );
}
