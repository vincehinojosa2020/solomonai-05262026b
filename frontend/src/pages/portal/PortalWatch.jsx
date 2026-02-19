import { useState, useEffect, useRef } from 'react';
import { useOutletContext } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Play, ChevronLeft, ChevronRight, Clock, Search, 
  BookmarkPlus, Volume2, VolumeX, Pause, Maximize,
  X, Info, List, SkipBack, SkipForward, Settings
} from 'lucide-react';

// ═══════════════════════════════════════════════════════════════════════════════
// MASTERCLASS-STYLE ABUNDANT TV - Premium Dark Cinematic Experience
// ═══════════════════════════════════════════════════════════════════════════════

// Placeholder video URLs - using publicly accessible sample videos
const PLACEHOLDER_VIDEOS = [
  'https://www.w3schools.com/html/mov_bbb.mp4',
  'https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4',
  'https://www.w3schools.com/html/movie.mp4',
];

// Get a consistent video URL for each course
const getVideoUrl = (courseId) => {
  const index = parseInt(courseId) % PLACEHOLDER_VIDEOS.length;
  return PLACEHOLDER_VIDEOS[index];
};

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
    videoUrl: PLACEHOLDER_VIDEOS[0],
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
    videoUrl: PLACEHOLDER_VIDEOS[1],
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
    videoUrl: PLACEHOLDER_VIDEOS[2],
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
// VIDEO PLAYER MODAL COMPONENT
// ═══════════════════════════════════════════════════════════════════════════════

