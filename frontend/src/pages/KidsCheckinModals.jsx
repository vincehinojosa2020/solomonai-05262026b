import { motion } from 'framer-motion';
import {
  CheckCircle2, Phone, User, Users, UserCheck,
  AlertCircle, Sparkles,
} from 'lucide-react';
import { getAvatarStyle, formatAge } from './KidsCheckinUtils';

/**
 * Checkout Confirmation Modal
 */
export const CheckoutConfirmModal = ({ checkin, onClose, onCheckout }) => {
  if (!checkin) return null;
  return (
    <motion.div
      className="kca-modal-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        className="kca-modal"
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="kca-modal-icon">
          <span style={{ fontSize: 32 }}>🎉</span>
        </div>
        <h2>Check Out {checkin.child?.name}?</h2>
        <p>Pickup Code: <strong>{checkin.pickup_code}</strong></p>
        <p className="kca-modal-warning">
          Please verify the parent's identity before releasing the child
        </p>

        <div className="kca-modal-parent">
          <User className="w-4 h-4" />
          <span>{checkin.child?.parent_name}</span>
          {checkin.child?.parent_phone && (
            <>
              <Phone className="w-4 h-4" />
              <span>{checkin.child.parent_phone}</span>
            </>
          )}
        </div>

        <div className="kca-modal-actions">
          <button className="kca-modal-cancel" onClick={onClose}>Cancel</button>
          <button
            className="kca-modal-confirm"
            onClick={() => onCheckout(checkin.id)}
            data-testid="confirm-checkout-btn"
          >
            <CheckCircle2 className="w-5 h-5" />
            Confirm Checkout
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
};

/**
 * Manual Check-In Modal
 */
export const ManualCheckinModal = ({
  allKids, checkins, manualSearch, setManualSearch,
  manualClassroom, setManualClassroom,
  onClose, onCheckin,
}) => {
  const filtered = allKids.filter(kid =>
    !checkins.some(c => c.child_id === kid.id) &&
    (kid.name?.toLowerCase().includes(manualSearch.toLowerCase()) ||
     kid.parent_name?.toLowerCase().includes(manualSearch.toLowerCase()))
  );

  return (
    <motion.div
      className="kca-modal-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        className="kca-modal kca-register-modal"
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
        data-testid="manual-checkin-modal"
      >
        <div className="kca-modal-icon" style={{ background: '#eff6ff' }}>
          <UserCheck className="w-10 h-10" style={{ color: '#3b82f6' }} />
        </div>
        <h2>Manual Check-In</h2>
        <p className="kca-modal-subtitle">Search for a child and check them in directly</p>

        <div style={{ marginTop: 16 }}>
          <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
            <input
              type="text"
              placeholder="Search child or parent name..."
              value={manualSearch}
              onChange={(e) => setManualSearch(e.target.value)}
              style={{ flex: 1, padding: '10px 14px', borderRadius: 10, border: '2px solid #e2e8f0', fontSize: 14 }}
              data-testid="manual-checkin-search"
            />
            <select
              value={manualClassroom}
              onChange={(e) => setManualClassroom(e.target.value)}
              style={{ padding: '10px 14px', borderRadius: 10, border: '2px solid #e2e8f0', fontSize: 14 }}
              data-testid="manual-checkin-classroom"
            >
              <option>Sunday School</option>
              <option>Nursery</option>
              <option>Preschool</option>
              <option>Elementary</option>
              <option>Youth Room</option>
            </select>
          </div>

          <div style={{ maxHeight: 300, overflowY: 'auto' }}>
            {filtered.map(kid => {
              const avatarStyle = getAvatarStyle(kid.name);
              return (
                <div key={kid.id} style={{
                  display: 'flex', alignItems: 'center', gap: 12, padding: '10px 12px',
                  borderRadius: 10, border: '1px solid #e2e8f0', marginBottom: 8,
                  background: '#f8fafc'
                }} data-testid={`manual-kid-${kid.id}`}>
                  <div style={{
                    width: 40, height: 40, borderRadius: '50%', display: 'flex',
                    alignItems: 'center', justifyContent: 'center', color: 'white',
                    fontWeight: 700, fontSize: 16, background: avatarStyle.bg
                  }}>
                    {kid.name?.charAt(0)}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600, fontSize: 14, color: '#1e293b' }}>{kid.name}</div>
                    <div style={{ fontSize: 12, color: '#64748b' }}>{kid.parent_name} &middot; {formatAge(kid.birthdate)}</div>
                  </div>
                  <button
                    onClick={() => onCheckin(kid)}
                    style={{
                      padding: '8px 16px', background: '#3b82f6', color: 'white',
                      border: 'none', borderRadius: 8, fontSize: 13, fontWeight: 600,
                      cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6
                    }}
                    data-testid={`manual-checkin-kid-${kid.id}`}
                  >
                    <UserCheck style={{ width: 16, height: 16 }} />
                    Check In
                  </button>
                </div>
              );
            })}
            {filtered.length === 0 && (
              <div style={{ textAlign: 'center', padding: 24, color: '#94a3b8' }}>
                No available children found
              </div>
            )}
          </div>
        </div>

        <div className="kca-modal-actions" style={{ marginTop: 16 }}>
          <button className="kca-modal-cancel" onClick={onClose}>Close</button>
        </div>
      </motion.div>
    </motion.div>
  );
};

