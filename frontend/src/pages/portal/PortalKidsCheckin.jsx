import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Baby, Plus, Check, X, Clock, AlertCircle, Shield,
  Phone, User, Calendar, Heart, CheckCircle2, QrCode,
  MessageSquare, Edit2, Trash2
} from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

export default function PortalKidsCheckin() {
  const { user, tenant } = useOutletContext();
  const [children, setChildren] = useState([]);
  const [checkins, setCheckins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddChild, setShowAddChild] = useState(false);
  const [showCheckin, setShowCheckin] = useState(false);
  const [selectedChild, setSelectedChild] = useState(null);
  
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
        toast.success(
          <div className="flex flex-col gap-1">
            <strong>{child.name} checked in!</strong>
            <span className="text-sm">Pickup Code: <strong>{data.pickup_code}</strong></span>
            <span className="text-xs text-green-600">SMS sent to {user?.phone || 'your phone'}</span>
          </div>,
          { duration: 8000 }
        );
        setShowCheckin(false);
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
      <div className="kids-checkin-loading">
        <Baby className="w-12 h-12 animate-pulse" />
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div className="kids-checkin-page">
      {/* Header */}
      <div className="kids-checkin-header">
        <div className="kids-header-content">
          <div className="kids-header-icon">
            <Baby className="w-8 h-8" />
          </div>
          <div>
            <h1>Kids Check-in</h1>
            <p>Sunday School & Children's Ministry</p>
          </div>
        </div>
        <button 
          className="kids-add-btn"
          onClick={() => setShowAddChild(true)}
          data-testid="add-child-btn"
        >
          <Plus className="w-5 h-5" />
          Add Child
        </button>
      </div>

      {/* Quick Check-in Banner */}
      {children.length > 0 && (
        <div className="kids-quick-checkin">
          <div className="quick-checkin-info">
            <CheckCircle2 className="w-6 h-6" />
            <div>
              <h3>Ready to Check In?</h3>
              <p>Tap a child below to check them in for today's service</p>
            </div>
          </div>
        </div>
      )}

      {/* Children List */}
      <div className="kids-list">
        {children.length === 0 ? (
          <div className="kids-empty">
            <Baby className="w-16 h-16" />
            <h3>No Children Added Yet</h3>
            <p>Add your children to enable quick check-in for Sunday School</p>
            <button 
              className="kids-empty-btn"
              onClick={() => setShowAddChild(true)}
            >
              <Plus className="w-5 h-5" />
              Add Your First Child
            </button>
          </div>
        ) : (
          children.map((child) => {
            const checkedIn = isCheckedIn(child.id);
            const checkinInfo = getCheckinInfo(child.id);
            
            return (
              <motion.div
                key={child.id}
                className={`kids-card ${checkedIn ? 'checked-in' : ''}`}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                data-testid={`child-card-${child.id}`}
              >
                <div className="kids-card-avatar">
                  {child.name.charAt(0)}
                </div>
                <div className="kids-card-info">
                  <h3>{child.name}</h3>
                  <p>{getAge(child.birthdate)} years old</p>
                  {child.allergies && (
                    <span className="kids-allergy-badge">
                      <AlertCircle className="w-3 h-3" />
                      {child.allergies}
                    </span>
                  )}
                </div>
                
                {checkedIn ? (
                  <div className="kids-card-status">
                    <div className="kids-checked-in-badge">
                      <Check className="w-4 h-4" />
                      Checked In
                    </div>
                    <div className="kids-pickup-code">
                      <QrCode className="w-4 h-4" />
                      {checkinInfo?.pickup_code}
                    </div>
                    <span className="kids-checkin-time">
                      <Clock className="w-3 h-3" />
                      {new Date(checkinInfo?.checked_in_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                ) : (
                  <button
                    className="kids-checkin-btn"
                    onClick={() => checkInChild(child)}
                    data-testid={`checkin-btn-${child.id}`}
                  >
                    <Check className="w-5 h-5" />
                    Check In
                  </button>
                )}
              </motion.div>
            );
          })
        )}
      </div>

      {/* Active Check-ins Summary */}
      {checkins.length > 0 && (
        <div className="kids-active-summary">
          <h3>
            <Shield className="w-5 h-5" />
            Currently Checked In
          </h3>
          <p>{checkins.length} {checkins.length === 1 ? 'child' : 'children'} in Sunday School</p>
          <div className="kids-active-note">
            <MessageSquare className="w-4 h-4" />
            You'll receive a text if your child needs you during service
          </div>
        </div>
      )}

      {/* Add Child Modal */}
      <AnimatePresence>
        {showAddChild && (
          <motion.div
            className="kids-modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowAddChild(false)}
          >
            <motion.div
              className="kids-modal"
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <button className="kids-modal-close" onClick={() => setShowAddChild(false)}>
                <X className="w-5 h-5" />
              </button>
              
              <div className="kids-modal-header">
                <Baby className="w-8 h-8" />
                <h2>Add a Child</h2>
              </div>

              <div className="kids-modal-form">
                <div className="kids-form-group">
                  <label>Child's Name *</label>
                  <input
                    type="text"
                    value={newChild.name}
                    onChange={(e) => setNewChild({ ...newChild, name: e.target.value })}
                    placeholder="Enter child's full name"
                    data-testid="child-name-input"
                  />
                </div>

                <div className="kids-form-group">
                  <label>Birthdate *</label>
                  <input
                    type="date"
                    value={newChild.birthdate}
                    onChange={(e) => setNewChild({ ...newChild, birthdate: e.target.value })}
                    data-testid="child-birthdate-input"
                  />
                </div>

                <div className="kids-form-group">
                  <label>Allergies</label>
                  <input
                    type="text"
                    value={newChild.allergies}
                    onChange={(e) => setNewChild({ ...newChild, allergies: e.target.value })}
                    placeholder="e.g., Peanuts, Dairy"
                    data-testid="child-allergies-input"
                  />
                </div>

                <div className="kids-form-group">
                  <label>Special Needs / Notes</label>
                  <textarea
                    value={newChild.special_needs}
                    onChange={(e) => setNewChild({ ...newChild, special_needs: e.target.value })}
                    placeholder="Any special accommodations needed?"
                    rows={2}
                  />
                </div>

                <div className="kids-form-row">
                  <div className="kids-form-group">
                    <label>Emergency Contact</label>
                    <input
                      type="text"
                      value={newChild.emergency_contact}
                      onChange={(e) => setNewChild({ ...newChild, emergency_contact: e.target.value })}
                      placeholder="Contact name"
                    />
                  </div>
                  <div className="kids-form-group">
                    <label>Emergency Phone</label>
                    <input
                      type="tel"
                      value={newChild.emergency_phone}
                      onChange={(e) => setNewChild({ ...newChild, emergency_phone: e.target.value })}
                      placeholder="(555) 123-4567"
                    />
                  </div>
                </div>

                <button 
                  className="kids-modal-submit"
                  onClick={addChild}
                  data-testid="save-child-btn"
                >
                  <Plus className="w-5 h-5" />
                  Add Child
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
