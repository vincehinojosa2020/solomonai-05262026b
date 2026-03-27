import { useState, useEffect, useCallback } from 'react';
import { usePolling } from '@/hooks/usePolling';
import {
  Calendar, Check, X, Clock, MapPin, AlertTriangle, ChevronDown,
  Filter, CheckCircle, XCircle, Loader2, Users, ArrowRight
} from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from '@/components/ui/dialog';

const STATUS_STYLES = {
  pending: { bg: '#fef3c7', text: '#92400e', icon: Clock, label: 'Pending' },
  approved: { bg: '#dcfce7', text: '#166534', icon: CheckCircle, label: 'Approved' },
  rejected: { bg: '#fee2e2', text: '#991b1b', icon: XCircle, label: 'Rejected' },
};

export default function CalendarApprovals() {
  const [bookings, setBookings] = useState([]);
  const [counts, setCounts] = useState({ pending: 0, approved: 0, rejected: 0 });
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('pending');
  const [selectedIds, setSelectedIds] = useState([]);
  const [showNewRequest, setShowNewRequest] = useState(false);
  const [rooms, setRooms] = useState([]);
  const [conflicts, setConflicts] = useState([]);
  const [showConflicts, setShowConflicts] = useState(false);
  const [processing, setProcessing] = useState(null);
  const [newBooking, setNewBooking] = useState({
    event_name: '', description: '', event_date: '', start_time: '', end_time: '',
    room_id: '', room_name: '', notes: ''
  });

  const fetchBookings = useCallback(async () => {
    try {
      const params = filter !== 'all' ? `?status=${filter}` : '';
      const res = await fetch(`${API_URL}/admin/calendar/approvals${params}`);
      if (res.ok) {
        const data = await res.json();
        setBookings(data.bookings || []);
        setCounts(data.counts || {});
      }
    } catch { toast.error('Failed to load approvals'); }
    finally { setLoading(false); }
  }, [filter]);

  const fetchRooms = async () => {
    try {
      const res = await fetch(`${API_URL}/admin/calendar/rooms`);
      if (res.ok) { const d = await res.json(); setRooms(d.rooms || []); }
    } catch {}
  };

  const fetchConflicts = async () => {
    try {
      const res = await fetch(`${API_URL}/admin/calendar/conflicts`);
      if (res.ok) { const d = await res.json(); setConflicts(d.conflicts || []); }
    } catch {}
  };

  useEffect(() => { fetchBookings(); fetchRooms(); }, [filter, fetchBookings]);
  usePolling(fetchBookings, 15000);

  const handleDecision = async (bookingId, decision) => {
    setProcessing(bookingId);
    try {
      const res = await fetch(`${API_URL}/admin/calendar/approvals/${bookingId}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision })
      });
      if (res.ok) {
        toast.success(`Booking ${decision}`);
        fetchBookings();
      }
    } catch { toast.error('Failed to process'); }
    finally { setProcessing(null); }
  };

  const handleBulkDecision = async (decision) => {
    if (selectedIds.length === 0) return;
    try {
      const res = await fetch(`${API_URL}/admin/calendar/approvals/bulk`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ booking_ids: selectedIds, decision })
      });
      if (res.ok) {
        const d = await res.json();
        toast.success(`${d.updated} bookings ${decision}`);
        setSelectedIds([]);
        fetchBookings();
      }
    } catch { toast.error('Bulk action failed'); }
  };

  const handleCreateBooking = async () => {
    if (!newBooking.event_name || !newBooking.event_date || !newBooking.room_id) {
      toast.error('Name, date, and room are required');
      return;
    }
    const room = rooms.find(r => r.id === newBooking.room_id);
    try {
      const res = await fetch(`${API_URL}/admin/calendar/booking-requests`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...newBooking, room_name: room?.name || '' })
      });
      if (res.ok) {
        const d = await res.json();
        toast.success(d.message);
        setShowNewRequest(false);
        setNewBooking({ event_name: '', description: '', event_date: '', start_time: '', end_time: '', room_id: '', room_name: '', notes: '' });
        fetchBookings();
      }
    } catch { toast.error('Failed to create request'); }
  };

  const toggleSelect = (id) => {
    setSelectedIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };

  const pendingBookings = bookings.filter(b => b.status === 'pending');

  return (
    <div className="page-container" data-testid="calendar-approvals-page">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 32 }}>
        <div>
          <h1 className="page-title" style={{ fontSize: 28, fontWeight: 800, color: '#0f172a', letterSpacing: '-0.02em' }}>
            Room Booking Approvals
          </h1>
          <p style={{ fontSize: 14, color: '#64748b', marginTop: 4 }}>
            Review and manage room booking requests across all campuses
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <Button variant="outline" onClick={() => { fetchConflicts(); setShowConflicts(true); }} data-testid="view-conflicts-btn">
            <AlertTriangle className="w-4 h-4 mr-2" /> Conflicts
          </Button>
          <Button onClick={() => setShowNewRequest(true)} data-testid="new-booking-btn">
            <Calendar className="w-4 h-4 mr-2" /> New Request
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 24 }}>
        {[
          { key: 'pending', label: 'Pending', color: '#f59e0b' },
          { key: 'approved', label: 'Approved', color: '#22c55e' },
          { key: 'rejected', label: 'Rejected', color: '#ef4444' },
        ].map(s => (
          <button key={s.key} onClick={() => setFilter(s.key)}
            data-testid={`filter-${s.key}`}
            style={{
              padding: '16px 20px', background: filter === s.key ? '#f8fafc' : '#fff',
              border: filter === s.key ? `2px solid ${s.color}` : '1px solid #e5e7eb',
              borderRadius: 12, cursor: 'pointer', textAlign: 'left', transition: 'all 0.15s'
            }}>
            <p style={{ fontSize: 28, fontWeight: 800, color: s.color, fontFamily: 'monospace' }}>{counts[s.key] || 0}</p>
            <p style={{ fontSize: 13, fontWeight: 600, color: '#64748b' }}>{s.label}</p>
          </button>
        ))}
      </div>

      {/* Bulk actions */}
      {selectedIds.length > 0 && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 16px', background: '#f0f9ff', border: '1px solid #bae6fd', borderRadius: 10, marginBottom: 16 }}>
          <span style={{ fontSize: 13, fontWeight: 600, color: '#0369a1' }}>{selectedIds.length} selected</span>
          <Button size="sm" onClick={() => handleBulkDecision('approved')} style={{ background: '#22c55e' }} data-testid="bulk-approve">
            <Check className="w-3 h-3 mr-1" /> Approve All
          </Button>
          <Button size="sm" variant="destructive" onClick={() => handleBulkDecision('rejected')} data-testid="bulk-reject">
            <X className="w-3 h-3 mr-1" /> Reject All
          </Button>
          <button onClick={() => setSelectedIds([])} style={{ marginLeft: 'auto', fontSize: 12, color: '#64748b', background: 'none', border: 'none', cursor: 'pointer' }}>Clear</button>
        </div>
      )}

      {/* Bookings list */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: 60 }}>
          <Loader2 className="w-6 h-6 animate-spin" style={{ margin: '0 auto', color: '#64748b' }} />
        </div>
      ) : bookings.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 60, color: '#94a3b8' }}>
          <Calendar className="w-10 h-10" style={{ margin: '0 auto 12px' }} />
          <p style={{ fontSize: 15, fontWeight: 600 }}>No {filter} booking requests</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {bookings.map(booking => {
            const style = STATUS_STYLES[booking.status] || STATUS_STYLES.pending;
            const Icon = style.icon;
            return (
              <div key={booking.id} data-testid={`booking-${booking.id}`}
                style={{
                  background: '#fff', border: booking.has_conflicts ? '2px solid #f59e0b' : '1px solid #e5e7eb',
                  borderRadius: 14, padding: '20px 24px', display: 'flex', alignItems: 'center', gap: 16,
                  transition: 'box-shadow 0.15s', position: 'relative'
                }}>
                {booking.status === 'pending' && (
                  <input type="checkbox" checked={selectedIds.includes(booking.id)}
                    onChange={() => toggleSelect(booking.id)}
                    style={{ width: 18, height: 18, accentColor: '#0f172a', flexShrink: 0 }} />
                )}
                {booking.has_conflicts && (
                  <div style={{ position: 'absolute', top: -8, right: 16, background: '#fef3c7', padding: '2px 10px', borderRadius: 100, fontSize: 11, fontWeight: 700, color: '#92400e', border: '1px solid #fde68a' }}>
                    Conflict
                  </div>
                )}
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                    <h3 style={{ fontSize: 16, fontWeight: 700, color: '#0f172a' }}>{booking.event_name}</h3>
                    <span style={{ fontSize: 11, fontWeight: 600, padding: '2px 10px', borderRadius: 100, background: style.bg, color: style.text }}>
                      {style.label}
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: 20, fontSize: 13, color: '#64748b' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                      <Calendar className="w-3.5 h-3.5" /> {booking.event_date}
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                      <Clock className="w-3.5 h-3.5" /> {booking.start_time} - {booking.end_time}
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                      <MapPin className="w-3.5 h-3.5" /> {booking.room_name}
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                      <Users className="w-3.5 h-3.5" /> {booking.requested_by}
                    </span>
                  </div>
                </div>
                {booking.status === 'pending' && (
                  <div style={{ display: 'flex', gap: 8 }}>
                    <Button size="sm" onClick={() => handleDecision(booking.id, 'approved')}
                      disabled={processing === booking.id}
                      data-testid={`approve-${booking.id}`}
                      style={{ background: '#22c55e', color: '#fff' }}>
                      {processing === booking.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <Check className="w-4 h-4" />}
                    </Button>
                    <Button size="sm" variant="destructive" onClick={() => handleDecision(booking.id, 'rejected')}
                      disabled={processing === booking.id}
                      data-testid={`reject-${booking.id}`}>
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* New Booking Request Dialog */}
      <Dialog open={showNewRequest} onOpenChange={setShowNewRequest}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>New Room Booking Request</DialogTitle>
            <DialogDescription>Submit a request to book a room. It will need admin approval.</DialogDescription>
          </DialogHeader>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14, marginTop: 8 }}>
            <div>
              <label className="form-label">Event Name *</label>
              <input className="form-input" value={newBooking.event_name} data-testid="booking-event-name"
                onChange={e => setNewBooking({ ...newBooking, event_name: e.target.value })} placeholder="Youth Group Night" />
            </div>
            <div>
              <label className="form-label">Description</label>
              <textarea className="form-input" rows={2} value={newBooking.description}
                onChange={e => setNewBooking({ ...newBooking, description: e.target.value })} placeholder="Brief description..." />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}>
              <div>
                <label className="form-label">Date *</label>
                <input className="form-input" type="date" value={newBooking.event_date} data-testid="booking-date"
                  onChange={e => setNewBooking({ ...newBooking, event_date: e.target.value })} />
              </div>
              <div>
                <label className="form-label">Start Time *</label>
                <input className="form-input" type="time" value={newBooking.start_time} data-testid="booking-start"
                  onChange={e => setNewBooking({ ...newBooking, start_time: e.target.value })} />
              </div>
              <div>
                <label className="form-label">End Time *</label>
                <input className="form-input" type="time" value={newBooking.end_time} data-testid="booking-end"
                  onChange={e => setNewBooking({ ...newBooking, end_time: e.target.value })} />
              </div>
            </div>
            <div>
              <label className="form-label">Room *</label>
              <select className="form-input" value={newBooking.room_id} data-testid="booking-room"
                onChange={e => setNewBooking({ ...newBooking, room_id: e.target.value })}>
                <option value="">Select a room</option>
                {rooms.map(r => <option key={r.id} value={r.id}>{r.name} (capacity: {r.capacity})</option>)}
              </select>
            </div>
            <div>
              <label className="form-label">Notes</label>
              <textarea className="form-input" rows={2} value={newBooking.notes}
                onChange={e => setNewBooking({ ...newBooking, notes: e.target.value })} placeholder="Special setup, AV needs..." />
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 4 }}>
              <Button variant="outline" onClick={() => setShowNewRequest(false)}>Cancel</Button>
              <Button onClick={handleCreateBooking} data-testid="submit-booking-btn">Submit Request</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Conflicts Dialog */}
      <Dialog open={showConflicts} onOpenChange={setShowConflicts}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>Room Booking Conflicts</DialogTitle>
            <DialogDescription>These bookings overlap in the same room at the same time.</DialogDescription>
          </DialogHeader>
          <div style={{ maxHeight: 400, overflowY: 'auto' }}>
            {conflicts.length === 0 ? (
              <p style={{ textAlign: 'center', color: '#64748b', padding: 32 }}>No conflicts detected</p>
            ) : conflicts.map((c, i) => (
              <div key={i} style={{ padding: 16, border: '1px solid #fde68a', background: '#fffbeb', borderRadius: 10, marginBottom: 10 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                  <AlertTriangle className="w-4 h-4" style={{ color: '#f59e0b' }} />
                  <span style={{ fontSize: 13, fontWeight: 700, color: '#92400e' }}>{c.room_name} - {c.date}</span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', gap: 8, alignItems: 'center' }}>
                  <div style={{ padding: 10, background: '#fff', borderRadius: 8, border: '1px solid #e5e7eb' }}>
                    <p style={{ fontSize: 13, fontWeight: 600, color: '#0f172a' }}>{c.booking_a.event_name}</p>
                    <p style={{ fontSize: 12, color: '#64748b' }}>{c.booking_a.start_time} - {c.booking_a.end_time}</p>
                  </div>
                  <span style={{ fontSize: 12, fontWeight: 700, color: '#f59e0b' }}>VS</span>
                  <div style={{ padding: 10, background: '#fff', borderRadius: 8, border: '1px solid #e5e7eb' }}>
                    <p style={{ fontSize: 13, fontWeight: 600, color: '#0f172a' }}>{c.booking_b.event_name}</p>
                    <p style={{ fontSize: 12, color: '#64748b' }}>{c.booking_b.start_time} - {c.booking_b.end_time}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
