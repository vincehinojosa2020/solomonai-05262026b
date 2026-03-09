import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Church, MapPin, Wifi, Flame, Trophy, Star, Crown, 
  ChevronRight, Clock, Check, Users, Heart, Play
} from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

// Attendance streak badges configuration
const STREAK_BADGES = [
  { threshold: 4, name: 'Month Strong', icon: '🔥', color: '#f97316' },
  { threshold: 8, name: '2 Month Champion', icon: '⭐', color: '#eab308' },
  { threshold: 12, name: 'Quarter Master', icon: '🏆', color: '#22c55e' },
  { threshold: 26, name: 'Half Year Hero', icon: '👑', color: '#8b5cf6' },
  { threshold: 52, name: 'Year of Faith', icon: '💎', color: '#06b6d4' },
];

// Service Mode Banner - Shows when it's service day/time
export const ServiceModeBanner = ({ 
  isServiceDay, 
  isServiceTime, 
  currentService, 
  nextService,
  checkInStatus,
  onCheckIn,
  streak = 0
}) => {
  const [checkingIn, setCheckingIn] = useState(false);

  const handleCheckIn = async (type) => {
    setCheckingIn(true);
    try {
      await onCheckIn(type);
    } finally {
      setCheckingIn(false);
    }
  };

  if (!isServiceDay && !isServiceTime) return null;

  return (
    <motion.div
      className="service-mode-banner"
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      data-testid="service-mode-banner"
    >
      <div className="service-mode-glow" />
      
      {/* Main Content */}
      <div className="service-mode-content">
        {isServiceTime && currentService ? (
          <>
            <div className="service-mode-live">
              <span className="live-dot" />
              <span>LIVE NOW</span>
            </div>
            <h2 className="service-mode-title">
              {currentService.name} is happening now!
            </h2>
            <p className="service-mode-subtitle">
              Join us for worship, prayer, and the Word
            </p>
          </>
        ) : (
          <>
            <div className="service-mode-upcoming">
              <Clock className="w-4 h-4" />
              <span>Coming Up</span>
            </div>
            <h2 className="service-mode-title">
              It's {new Date().toLocaleDateString('en-US', { weekday: 'long' })}!
            </h2>
            <p className="service-mode-subtitle">
              {nextService ? `${nextService.name} starts at ${nextService.start}` : 'Service day - join us today!'}
            </p>
          </>
        )}

        {/* Check-in Section */}
        {!checkInStatus ? (
          <div className="service-mode-checkin">
            <p className="checkin-prompt">How are you joining today?</p>
            <div className="checkin-buttons">
              <button
                className="checkin-btn in-person"
                onClick={() => handleCheckIn('in_person')}
                disabled={checkingIn}
                data-testid="checkin-in-person"
              >
                <MapPin className="w-5 h-5" />
                <span>I'm Here</span>
                <span className="checkin-sub">In Person</span>
              </button>
              <button
                className="checkin-btn online"
                onClick={() => handleCheckIn('online')}
                disabled={checkingIn}
                data-testid="checkin-online"
              >
                <Wifi className="w-5 h-5" />
                <span>Watching Online</span>
                <span className="checkin-sub">From Home</span>
              </button>
            </div>
          </div>
        ) : (
          <div className="service-mode-checked-in" data-testid="checked-in-status">
            <div className="checked-in-badge">
              <Check className="w-5 h-5" />
              <span>Checked In {checkInStatus === 'in_person' ? 'In Person' : 'Online'}</span>
            </div>
            {streak > 0 && (
              <div className="streak-display">
                <Flame className="w-5 h-5" />
                <span>{streak} Week Streak!</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Watch Live Button */}
      {isServiceTime && (
        <a href="/portal/watch" className="service-mode-watch-btn" data-testid="watch-live-btn">
          <Play className="w-5 h-5" />
          Watch Live
        </a>
      )}
    </motion.div>
  );
};

// Attendance Streak Card
export const AttendanceStreakCard = ({ 
  currentStreak = 0, 
  longestStreak = 0, 
  totalAttended = 0,
  badges = []
}) => {
  const nextBadge = STREAK_BADGES.find(b => b.threshold > currentStreak);
  const weeksToNext = nextBadge ? nextBadge.threshold - currentStreak : 0;

  return (
    <motion.div 
      className="streak-card"
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      data-testid="attendance-streak-card"
    >
      <div className="streak-card-header">
        <Flame className="w-6 h-6 text-orange-500" />
        <h3>Attendance Streak</h3>
      </div>

      <div className="streak-stats">
        <div className="streak-stat main">
          <span className="streak-number">{currentStreak}</span>
          <span className="streak-label">Week Streak</span>
        </div>
        <div className="streak-stat">
          <span className="streak-number-sm">{longestStreak}</span>
          <span className="streak-label">Best Streak</span>
        </div>
        <div className="streak-stat">
          <span className="streak-number-sm">{totalAttended}</span>
          <span className="streak-label">Total Services</span>
        </div>
      </div>

      {/* Progress to next badge */}
      {nextBadge && (
        <div className="streak-progress">
          <div className="streak-progress-header">
            <span>Next Badge: {nextBadge.icon} {nextBadge.name}</span>
            <span>{weeksToNext} weeks to go</span>
          </div>
          <div className="streak-progress-bar">
            <motion.div 
              className="streak-progress-fill"
              initial={{ width: 0 }}
              animate={{ width: `${(currentStreak / nextBadge.threshold) * 100}%` }}
              style={{ backgroundColor: nextBadge.color }}
            />
          </div>
        </div>
      )}

      {/* Earned Badges */}
      {badges.length > 0 && (
        <div className="streak-badges">
          <span className="badges-label">Earned Badges:</span>
          <div className="badges-list">
            {badges.map((badge, idx) => (
              <div key={idx} className="badge-item" title={badge.name}>
                <span className="badge-icon">{badge.icon}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  );
};

// Prayer Wall Preview Card
export const PrayerWallCard = ({ requests = [], onViewAll }) => {
  return (
    <motion.div 
      className="prayer-wall-card"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      data-testid="prayer-wall-card"
    >
      <div className="prayer-wall-header">
        <div className="prayer-wall-title">
          <Heart className="w-5 h-5 text-rose-500" />
          <h3>Prayer Wall</h3>
        </div>
        <button onClick={onViewAll} className="prayer-wall-view-all">
          View All <ChevronRight className="w-4 h-4" />
        </button>
      </div>

      <div className="prayer-wall-list">
        {requests.length === 0 ? (
          <p className="prayer-wall-empty">No prayer requests shared yet</p>
        ) : (
          requests.slice(0, 3).map((req, idx) => (
            <div key={req.id || idx} className="prayer-wall-item">
              <div className="prayer-item-header">
                <span className="prayer-category">{getCategoryIcon(req.category)} {req.category}</span>
                <span className="prayer-count">🙏 {req.prayer_count || 0}</span>
              </div>
              <p className="prayer-title">{req.title}</p>
              <p className="prayer-author">
                {req.is_anonymous ? 'Anonymous' : req.user_name}
              </p>
            </div>
          ))
        )}
      </div>

      <a href="/portal/prayer" className="prayer-wall-cta" data-testid="prayer-request-cta">
        <Heart className="w-4 h-4" />
        Submit Prayer Request
      </a>
    </motion.div>
  );
};

const getCategoryIcon = (category) => {
  const icons = {
    general: '🙏',
    healing: '💚',
    family: '👨‍👩‍👧‍👦',
    financial: '💰',
    guidance: '🧭',
    thanksgiving: '🙌',
    salvation: '✝️',
    relationships: '❤️',
  };
  return icons[category] || '🙏';
};

export default ServiceModeBanner;