const VideoPlayerModal = ({ isOpen, onClose, course }) => {
  const videoRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [showControls, setShowControls] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showPlaylist, setShowPlaylist] = useState(false);
  const controlsTimeoutRef = useRef(null);
  const containerRef = useRef(null);

  // Format time helper
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Play/Pause toggle
  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  // Mute toggle
  const toggleMute = () => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  };

  // Fullscreen toggle
  const toggleFullscreen = () => {
    if (containerRef.current) {
      if (!isFullscreen) {
        if (containerRef.current.requestFullscreen) {
          containerRef.current.requestFullscreen();
        }
      } else {
        if (document.exitFullscreen) {
          document.exitFullscreen();
        }
      }
      setIsFullscreen(!isFullscreen);
    }
  };

  // Progress update
  const handleTimeUpdate = () => {
    if (videoRef.current) {
      const current = videoRef.current.currentTime;
      const dur = videoRef.current.duration;
      setCurrentTime(current);
      setDuration(dur);
      setProgress((current / dur) * 100);
    }
  };

  // Seek
  const handleSeek = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const pos = (e.clientX - rect.left) / rect.width;
    if (videoRef.current) {
      videoRef.current.currentTime = pos * videoRef.current.duration;
    }
  };

  // Skip forward/back
  const skip = (seconds) => {
    if (videoRef.current) {
      videoRef.current.currentTime += seconds;
    }
  };

  // Auto-hide controls
  const handleMouseMove = () => {
    setShowControls(true);
    if (controlsTimeoutRef.current) {
      clearTimeout(controlsTimeoutRef.current);
    }
    controlsTimeoutRef.current = setTimeout(() => {
      if (isPlaying) {
        setShowControls(false);
      }
    }, 3000);
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (!isOpen) return;
      switch (e.key) {
        case ' ':
        case 'k':
          e.preventDefault();
          togglePlay();
          break;
        case 'm':
          toggleMute();
          break;
        case 'f':
          toggleFullscreen();
          break;
        case 'ArrowLeft':
          skip(-10);
          break;
        case 'ArrowRight':
          skip(10);
          break;
        case 'Escape':
          onClose();
          break;
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, isPlaying]);

  // Auto-play on open
  useEffect(() => {
    if (isOpen && videoRef.current) {
      videoRef.current.play().then(() => setIsPlaying(true)).catch(() => {});
    }
  }, [isOpen, course]);

  // Cleanup on close
  useEffect(() => {
    if (!isOpen && videoRef.current) {
      videoRef.current.pause();
      setIsPlaying(false);
    }
  }, [isOpen]);

  if (!isOpen || !course) return null;

  const videoUrl = course.videoUrl || getVideoUrl(course.id);

  return (
    <AnimatePresence>
      <motion.div
        className="video-modal-backdrop"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
      >
        <motion.div
          ref={containerRef}
          className="video-modal-container"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          transition={{ duration: 0.3 }}
          onClick={(e) => e.stopPropagation()}
          onMouseMove={handleMouseMove}
          data-testid="video-player-modal"
        >
          {/* Video Element */}
          <video
            ref={videoRef}
            src={videoUrl}
            className="video-element"
            onTimeUpdate={handleTimeUpdate}
            onEnded={() => setIsPlaying(false)}
            onClick={togglePlay}
            playsInline
          />

          {/* Center Play Button (when paused) */}
          <AnimatePresence>
            {!isPlaying && (
              <motion.button
                className="video-center-play"
                onClick={togglePlay}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
              >
                <Play className="w-16 h-16" fill="currentColor" />
              </motion.button>
            )}
          </AnimatePresence>

          {/* Top Bar */}
          <motion.div
            className="video-top-bar"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: showControls ? 1 : 0, y: showControls ? 0 : -20 }}
            transition={{ duration: 0.2 }}
          >
            <button className="video-close-btn" onClick={onClose} data-testid="video-close-btn">
              <X className="w-6 h-6" />
            </button>
            <div className="video-title-info">
              <h2 className="video-title">{course.title}</h2>
              <p className="video-instructor">{course.instructor}</p>
            </div>
            <button 
              className="video-playlist-btn"
              onClick={() => setShowPlaylist(!showPlaylist)}
            >
              <List className="w-5 h-5" />
              <span>Lessons</span>
            </button>
          </motion.div>

          {/* Bottom Controls */}
          <motion.div
            className="video-controls"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: showControls ? 1 : 0, y: showControls ? 0 : 20 }}
            transition={{ duration: 0.2 }}
          >
            {/* Progress Bar */}
            <div className="video-progress-container" onClick={handleSeek}>
              <div className="video-progress-bar">
                <div 
                  className="video-progress-fill" 
                  style={{ width: `${progress}%` }}
                />
                <div 
                  className="video-progress-handle"
                  style={{ left: `${progress}%` }}
                />
              </div>
            </div>

            {/* Controls Row */}
            <div className="video-controls-row">
              <div className="video-controls-left">
                <button className="video-control-btn" onClick={() => skip(-10)}>
                  <SkipBack className="w-5 h-5" />
                </button>
                <button 
                  className="video-control-btn play-pause" 
                  onClick={togglePlay}
                  data-testid="video-play-pause"
                >
                  {isPlaying ? (
                    <Pause className="w-6 h-6" fill="currentColor" />
                  ) : (
                    <Play className="w-6 h-6" fill="currentColor" />
                  )}
                </button>
                <button className="video-control-btn" onClick={() => skip(10)}>
                  <SkipForward className="w-5 h-5" />
                </button>
                <button className="video-control-btn" onClick={toggleMute}>
                  {isMuted ? (
                    <VolumeX className="w-5 h-5" />
                  ) : (
                    <Volume2 className="w-5 h-5" />
                  )}
                </button>
                <span className="video-time">
                  {formatTime(currentTime)} / {formatTime(duration || 0)}
                </span>
              </div>
              <div className="video-controls-right">
                <button className="video-control-btn">
                  <Settings className="w-5 h-5" />
                </button>
                <button className="video-control-btn" onClick={toggleFullscreen}>
                  <Maximize className="w-5 h-5" />
                </button>
              </div>
            </div>
          </motion.div>

          {/* Playlist Sidebar */}
          <AnimatePresence>
            {showPlaylist && (
              <motion.div
                className="video-playlist-sidebar"
                initial={{ opacity: 0, x: 100 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 100 }}
              >
                <div className="playlist-header">
                  <h3>Lessons</h3>
                  <button onClick={() => setShowPlaylist(false)}>
                    <X className="w-5 h-5" />
                  </button>
                </div>
                <div className="playlist-items">
                  {Array.from({ length: course.lessons || 8 }, (_, i) => (
                    <div 
                      key={i} 
                      className={`playlist-item ${i === 0 ? 'active' : ''}`}
                    >
                      <span className="playlist-item-num">{i + 1}</span>
                      <div className="playlist-item-info">
                        <p className="playlist-item-title">
                          {i === 0 ? 'Introduction' : `Lesson ${i + 1}: ${course.title.split(' ')[0]} Basics`}
                        </p>
                        <span className="playlist-item-duration">
                          {Math.floor(Math.random() * 15) + 5}:00
                        </span>
                      </div>
                      {i === 0 && <Play className="w-4 h-4 playlist-playing" />}
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// CAROUSEL & CARD COMPONENTS
// ═══════════════════════════════════════════════════════════════════════════════

// Horizontal Carousel Component
const Carousel = ({ title, subtitle, courses, goldAccent = false, onPlayCourse }) => {
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
            <CourseCard 
              key={course.id} 
              course={course} 
              index={index}
              onPlay={() => onPlayCourse(course)}
            />
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
const CourseCard = ({ course, index, onPlay }) => {
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
      onClick={onPlay}
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
const InstructorSpotlight = ({ onPlay }) => {
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
          onClick={() => onPlay({
            id: 'spotlight',
            title: 'Faith in the Storm - Introduction',
            instructor: 'Pastor David Rivera',
            lessons: 24,
            videoUrl: PLACEHOLDER_VIDEOS[0]
          })}
        >
          <Play className="w-4 h-4" />
          Watch Preview
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
  
  // Video Player State
  const [videoModalOpen, setVideoModalOpen] = useState(false);
  const [selectedCourse, setSelectedCourse] = useState(null);

  // Open video player
  const handlePlayCourse = (course) => {
    setSelectedCourse(course);
    setVideoModalOpen(true);
  };

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
      {/* ═══ VIDEO PLAYER MODAL ═══ */}
      <VideoPlayerModal
        isOpen={videoModalOpen}
        onClose={() => setVideoModalOpen(false)}
        course={selectedCourse}
      />

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
                  onClick={() => handlePlayCourse({
                    ...currentHero,
                    id: currentHero.id,
                    image: currentHero.backgroundImg,
                  })}
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
          onPlayCourse={handlePlayCourse}
        />
        
        {/* Trending Now */}
        <Carousel 
          title="Trending This Week" 
          courses={COURSES.trending}
          onPlayCourse={handlePlayCourse}
        />
        
        {/* Instructor Spotlight */}
        <InstructorSpotlight onPlay={handlePlayCourse} />
        
        {/* New Releases */}
        <Carousel 
          title="New Releases" 
          subtitle="Fresh content just added"
          courses={COURSES.newReleases}
          onPlayCourse={handlePlayCourse}
        />
        
        {/* Deep Studies */}
        <Carousel 
          title="Deep Dives" 
          subtitle="In-depth explorations for serious students"
          courses={COURSES.deepStudies}
          goldAccent
          onPlayCourse={handlePlayCourse}
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
