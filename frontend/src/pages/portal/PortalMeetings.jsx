import { useEffect, useState } from 'react';
import { Calendar, Clock, MessageSquare } from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

export default function PortalMeetings() {
  const [slots, setSlots] = useState([]);
  const [meetings, setMeetings] = useState([]);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [topic, setTopic] = useState('');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(true);
  const [booking, setBooking] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [slotsRes, meetingsRes] = await Promise.all([
        fetch(`${API_URL}/portal/meetings/slots`),
        fetch(`${API_URL}/portal/meetings`)
      ]);
      if (slotsRes.ok) {
        const data = await slotsRes.json();
        setSlots(data.slots || []);
      }
      if (meetingsRes.ok) {
        const data = await meetingsRes.json();
        setMeetings(data.meetings || []);
      }
    } catch (error) {
      toast.error('Unable to load meetings');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const formatSlotTime = (slot) => {
    if (!slot) return '';
    const start = new Date(slot.start_time);
    const end = new Date(slot.end_time);
    return `${start.toLocaleDateString()} · ${start.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })} - ${end.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}`;
  };

  const bookMeeting = async () => {
    if (!selectedSlot) return;
    if (!topic.trim()) {
      toast.error('Please add a meeting topic');
      return;
    }
    setBooking(true);
    try {
      const res = await fetch(`${API_URL}/portal/meetings/book`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        
        body: JSON.stringify({
          slot_id: selectedSlot.id,
          topic: topic.trim(),
          notes: notes.trim() || null
        })
      });
      if (res.ok) {
        toast.success('Meeting scheduled!');
        setSelectedSlot(null);
        setTopic('');
        setNotes('');
        fetchData();
      } else {
        toast.error('Unable to book meeting');
      }
    } catch (error) {
      toast.error('Unable to book meeting');
    } finally {
      setBooking(false);
    }
  };

  return (
    <div className="portal-meetings" data-testid="portal-meetings-page">
      <div className="portal-meetings-header">
        <div>
          <span className="portal-tag">Pastoral Care</span>
          <h1>Meet with a Pastor</h1>
          <p>Pick a time that works for you and share a brief topic so we can serve you well.</p>
        </div>
      </div>

      <div className="portal-meetings-grid">
        <div className="portal-meetings-card" data-testid="meeting-slots-card">
          <h3><Calendar className="w-4 h-4" /> Available Time Slots</h3>
          {loading ? (
            <div className="portal-meetings-empty">Loading slots...</div>
          ) : slots.length === 0 ? (
            <div className="portal-meetings-empty">No open slots right now.</div>
          ) : (
            <div className="portal-meetings-slots">
              {slots.map((slot) => (
                <button
                  key={slot.id}
                  className={`portal-meeting-slot ${selectedSlot?.id === slot.id ? 'active' : ''}`}
                  onClick={() => setSelectedSlot(slot)}
                  data-testid={`meeting-slot-${slot.id}`}
                >
                  <span>{formatSlotTime(slot)}</span>
                  <span className="slot-location">{slot.location || 'Pastor Office'}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="portal-meetings-card" data-testid="meeting-booking-card">
          <h3><MessageSquare className="w-4 h-4" /> Book a Session</h3>
          <div className="portal-meetings-form">
            <div className="portal-meetings-field">
              <label>Selected slot</label>
              <div className="portal-meetings-slot-preview" data-testid="meeting-slot-preview">
                {selectedSlot ? formatSlotTime(selectedSlot) : 'Select a slot to continue'}
              </div>
            </div>
            <div className="portal-meetings-field">
              <label>Meeting topic</label>
              <input
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="Prayer, counseling, discipleship..."
                data-testid="meeting-topic-input"
              />
            </div>
            <div className="portal-meetings-field">
              <label>Notes (optional)</label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
                placeholder="Anything you'd like the pastor to know?"
                data-testid="meeting-notes-input"
              />
            </div>
            <button
              className="portal-meetings-submit"
              onClick={bookMeeting}
              disabled={!selectedSlot || booking}
              data-testid="meeting-book-btn"
            >
              {booking ? 'Booking...' : 'Book Meeting'}
            </button>
          </div>
        </div>
      </div>

      <div className="portal-meetings-card" data-testid="meeting-history-card">
        <h3><Clock className="w-4 h-4" /> Upcoming Sessions</h3>
        {meetings.length === 0 ? (
          <div className="portal-meetings-empty">No meetings scheduled yet.</div>
        ) : (
          <div className="portal-meetings-history">
            {meetings.map((meeting) => (
              <div key={meeting.id} className="portal-meeting-history-item" data-testid={`meeting-history-${meeting.id}`}>
                <div>
                  <strong>{meeting.topic || 'Pastoral Meeting'}</strong>
                  <span>{formatSlotTime(meeting.slot)}</span>
                </div>
                <span className="meeting-status">{meeting.status}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
