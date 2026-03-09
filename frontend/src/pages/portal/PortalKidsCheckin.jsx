import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Plus, Check, X, Clock, AlertCircle,
  Phone, Heart, QrCode, Sparkles, Star,
  PartyPopper, Sun, CloudSun
} from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

// Fun avatar colors for children
const AVATAR_COLORS = [
  { bg: 'linear-gradient(135deg, #FF6B6B 0%, #FF8E8E 100%)', emoji: '🦁' },
  { bg: 'linear-gradient(135deg, #4ECDC4 0%, #7EDAD4 100%)', emoji: '🐸' },
  { bg: 'linear-gradient(135deg, #FFE66D 0%, #FFF09D 100%)', emoji: '🌻' },
  { bg: 'linear-gradient(135deg, #95E1D3 0%, #B8EDE3 100%)', emoji: '🐢' },
  { bg: 'linear-gradient(135deg, #DDA0DD 0%, #E8C0E8 100%)', emoji: '🦋' },
  { bg: 'linear-gradient(135deg, #87CEEB 0%, #ADD8E6 100%)', emoji: '🐬' },
  { bg: 'linear-gradient(135deg, #F4A460 0%, #F7C797 100%)', emoji: '🦊' },
  { bg: 'linear-gradient(135deg, #98D8C8 0%, #BCE4D8 100%)', emoji: '🐢' },
];

// Get consistent color for a child based on their name
const getAvatarStyle = (name) => {
  const index = name.charCodeAt(0) % AVATAR_COLORS.length;
  return AVATAR_COLORS[index];
};

