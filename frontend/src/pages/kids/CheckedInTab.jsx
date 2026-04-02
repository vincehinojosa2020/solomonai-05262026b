import { Search, CheckCircle2, Shield, Clock, AlertCircle, Phone, User } from 'lucide-react';
import { getAvatarStyle, formatAge } from './constants';

export function CheckedInTab({ checkins, searchTerm, setSearchTerm, onCheckout }) {
  const filtered = checkins.filter(c =>
    !searchTerm || c.child_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.parent_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.security_code?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="kca-tab-content" data-testid="checked-in-tab">
      <div className="kca-search-bar">
        <Search className="kca-search-icon" />
        <input type="text" placeholder="Search by child name, parent, or code..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} className="kca-search-input" data-testid="checkin-search" />
        <span className="kca-count-badge">{filtered.length} checked in</span>
      </div>

      {filtered.length === 0 ? (
        <div className="kca-empty">
          <CheckCircle2 className="kca-empty-icon" />
          <p>No children currently checked in</p>
        </div>
      ) : (
        <div className="kca-grid">
          {filtered.map(c => {
            const avatar = getAvatarStyle(c.child_name);
            return (
              <div key={c.id} className="kca-card" data-testid={`checkin-card-${c.id}`}>
                <div className="kca-card-header">
                  <div className="kca-avatar" style={{ background: avatar.bg }}><span className="kca-avatar-emoji">{avatar.emoji}</span></div>
                  <div className="kca-card-info">
                    <h3 className="kca-child-name">{c.child_name}</h3>
                    <p className="kca-age">{formatAge(c.child_birthdate)}</p>
                  </div>
                  <div className="kca-security-code" data-testid={`security-code-${c.id}`}>
                    <Shield className="w-3 h-3" />{c.security_code}
                  </div>
                </div>
                <div className="kca-card-details">
                  <div className="kca-detail"><Clock className="w-3.5 h-3.5" />{new Date(c.checked_in_at).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}</div>
                  <div className="kca-detail"><User className="w-3.5 h-3.5" />{c.parent_name}</div>
                  {c.parent_phone && <div className="kca-detail"><Phone className="w-3.5 h-3.5" />{c.parent_phone}</div>}
                  <div className="kca-detail kca-classroom">{c.classroom || 'Sunday School'}</div>
                  {c.allergies && <div className="kca-detail kca-allergy"><AlertCircle className="w-3.5 h-3.5" />{c.allergies}</div>}
                </div>
                <button onClick={() => onCheckout(c)} className="kca-checkout-btn" data-testid={`checkout-btn-${c.id}`}>Check Out</button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