/**
 * Register Family Modal
 */
export const RegisterFamilyModal = ({ newFamily, setNewFamily, onClose, onRegister }) => (
  <motion.div
    className="kca-modal-overlay"
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    exit={{ opacity: 0 }}
    onClick={onClose}
  >
    <motion.div
      className="kca-modal kca-register-modal"
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      exit={{ scale: 0.9, opacity: 0 }}
      onClick={(e) => e.stopPropagation()}
      data-testid="register-family-modal"
    >
      <div className="kca-modal-icon kca-modal-icon-green">
        <Users className="w-10 h-10" />
      </div>
      <h2>Register New Family</h2>
      <p className="kca-modal-subtitle">Welcome a new family to Sunday School!</p>

      <div className="kca-register-form">
        <div className="kca-form-section">
          <h3><User className="w-4 h-4" /> Parent Information</h3>
          <div className="kca-form-row">
            <input
              type="text"
              placeholder="Parent Name *"
              value={newFamily.parentName}
              onChange={(e) => setNewFamily(prev => ({ ...prev, parentName: e.target.value }))}
              data-testid="parent-name-input"
            />
            <input
              type="email"
              placeholder="Email *"
              value={newFamily.parentEmail}
              onChange={(e) => setNewFamily(prev => ({ ...prev, parentEmail: e.target.value }))}
              data-testid="parent-email-input"
            />
          </div>
          <input
            type="tel"
            placeholder="Phone Number"
            value={newFamily.parentPhone}
            onChange={(e) => setNewFamily(prev => ({ ...prev, parentPhone: e.target.value }))}
            data-testid="parent-phone-input"
          />
        </div>

        <div className="kca-form-section">
          <h3><Sparkles className="w-4 h-4" /> Child Information</h3>
          <div className="kca-form-row">
            <input
              type="text"
              placeholder="Child Name *"
              value={newFamily.childName}
              onChange={(e) => setNewFamily(prev => ({ ...prev, childName: e.target.value }))}
              data-testid="child-name-input"
            />
            <input
              type="date"
              placeholder="Birthdate"
              value={newFamily.childBirthdate}
              onChange={(e) => setNewFamily(prev => ({ ...prev, childBirthdate: e.target.value }))}
              data-testid="child-birthdate-input"
            />
          </div>
          <input
            type="text"
            placeholder="Allergies (if any)"
            value={newFamily.childAllergies}
            onChange={(e) => setNewFamily(prev => ({ ...prev, childAllergies: e.target.value }))}
          />
          <textarea
            placeholder="Special notes (e.g., special needs, preferences)"
            value={newFamily.childNotes}
            onChange={(e) => setNewFamily(prev => ({ ...prev, childNotes: e.target.value }))}
            rows={2}
          />
        </div>
      </div>

      <div className="kca-modal-actions">
        <button className="kca-modal-cancel" onClick={onClose}>Cancel</button>
        <button
          className="kca-modal-confirm kca-modal-confirm-green"
          onClick={onRegister}
          data-testid="submit-register-btn"
        >
          <CheckCircle2 className="w-5 h-5" />
          Register Family
        </button>
      </div>
    </motion.div>
  </motion.div>
);
