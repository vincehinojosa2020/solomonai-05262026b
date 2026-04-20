import { useEffect, useRef, useState } from 'react';
import { Calendar, Clock, Mic, Plus, Save, FileAudio, Users, ChevronDown, ChevronUp, FileText, Sparkles, Loader2 } from 'lucide-react';
import { API_URL, formatCurrency } from '@/lib/utils';
import { toast } from 'sonner';
import DOMPurify from 'dompurify';

export default function MeetingsAdminPage() {
  const [slots, setSlots] = useState([]);
  const [meetings, setMeetings] = useState([]);
  const [slotForm, setSlotForm] = useState({
    date: '',
    start_time: '',
    end_time: '',
    location: "Pastor's office"
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [recordingMeetingId, setRecordingMeetingId] = useState(null);
  const [uploadingMeetingId, setUploadingMeetingId] = useState(null);
  const [expandedMeetings, setExpandedMeetings] = useState({});
  const recorderRef = useRef(null);
  const recordedChunksRef = useRef([]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [slotsRes, meetingsRes] = await Promise.all([
        fetch(`${API_URL}/admin/meetings/slots`),
        fetch(`${API_URL}/admin/meetings`)
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
      toast.error('Unable to load meeting data');
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

  const createSlot = async () => {
    if (!slotForm.date || !slotForm.start_time || !slotForm.end_time) {
      toast.error('Please add date and time');
      return;
    }
    setSaving(true);
    try {
      const start = new Date(`${slotForm.date}T${slotForm.start_time}`);
      const end = new Date(`${slotForm.date}T${slotForm.end_time}`);
      const res = await fetch(`${API_URL}/admin/meetings/slots`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        
        body: JSON.stringify({
          start_time: start.toISOString(),
          end_time: end.toISOString(),
          location: slotForm.location
        })
      });
      if (res.ok) {
        toast.success('Slot added');
        setSlotForm({ ...slotForm, start_time: '', end_time: '' });
        fetchData();
      } else {
        toast.error('Unable to add slot');
      }
    } catch (error) {
      toast.error('Unable to add slot');
    } finally {
      setSaving(false);
    }
  };

  const updateMeetingNotes = async (meetingId, notes, status) => {
    try {
      const res = await fetch(`${API_URL}/admin/meetings/${meetingId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        
        body: JSON.stringify({ notes, status })
      });
      if (res.ok) {
        toast.success('Notes saved');
        fetchData();
      } else {
        toast.error('Unable to save notes');
      }
    } catch (error) {
      toast.error('Unable to save notes');
    }
  };

  const uploadRecording = async (meetingId, blob) => {
    setUploadingMeetingId(meetingId);
    try {
      const formData = new FormData();
      formData.append('file', blob, `meeting-${meetingId}.webm`);
      toast.info('Transcribing and analyzing recording...', { duration: 10000 });
      const res = await fetch(`${API_URL}/admin/meetings/${meetingId}/recording`, {
        method: 'POST',
        
        body: formData
      });
      if (res.ok) {
        const data = await res.json();
        toast.success('Recording transcribed and summarized!');
        setExpandedMeetings(prev => ({ ...prev, [meetingId]: true }));
        fetchData();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Unable to process recording');
      }
    } catch (error) {
      toast.error('Unable to process recording');
    } finally {
      setUploadingMeetingId(null);
    }
  };

  const toggleExpand = (meetingId) => {
    setExpandedMeetings(prev => ({ ...prev, [meetingId]: !prev[meetingId] }));
  };

  const startRecording = async (meetingId) => {
    if (recordingMeetingId) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      recordedChunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) recordedChunksRef.current.push(event.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(recordedChunksRef.current, { type: 'audio/webm' });
        uploadRecording(meetingId, blob);
        stream.getTracks().forEach((track) => track.stop());
        setRecordingMeetingId(null);
      };

      recorderRef.current = recorder;
      setRecordingMeetingId(meetingId);
      recorder.start();
    } catch (error) {
      toast.error('Microphone access denied');
    }
  };

  const stopRecording = () => {
    recorderRef.current?.stop();
  };

  return (
    <div className="meetings-admin" data-testid="meetings-admin-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Pastoral Meetings</h1>
          <p className="page-subtitle">Schedule 1:1 sessions, capture notes, and keep history for every member.</p>
        </div>
      </div>

      <div className="meetings-admin-grid">
        <div className="meetings-admin-card" data-testid="meetings-slots-card">
          <h3><Calendar className="w-4 h-4" /> Meeting Slots</h3>
          <div className="meetings-slot-form">
            <input
              type="date"
              value={slotForm.date}
              onChange={(e) => setSlotForm({ ...slotForm, date: e.target.value })}
              data-testid="meeting-slot-date"
            />
            <input
              type="time"
              value={slotForm.start_time}
              onChange={(e) => setSlotForm({ ...slotForm, start_time: e.target.value })}
              data-testid="meeting-slot-start"
            />
            <input
              type="time"
              value={slotForm.end_time}
              onChange={(e) => setSlotForm({ ...slotForm, end_time: e.target.value })}
              data-testid="meeting-slot-end"
            />
            <input
              value={slotForm.location}
              onChange={(e) => setSlotForm({ ...slotForm, location: e.target.value })}
              placeholder="Location"
              data-testid="meeting-slot-location"
            />
            <button className="meetings-slot-btn" onClick={createSlot} disabled={saving} data-testid="meeting-slot-save">
              <Plus className="w-4 h-4" /> Add Slot
            </button>
          </div>
          {loading ? (
            <div className="meetings-empty">Loading slots...</div>
          ) : (
            <div className="meetings-slot-list">
              {slots.map((slot) => (
                <div key={slot.id} className="meetings-slot-item" data-testid={`meeting-slot-admin-${slot.id}`}>
                  <div>
                    <strong>{formatSlotTime(slot)}</strong>
                    <span>{slot.location || "Pastor's office"}</span>
                  </div>
                  <span className="meeting-status">{slot.status}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="meetings-admin-card" data-testid="meetings-list-card">
          <h3><Users className="w-4 h-4" /> Scheduled Meetings</h3>
          {meetings.length === 0 ? (
            <div className="meetings-empty">No meetings scheduled yet.</div>
          ) : (
            <div className="meetings-list">
              {meetings.map((meeting) => (
                <div key={meeting.id} className="meeting-card" data-testid={`meeting-${meeting.id}`}>
                  <div className="meeting-card-header">
                    <div>
                      <strong>{meeting.member_name || 'Member'} · {meeting.topic || 'Meeting'}</strong>
                      <span>{formatSlotTime(meeting.slot)}</span>
                    </div>
                    <span className={`meeting-status ${meeting.status}`}>{meeting.status}</span>
                  </div>
                  <textarea
                    defaultValue={meeting.notes || ''}
                    placeholder="Add pastoral notes..."
                    className="meeting-notes"
                    data-testid={`meeting-notes-${meeting.id}`}
                  />
                  <div className="meeting-actions">
                    <button
                      className="meeting-save-btn"
                      onClick={(e) => {
                        const notes = e.currentTarget.closest('.meeting-card').querySelector('textarea').value;
                        updateMeetingNotes(meeting.id, notes, meeting.status);
                      }}
                      data-testid={`meeting-save-${meeting.id}`}
                    >
                      <Save className="w-4 h-4" /> Save Notes
                    </button>
                    {uploadingMeetingId === meeting.id ? (
                      <button className="meeting-record-btn processing" disabled>
                        <Loader2 className="w-4 h-4 animate-spin" /> Processing...
                      </button>
                    ) : (
                      <button
                        className={`meeting-record-btn ${recordingMeetingId === meeting.id ? 'recording' : ''}`}
                        onClick={() => recordingMeetingId === meeting.id ? stopRecording() : startRecording(meeting.id)}
                        data-testid={`meeting-record-${meeting.id}`}
                      >
                        <Mic className="w-4 h-4" /> {recordingMeetingId === meeting.id ? 'Stop Recording' : 'Record Meeting'}
                      </button>
                    )}
                    <label className={`meeting-upload ${uploadingMeetingId === meeting.id ? 'disabled' : ''}`}>
                      <FileAudio className="w-4 h-4" /> Upload Audio
                      <input
                        type="file"
                        accept="audio/*"
                        disabled={uploadingMeetingId === meeting.id}
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (file) uploadRecording(meeting.id, file);
                        }}
                        data-testid={`meeting-upload-${meeting.id}`}
                      />
                    </label>
                  </div>
                  
                  {/* AI Summary Section */}
                  {(meeting.summary || meeting.transcript) && (
                    <div className="meeting-ai-section" data-testid={`meeting-ai-${meeting.id}`}>
                      <button 
                        className="meeting-ai-toggle"
                        onClick={() => toggleExpand(meeting.id)}
                      >
                        <Sparkles className="w-4 h-4" />
                        <span>AI Meeting Summary</span>
                        {expandedMeetings[meeting.id] ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                      </button>
                      
                      {expandedMeetings[meeting.id] && (
                        <div className="meeting-ai-content">
                          {meeting.summary && (
                            <div className="meeting-summary-box" data-testid={`meeting-summary-${meeting.id}`}>
                              <h4><Sparkles className="w-4 h-4" /> AI Summary</h4>
                              <div className="meeting-summary-text" dangerouslySetInnerHTML={{ 
                                __html: DOMPurify.sanitize(meeting.summary
                                  .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                                  .replace(/\n/g, '<br/>'))
                              }} />
                            </div>
                          )}
                          {meeting.transcript && (
                            <div className="meeting-transcript-box" data-testid={`meeting-transcript-${meeting.id}`}>
                              <h4><FileText className="w-4 h-4" /> Transcript</h4>
                              <p className="meeting-transcript-text">{meeting.transcript}</p>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
