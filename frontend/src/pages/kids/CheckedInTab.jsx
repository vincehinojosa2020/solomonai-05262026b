import { motion } from 'framer-motion';
import { CheckCircle2, AlertCircle, Clock, User, UserX } from 'lucide-react';
import { getAvatarStyle, formatAge } from '../KidsCheckinUtils';

export function CheckedInTab({ enrichedCheckins, onCheckout }) {
  return (
    <motion.div
      key="checkedin"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="kca-checkedin-grid"
    >
      {enrichedCheckins.length === 0 ? (
        <div className="kca-empty">
          <span className="kca-empty-emoji" aria-hidden="true">&#x1F3E0;</span>
          <h3>No Children Checked In</h3>
          <p>Check in children using the "Check In" tab</p>
        </div>
      ) : (
        enrichedCheckins.map((checkin) => {
          const avatarStyle = getAvatarStyle(checkin.child?.name || 'A');
          return (
            <motion.div
              key={checkin.id}
              className="kca-child-card"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              data-testid={`checked-in-card-${checkin.id}`}
            >
              <div className="kca-card-status">
                <CheckCircle2 className="w-4 h-4" />
                <span>Checked In</span>
              </div>
              <div className="kca-card-avatar" style={{ background: avatarStyle.bg }}>
                <span className="kca-avatar-letter">{checkin.child?.name?.charAt(0) || '?'}</span>
                <span className="kca-avatar-emoji" aria-hidden="true">{avatarStyle.emoji}</span>
              </div>
              <h3>{checkin.child?.name || 'Unknown'}</h3>
              <p className="kca-card-age">
                <span aria-hidden="true">&#x1F382;</span> {formatAge(checkin.child?.birthdate)}
              </p>
              {checkin.child?.allergies && (
                <div className="kca-allergy-badge" role="alert">
                  <AlertCircle className="w-3 h-3" />
                  {checkin.child.allergies}
                </div>
              )}
              <div className="kca-pickup-code">
                <span className="kca-code-label">Pickup Code</span>
                <span className="kca-code-value">{checkin.pickup_code}</span>
              </div>
              <div className="kca-card-meta">
                <div className="kca-meta-item">
                  <Clock className="w-3 h-3" />
                  {new Date(checkin.checked_in_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
                <div className="kca-meta-item">
                  <User className="w-3 h-3" />
                  {checkin.child?.parent_name || 'Unknown'}
                </div>
              </div>
              <button
                className="kca-checkout-btn"
                onClick={() => onCheckout(checkin)}
                data-testid={`checkout-btn-${checkin.id}`}
                aria-label={`Check out ${checkin.child?.name || 'child'}`}
              >
                <UserX className="w-4 h-4" />
                Check Out
              </button>
            </motion.div>
          );
        })
      )}
    </motion.div>
  );
}
