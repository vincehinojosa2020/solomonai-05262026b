import { useState, useEffect, useCallback } from 'react';
import { useOutletContext } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { usePolling } from '@/hooks/usePolling';
import { 
  Plus, Check, X, Clock, AlertCircle,
  Phone, Heart, Sparkles, Star, Cross
} from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

// Colorful Bible-themed avatar styles (warm, vibrant colors - no rainbow)
const AVATAR_COLORS = [
  { bg: 'linear-gradient(135deg, #E11D48 0%, #F43F5E 100%)', emoji: '🦁', character: 'Daniel' },      // Rose/Red - Daniel & Lions
  { bg: 'linear-gradient(135deg, #7C3AED 0%, #A78BFA 100%)', emoji: '🐑', character: 'David' },       // Purple - David the Shepherd
  { bg: 'linear-gradient(135deg, #0891B2 0%, #22D3EE 100%)', emoji: '🌊', character: 'Moses' },       // Cyan - Moses & Red Sea
  { bg: 'linear-gradient(135deg, #EA580C 0%, #FB923C 100%)', emoji: '⭐', character: 'Abraham' },     // Orange - Stars of Abraham
  { bg: 'linear-gradient(135deg, #059669 0%, #34D399 100%)', emoji: '🕊️', character: 'Noah' },       // Emerald - Noah's Dove
  { bg: 'linear-gradient(135deg, #2563EB 0%, #60A5FA 100%)', emoji: '🐋', character: 'Jonah' },       // Blue - Jonah & Whale
  { bg: 'linear-gradient(135deg, #DB2777 0%, #F472B6 100%)', emoji: '👑', character: 'Esther' },      // Pink - Queen Esther
  { bg: 'linear-gradient(135deg, #CA8A04 0%, #FACC15 100%)', emoji: '💪', character: 'Samson' },      // Gold - Samson
];

// Get consistent style for a child based on their name
const getAvatarStyle = (name) => {
  const index = name.charCodeAt(0) % AVATAR_COLORS.length;
  return AVATAR_COLORS[index];
};

// Calculate age - works for any age
const getAge = (birthdate) => {
  if (!birthdate) return null;
  const today = new Date();
  const birth = new Date(birthdate);
  let age = today.getFullYear() - birth.getFullYear();
  const monthDiff = today.getMonth() - birth.getMonth();
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
    age--;
  }
  return age;
};

