import { motion } from 'framer-motion';
import { Search, UserCheck, AlertCircle } from 'lucide-react';
import { getAvatarStyle, formatAge } from '../KidsCheckinUtils';

export function CheckInTab({ searchTerm, setSearchTerm, availableForCheckin, onDirectCheckin }) {
  return (
    <motion.div
      key="checkin"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
    >
      <div className="kca-search-box" role="search">
        <Search className="w-5 h-5" aria-hidden="true" />
        <input
          type="text"
          placeholder="Search by child or parent name..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          data-testid="search-kids-input"
          aria-label="Search children"
        />
      </div>
      <div className="kca-kids-list" role="list" aria-label="Children available for check-in">
        {availableForCheckin.length === 0 ? (
          <div className="kca-empty">
            <span className="kca-empty-emoji" aria-hidden="true">&#x2705;</span>
            <h3>All Registered Kids Are Checked In!</h3>
            <p>Or no kids match your search criteria</p>
          </div>
        ) : (
          availableForCheckin.map((kid) => {
            const avatarStyle = getAvatarStyle(kid.name);
            return (
              <div key={kid.id} className="kca-kid-row" data-testid={`kid-row-${kid.id}`} role="listitem">
                <div className="kca-kid-avatar" style={{ background: avatarStyle.bg }}>
                  {kid.name.charAt(0)}
                </div>
                <div className="kca-kid-info">
                  <h4>{kid.name}</h4>
                  <div className="kca-kid-details">
                    <span aria-hidden="true">&#x1F382;</span><span> {formatAge(kid.birthdate)}</span>
                    <span> &#x2022; {kid.parent_name}</span>
                    {kid.allergies && (
                      <span className="kca-allergy-small">
                        <AlertCircle className="w-3 h-3" />
                        {kid.allergies}
                      </span>
                    )}
                  </div>
                </div>
                <button
                  className="kca-checkin-btn"
                  onClick={() => onDirectCheckin(kid)}
                  data-testid={`direct-checkin-btn-${kid.id}`}
                  aria-label={`Check in ${kid.name}`}
                >
                  <UserCheck className="w-4 h-4" />
                  Check In
                </button>
              </div>
            );
          })
        )}
      </div>
    </motion.div>
  );
}