export default function PortalKidsCheckin() {
  const { user, tenant } = useOutletContext();
  const [children, setChildren] = useState([]);
  const [checkins, setCheckins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddChild, setShowAddChild] = useState(false);
  const [showCheckin, setShowCheckin] = useState(false);
  const [selectedChild, setSelectedChild] = useState(null);
  const [showSuccess, setShowSuccess] = useState(null);
  
  // New child form
  const [newChild, setNewChild] = useState({
    name: '',
    birthdate: '',
    allergies: '',
    special_needs: '',
    emergency_contact: '',
    emergency_phone: ''
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Fetch children
      const childRes = await fetch(`${API_URL}/portal/kids`, { credentials: 'include' });
      if (childRes.ok) {
        const childData = await childRes.json();
        setChildren(childData.children || []);
      }
      
      // Fetch active checkins
      const checkinRes = await fetch(`${API_URL}/portal/kids/checkins/active`, { credentials: 'include' });
      if (checkinRes.ok) {
        const checkinData = await checkinRes.json();
        setCheckins(checkinData.checkins || []);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const addChild = async () => {
    if (!newChild.name || !newChild.birthdate) {
      toast.error('Please enter child name and birthdate');
      return;
    }

    try {
      const res = await fetch(`${API_URL}/portal/kids`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(newChild)
      });

      if (res.ok) {
        toast.success(`${newChild.name} added!`);
        setShowAddChild(false);
        setNewChild({ name: '', birthdate: '', allergies: '', special_needs: '', emergency_contact: '', emergency_phone: '' });
        fetchData();
      } else {
        toast.error('Failed to add child');
      }
    } catch (error) {
      toast.error('Error adding child');
    }
  };

  const checkInChild = async (child) => {
    try {
      const res = await fetch(`${API_URL}/portal/kids/${child.id}/checkin`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ classroom: 'Sunday School' })
      });

      if (res.ok) {
        const data = await res.json();
        // Show success celebration
        setShowSuccess({ child, pickup_code: data.pickup_code });
        setTimeout(() => setShowSuccess(null), 5000);
        fetchData();
      } else {
        toast.error('Check-in failed');
      }
    } catch (error) {
      toast.error('Error during check-in');
    }
  };

  const getAge = (birthdate) => {
    const today = new Date();
    const birth = new Date(birthdate);
    let age = today.getFullYear() - birth.getFullYear();
    const m = today.getMonth() - birth.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) {
      age--;
    }
    return age;
  };

  const isCheckedIn = (childId) => {
    return checkins.some(c => c.child_id === childId && c.status === 'checked_in');
  };

  const getCheckinInfo = (childId) => {
    return checkins.find(c => c.child_id === childId && c.status === 'checked_in');
  };

  if (loading) {
    return (
      <div className="kc-loading" data-testid="kids-checkin-loading">
        <div className="kc-loading-spinner">
          <Sun className="kc-spin-icon" />
        </div>
        <p>Getting ready for fun...</p>
      </div>
    );
  }

  return (
    <div className="kc-page" data-testid="kids-checkin-page">
      {/* Floating decorations */}
      <div className="kc-decorations">
        <span className="kc-deco kc-deco-1">🎈</span>
        <span className="kc-deco kc-deco-2">⭐</span>
        <span className="kc-deco kc-deco-3">🌈</span>
        <span className="kc-deco kc-deco-4">☁️</span>
        <span className="kc-deco kc-deco-5">🎨</span>
      </div>

      {/* Header */}
      <div className="kc-header">
        <div className="kc-header-bg">
          <div className="kc-header-wave"></div>
        </div>
        <div className="kc-header-content">
          <div className="kc-header-icon">
            <span className="kc-header-emoji">👶</span>
            <Sparkles className="kc-sparkle kc-sparkle-1" />
            <Sparkles className="kc-sparkle kc-sparkle-2" />
          </div>
          <div className="kc-header-text">
            <h1>Kids Check-in</h1>
            <p>Sunday School Adventure Awaits! ✨</p>
          </div>
        </div>
        <button 
          className="kc-add-btn"
          onClick={() => setShowAddChild(true)}
          data-testid="add-child-btn"
        >
          <Plus className="w-5 h-5" />
          <span>Add Child</span>
        </button>
      </div>

      {/* Ready to Check-in Banner */}
      {children.length > 0 && !checkins.some(c => c.status === 'checked_in') && (
        <motion.div 
          className="kc-ready-banner"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="kc-ready-icon">
            <CloudSun className="w-8 h-8" />
          </div>
          <div className="kc-ready-text">
            <h3>Ready for Today's Adventure? 🎉</h3>
            <p>Tap a child below to check them in for Sunday School!</p>
          </div>
        </motion.div>
      )}

      {/* Children Grid */}
      <div className="kc-children-grid">
        {children.length === 0 ? (
          <motion.div 
            className="kc-empty"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
          >
            <div className="kc-empty-illustration">
              <span className="kc-empty-emoji">🧒👧</span>
              <div className="kc-empty-stars">
                <Star className="kc-star kc-star-1" />
                <Star className="kc-star kc-star-2" />
                <Star className="kc-star kc-star-3" />
              </div>
            </div>
            <h3>No Little Ones Yet!</h3>
            <p>Add your children to enable quick check-in for Sunday School</p>
            <button 
              className="kc-empty-btn"
              onClick={() => setShowAddChild(true)}
              data-testid="add-first-child-btn"
            >
              <Plus className="w-5 h-5" />
              Add Your First Child
            </button>
          </motion.div>
        ) : (
          children.map((child, index) => {
            const checkedIn = isCheckedIn(child.id);
            const checkinInfo = getCheckinInfo(child.id);
            const avatarStyle = getAvatarStyle(child.name);
            
            return (
              <motion.div
                key={child.id}
                className={`kc-child-card ${checkedIn ? 'kc-checked-in' : ''}`}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                data-testid={`child-card-${child.id}`}
              >
                {checkedIn && (
                  <div className="kc-card-confetti">
                    <span>🎉</span>
                    <span>⭐</span>
                    <span>🎊</span>
                  </div>
                )}
                
                <div 
                  className="kc-child-avatar"
                  style={{ background: avatarStyle.bg }}
                >
                  <span className="kc-avatar-letter">{child.name.charAt(0).toUpperCase()}</span>
                  <span className="kc-avatar-emoji">{avatarStyle.emoji}</span>
                </div>
                
                <div className="kc-child-info">
                  <h3>{child.name}</h3>
                  <p className="kc-child-age">
                    <span className="kc-age-emoji">🎂</span>
                    {getAge(child.birthdate)} years old
                  </p>
                  {child.allergies && (
                    <div className="kc-allergy-tag">
                      <AlertCircle className="w-3 h-3" />
                      <span>{child.allergies}</span>
                    </div>
                  )}
                </div>
                
                {checkedIn ? (
                  <div className="kc-checked-status">
                    <div className="kc-status-badge">
                      <Check className="w-4 h-4" />
                      <span>Checked In!</span>
                    </div>
                    <div className="kc-pickup-code">
                      <span className="kc-code-label">Pickup Code</span>
                      <span className="kc-code-value">{checkinInfo?.pickup_code}</span>
                    </div>
                    <div className="kc-checkin-time">
                      <Clock className="w-3 h-3" />
                      {new Date(checkinInfo?.checked_in_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </div>
                  </div>
                ) : (
                  <motion.button
                    className="kc-checkin-btn"
                    onClick={() => checkInChild(child)}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    data-testid={`checkin-btn-${child.id}`}
                  >
                    <span className="kc-btn-icon">✓</span>
                    <span>Check In</span>
                  </motion.button>
                )}
              </motion.div>
            );
          })
        )}
      </div>

      {/* Active Check-ins Summary */}
      {checkins.filter(c => c.status === 'checked_in').length > 0 && (
        <motion.div 
          className="kc-summary"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="kc-summary-header">
            <span className="kc-summary-emoji">🎓</span>
            <h3>Currently in Sunday School</h3>
          </div>
          <p className="kc-summary-count">
            {checkins.filter(c => c.status === 'checked_in').length} {checkins.filter(c => c.status === 'checked_in').length === 1 ? 'child' : 'children'} having fun!
          </p>
          <div className="kc-summary-note">
            <Phone className="w-4 h-4" />
            <span>We'll text you if your child needs you during service</span>
          </div>
        </motion.div>
      )}

      {/* Success Celebration Modal */}
      <AnimatePresence>
        {showSuccess && (
          <motion.div
            className="kc-success-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowSuccess(null)}
          >
            <motion.div
              className="kc-success-modal"
              initial={{ scale: 0.5, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.5, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="kc-success-confetti">
                <span>🎉</span><span>🎊</span><span>⭐</span><span>🌟</span><span>✨</span>
              </div>
              <div className="kc-success-icon">
                <PartyPopper className="w-12 h-12" />
              </div>
              <h2>Yay! {showSuccess.child.name} is Checked In!</h2>
              <p>Have a wonderful time in Sunday School! 🌈</p>
              <div className="kc-success-code">
                <span className="kc-success-code-label">Your Pickup Code</span>
                <span className="kc-success-code-value">{showSuccess.pickup_code}</span>
              </div>
              <div className="kc-success-sms">
                <Phone className="w-4 h-4" />
                <span>SMS notification sent to your phone</span>
              </div>
              <button 
                className="kc-success-btn"
                onClick={() => setShowSuccess(null)}
              >
                Got it! 👍
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Add Child Modal */}
      <AnimatePresence>
        {showAddChild && (
          <motion.div
            className="kc-modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowAddChild(false)}
          >
            <motion.div
              className="kc-modal"
              initial={{ scale: 0.9, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.9, opacity: 0, y: 20 }}
              onClick={(e) => e.stopPropagation()}
            >
              <button className="kc-modal-close" onClick={() => setShowAddChild(false)}>
                <X className="w-5 h-5" />
              </button>
              
              <div className="kc-modal-header">
                <div className="kc-modal-icon">
                  <span>👶</span>
                </div>
                <h2>Add a Little One</h2>
                <p>Let's get your child ready for Sunday School!</p>
              </div>

              <div className="kc-modal-form">
                <div className="kc-form-group">
                  <label>
                    <span className="kc-label-emoji">📝</span>
                    Child's Name
                  </label>
                  <input
                    type="text"
                    value={newChild.name}
                    onChange={(e) => setNewChild({ ...newChild, name: e.target.value })}
                    placeholder="Enter your child's name"
                    data-testid="child-name-input"
                  />
                </div>

                <div className="kc-form-group">
                  <label>
                    <span className="kc-label-emoji">🎂</span>
                    Birthday
                  </label>
                  <input
                    type="date"
                    value={newChild.birthdate}
                    onChange={(e) => setNewChild({ ...newChild, birthdate: e.target.value })}
                    data-testid="child-birthdate-input"
                  />
                </div>

                <div className="kc-form-group">
                  <label>
                    <span className="kc-label-emoji">⚠️</span>
                    Any Allergies?
                  </label>
                  <input
                    type="text"
                    value={newChild.allergies}
                    onChange={(e) => setNewChild({ ...newChild, allergies: e.target.value })}
                    placeholder="e.g., Peanuts, Dairy (leave blank if none)"
                    data-testid="child-allergies-input"
                  />
                </div>

                <div className="kc-form-group">
                  <label>
                    <span className="kc-label-emoji">💝</span>
                    Special Needs / Notes
                  </label>
                  <textarea
                    value={newChild.special_needs}
                    onChange={(e) => setNewChild({ ...newChild, special_needs: e.target.value })}
                    placeholder="Any special accommodations we should know about?"
                    rows={2}
                  />
                </div>

                <div className="kc-form-divider">
                  <span>Emergency Contact</span>
                </div>

                <div className="kc-form-row">
                  <div className="kc-form-group">
                    <label>
                      <span className="kc-label-emoji">👤</span>
                      Contact Name
                    </label>
                    <input
                      type="text"
                      value={newChild.emergency_contact}
                      onChange={(e) => setNewChild({ ...newChild, emergency_contact: e.target.value })}
                      placeholder="Contact name"
                    />
                  </div>
                  <div className="kc-form-group">
                    <label>
                      <span className="kc-label-emoji">📞</span>
                      Phone Number
                    </label>
                    <input
                      type="tel"
                      value={newChild.emergency_phone}
                      onChange={(e) => setNewChild({ ...newChild, emergency_phone: e.target.value })}
                      placeholder="(555) 123-4567"
                    />
                  </div>
                </div>

                <button 
                  className="kc-modal-submit"
                  onClick={addChild}
                  data-testid="save-child-btn"
                >
                  <Heart className="w-5 h-5" />
                  <span>Add Child</span>
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