// Format age display
const formatAge = (birthdate) => {
  const age = getAge(birthdate);
  if (age === null) return 'Age not set';
  if (age === 0) return 'Under 1 year';
  if (age === 1) return '1 year old';
  return `${age} years old`;
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
    first_name: '',
    last_name: '',
    name: '',
    birthdate: '',
    grade: 'PreK',
    classroom: 'Sunday School Adventures',
    allergies: '',
    special_needs: '',
    emergency_contact: '',
    emergency_phone: ''
  });

  useEffect(() => {
    fetchData();
  }, []);

  // Real-time polling every 15 seconds for kids check-in status
  usePolling(useCallback(() => fetchData(), []), 15000);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Fetch children
      const childRes = await fetch(`${API_URL}/portal/kids`);
      if (childRes.ok) {
        const childData = await childRes.json();
        setChildren(childData.children || []);
      }
      
      // Fetch active checkins
      const checkinRes = await fetch(`${API_URL}/portal/kids/checkins/active`);
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
    const childName = newChild.first_name && newChild.last_name 
      ? `${newChild.first_name} ${newChild.last_name}` 
      : newChild.name;
    
    if (!childName || !newChild.birthdate) {
      toast.error('Please enter child name and birthdate');
      return;
    }

    try {
      const payload = { 
        ...newChild, 
        name: childName,
        first_name: newChild.first_name,
        last_name: newChild.last_name
      };
      const res = await fetch(`${API_URL}/portal/kids`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        toast.success(`${childName} added! Ready to check in.`);
        setShowAddChild(false);
        setNewChild({ first_name: '', last_name: '', name: '', birthdate: '', grade: 'PreK', classroom: 'Sunday School Adventures', allergies: '', special_needs: '', emergency_contact: '', emergency_phone: '' });
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
      const idempotencyKey = crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`;
      const res = await fetch(`${API_URL}/portal/kids/${child.id}/checkin`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-Idempotency-Key': idempotencyKey
        },
        body: JSON.stringify({ classroom: 'Sunday School' })
      });

      if (res.ok) {
        const data = await res.json();
        setShowSuccess({ child, pickup_code: data.pickup_code, nudge: data.nudge });
        // Request screen wake lock so QR stays visible
        try {
          if ('wakeLock' in navigator) {
            await navigator.wakeLock.request('screen');
          }
        } catch (e) { /* wake lock not supported */ }
        fetchData();
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || 'Check-in failed');
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
          <Cross className="kc-spin-icon" />
        </div>
        <p>Preparing for Sunday School...</p>
      </div>
    );
  }

  return (
    <div className="kc-page" data-testid="kids-checkin-page">
      {/* Floating decorations - Christian & Bible themes */}
      <div className="kc-decorations">
        <span className="kc-deco kc-deco-1">✝️</span>
        <span className="kc-deco kc-deco-2">⭐</span>
        <span className="kc-deco kc-deco-3">🕊️</span>
        <span className="kc-deco kc-deco-4">📖</span>
        <span className="kc-deco kc-deco-5">💜</span>
      </div>

      {/* Header */}
      <div className="kc-header">
        <div className="kc-header-bg">
          <div className="kc-header-wave"></div>
        </div>
        <div className="kc-header-content">
          <div className="kc-header-icon">
            <span className="kc-header-emoji">✝️</span>
            <Sparkles className="kc-sparkle kc-sparkle-1" />
            <Sparkles className="kc-sparkle kc-sparkle-2" />
          </div>
          <div className="kc-header-text">
            <h1>Kids Check-in</h1>
            <p>Sunday School Adventures! 📖</p>
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
            <Star className="w-8 h-8" />
          </div>
          <div className="kc-ready-text">
            <h3>Ready to Learn About Bible Heroes? 📖</h3>
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
              <span className="kc-empty-emoji">✝️</span>
              <div className="kc-empty-stars">
                <Star className="kc-star kc-star-1" />
                <Star className="kc-star kc-star-2" />
                <Star className="kc-star kc-star-3" />
              </div>
            </div>
            <h3>No Children Yet!</h3>
            <p>Add your children of any age for Sunday School check-in</p>
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
                    <span>✝️</span>
                    <span>⭐</span>
                    <span>🕊️</span>
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
                    {formatAge(child.birthdate)}
                  </p>
                  <p className="kc-bible-character">
                    <span>📖</span> Like {avatarStyle.character}
                  </p>
                  {child.allergies && (
                    <div className="kc-allergy-tag">
                      <AlertCircle className="w-3 h-3" />
                      <span>{child.allergies}</span>
                    </div>
                  )}
                </div>
                
                {checkedIn ? (
                  <div className="kc-checked-status" data-testid={`checked-in-status-${child.id}`}>
                    <div className="kc-status-badge">
                      <Check className="w-4 h-4" />
                      <span>Checked In!</span>
                    </div>
                    <div className="kc-qr-inline" data-testid={`qr-code-${child.id}`} style={{margin:'16px auto', background:'white', padding: 16, borderRadius: 16, display:'inline-block', boxShadow:'0 2px 12px rgba(0,0,0,0.1)'}}>
                      <QRCodeSVG 
                        value={`SOLOMON_PICKUP_${child.id}_${checkinInfo?.pickup_code}_${new Date().toISOString().split('T')[0]}`}
                        size={200}
                        level="M"
                        bgColor="#ffffff"
                        fgColor="#1f2937"
                      />
                    </div>
                    <div className="kc-pickup-code">
                      <span className="kc-code-label">Security Code</span>
                      <span className="kc-code-value" style={{fontSize: 48, letterSpacing: 8, fontFamily: 'monospace', fontWeight: 700}}>{checkinInfo?.pickup_code}</span>
                    </div>
                    <p style={{fontSize: 13, color:'#64748b', marginTop: 4}}>Show this to pick up your child at checkout</p>
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
            <span className="kc-summary-emoji">✝️</span>
            <h3>Currently in Sunday School</h3>
          </div>
          <p className="kc-summary-count">
            {checkins.filter(c => c.status === 'checked_in').length} {checkins.filter(c => c.status === 'checked_in').length === 1 ? 'child' : 'children'} learning God's Word!
          </p>
          <div className="kc-summary-note">
            <Phone className="w-4 h-4" />
            <span>We'll text you if your child needs you during service</span>
          </div>
        </motion.div>
      )}

      {/* Success Celebration Modal with QR Code */}
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
                <span>✝️</span><span>⭐</span><span>🕊️</span><span>📖</span><span>✨</span>
              </div>
              <div className="kc-success-icon">
                <Check className="w-12 h-12" />
              </div>
              <h2>{showSuccess.child.name} is safe!</h2>
              <p className="kc-success-subtitle">Ready for the best hour of their week!</p>
              
              {/* QR Code Display — 200px for bright sunlight readability */}
              <div className="kc-success-qr" data-testid="checkin-qr-code" style={{padding: 16, background: 'white', borderRadius: 16, display: 'inline-block', margin: '12px auto'}}>
                <QRCodeSVG 
                  value={`SOLOMON_PICKUP_${showSuccess.child.id}_${showSuccess.pickup_code}_${new Date().toISOString().split('T')[0]}`}
                  size={200}
                  level="M"
                  bgColor="#ffffff"
                  fgColor="#1f2937"
                />
              </div>
              
              <div className="kc-success-code">
                <span className="kc-success-code-label">Security Code</span>
                <span className="kc-success-code-value" data-testid="pickup-code-display" style={{fontSize: 48, letterSpacing: 8, fontFamily: 'monospace', fontWeight: 700}}>{showSuccess.pickup_code}</span>
              </div>
              
              <div className="kc-success-instructions">
                <p>Show this QR code or give the 3-digit code at pickup</p>
              </div>
              
              {/* Giving Nudge — warm, not a popup */}
              {showSuccess.nudge?.show_giving && (
                <div className="kc-giving-nudge" data-testid="giving-nudge" style={{background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 16, padding: '16px 20px', margin: '16px 0 8px', textAlign: 'center'}}>
                  <p style={{fontSize: 15, color: '#166534', marginBottom: 12, fontWeight: 500}}>The kids are in — support your church today?</p>
                  <div style={{display: 'flex', gap: 8, justifyContent: 'center', flexWrap: 'wrap'}}>
                    {(showSuccess.nudge.give_amounts || [10, 25, 50, 100]).map(amt => (
                      <button key={amt} onClick={(e) => { e.stopPropagation(); window.location.href = `/portal/give?amount=${amt}`; }}
                        style={{padding: '10px 18px', borderRadius: 10, background: '#22c55e', color: 'white', border: 'none', fontWeight: 600, fontSize: 15, cursor: 'pointer', minWidth: 60}}
                        data-testid={`give-nudge-${amt}`}
                      >${amt}</button>
                    ))}
                    <button onClick={(e) => { e.stopPropagation(); setShowSuccess(null); }}
                      style={{padding: '10px 18px', borderRadius: 10, background: 'white', color: '#64748b', border: '1px solid #e2e8f0', fontWeight: 500, fontSize: 15, cursor: 'pointer'}}
                      data-testid="give-nudge-not-today"
                    >Not today</button>
                  </div>
                </div>
              )}
              
              <button 
                className="kc-success-btn"
                onClick={() => setShowSuccess(null)}
                data-testid="checkin-done-btn"
              >
                Done
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
                  <span>✝️</span>
                </div>
                <h2>Add a Child</h2>
                <p>Register for Sunday School (any age welcome!)</p>
              </div>

              <div className="kc-modal-form">
                <div className="kc-form-row">
                  <div className="kc-form-group">
                    <label>
                      <span className="kc-label-emoji">📝</span>
                      First Name *
                    </label>
                    <input
                      type="text"
                      value={newChild.first_name}
                      onChange={(e) => setNewChild({ ...newChild, first_name: e.target.value })}
                      placeholder="First name"
                      data-testid="child-first-name-input"
                      style={{fontSize: 16}}
                    />
                  </div>
                  <div className="kc-form-group">
                    <label>
                      <span className="kc-label-emoji">📝</span>
                      Last Name *
                    </label>
                    <input
                      type="text"
                      value={newChild.last_name}
                      onChange={(e) => setNewChild({ ...newChild, last_name: e.target.value })}
                      placeholder="Last name"
                      data-testid="child-last-name-input"
                      style={{fontSize: 16}}
                    />
                  </div>
                </div>

                <div className="kc-form-group">
                  <label>
                    <span className="kc-label-emoji">🎂</span>
                    Date of Birth *
                  </label>
                  <input
                    type="date"
                    value={newChild.birthdate}
                    onChange={(e) => setNewChild({ ...newChild, birthdate: e.target.value })}
                    data-testid="child-birthdate-input"
                    style={{fontSize: 16}}
                  />
                </div>

                <div className="kc-form-group">
                  <label>
                    <span className="kc-label-emoji">🎒</span>
                    Grade / Class
                  </label>
                  <select
                    value={newChild.grade}
                    onChange={(e) => setNewChild({ ...newChild, grade: e.target.value })}
                    data-testid="child-grade-select"
                    style={{fontSize: 16, padding: '10px 12px', borderRadius: 8, border: '1px solid #e2e8f0', width: '100%'}}
                  >
                    <option value="PreK">PreK</option>
                    <option value="Kindergarten">Kindergarten</option>
                    <option value="1st">1st Grade</option>
                    <option value="2nd">2nd Grade</option>
                    <option value="3rd">3rd Grade</option>
                    <option value="4th">4th Grade</option>
                    <option value="5th">5th Grade</option>
                  </select>
                </div>

                <div className="kc-form-group">
                  <label>
                    <span className="kc-label-emoji">⚠️</span>
                    Allergies or Special Notes
                  </label>
                  <input
                    type="text"
                    value={newChild.allergies}
                    onChange={(e) => setNewChild({ ...newChild, allergies: e.target.value })}
                    placeholder="e.g., Peanuts, Dairy (leave blank if none)"
                    data-testid="child-allergies-input"
                    style={{fontSize: 16}}
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
                      style={{fontSize: 16}}
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
                      style={{fontSize: 16}}
                    />
                  </div>
                </div>

                <button 
                  className="kc-modal-submit"
                  onClick={addChild}
                  data-testid="save-child-btn"
                >
                  <Heart className="w-5 h-5" />
                  <span>Add Child to My Account</span>
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
