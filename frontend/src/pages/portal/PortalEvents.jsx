import { useState, useEffect, useCallback } from 'react';
import { useOutletContext } from 'react-router-dom';
import { usePolling } from '@/hooks/usePolling';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MapPin, Clock, Users, CheckCircle, Calendar as CalendarIcon,
  X, Share2, Ticket, AlertCircle, ChevronRight, CreditCard,
  Check, Loader2, Star, Lock, ArrowLeft
} from 'lucide-react';
import { API_URL, formatCurrency } from '@/lib/utils';
import { toast } from 'sonner';

const EVENT_CATEGORIES = [
  { id: 'all', label: 'All Events' },
  { id: 'worship', label: 'Worship' },
  { id: 'women', label: 'Women' },
  { id: 'men', label: 'Men' },
  { id: 'youth', label: 'Youth' },
  { id: 'community', label: 'Community' },
  { id: 'conferences', label: 'Conferences' },
];

// ── Mobile-first Paid Event Checkout Sheet ───────────────────────────────────
function PaidCheckoutSheet({ event, onClose, onSuccess, user }) {
  const [step, setStep] = useState('select');   // select → review → confirm
  const [selectedTier, setSelectedTier] = useState(null);
  const [savedCards, setSavedCards] = useState([]);
  const [selectedCard, setSelectedCard] = useState(null);
  const [coverFee, setCoverFee] = useState(false);
  const [loading, setLoading] = useState(false);
  const [confirmation, setConfirmation] = useState(null);

  const tiers = event?.ticket_tiers || [];
  const isFree = !event?.price || event.price === 0;

  useEffect(() => {
    // Auto-select first tier
    if (tiers.length > 0 && !selectedTier) setSelectedTier(tiers[0]);
    // Load saved cards
    const token = sessionStorage.getItem('session_token');
    if (token) {
      fetch(`${API_URL}/portal/payment-methods`, { headers: { Authorization: `Bearer ${token}` } })
        .then(r => r.ok ? r.json() : null)
        .then(d => {
          const cards = d?.payment_methods || [];
          setSavedCards(cards);
          const def = cards.find(c => c.is_default) || cards[0];
          if (def) setSelectedCard(def);
        })
        .catch(() => {});
    }
    // Free events: skip straight to review
    if (isFree) setSelectedTier({ id: 'free', name: 'Free Entry', price: 0 });
  }, [event]);

  const price = selectedTier?.price || 0;
  const processingFee = price > 0 ? Math.round((price * 0.019 + 0.30) * 100) / 100 : 0;
  const totalCharged = coverFee ? price + processingFee : price;

  const handleConfirm = async () => {
    setLoading(true);
    try {
      const token = sessionStorage.getItem('session_token');
      const res = await fetch(`${API_URL}/portal/events/${event.id}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          tier_id: selectedTier?.id || 'general',
          payment_method_id: selectedCard?.id || null,
          cover_fee: coverFee,
        }),
      });
      const data = await res.json();
      if (res.ok) {
        setConfirmation(data);
        setStep('confirmed');
        onSuccess?.();
      } else {
        toast.error(data.detail || 'Registration failed. Please try again.');
      }
    } catch {
      toast.error('Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    /* Full-screen overlay — bottom sheet on mobile, centered modal on desktop */
    <div
      className="fixed inset-0 z-50 flex flex-col justify-end md:justify-center md:items-center"
      style={{ background: 'rgba(0,0,0,0.6)' }}
      onClick={e => { if (e.target === e.currentTarget && step !== 'confirmed') onClose(); }}
    >
      <motion.div
        initial={{ y: '100%', opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: '100%', opacity: 0 }}
        transition={{ type: 'spring', damping: 28, stiffness: 300 }}
        className="bg-white rounded-t-3xl md:rounded-2xl w-full md:max-w-md overflow-hidden shadow-2xl"
        style={{ maxHeight: '92vh', overflowY: 'auto' }}
        data-testid="event-checkout-sheet"
      >
        {/* ── CONFIRMED ── */}
        {step === 'confirmed' && confirmation && (
          <div className="p-6 text-center">
            <div className="w-20 h-20 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="w-10 h-10 text-emerald-600" />
            </div>
            <h2 className="text-2xl font-black text-slate-900 mb-1">You're in! 🎉</h2>
            <p className="text-slate-500 text-sm mb-6">See you at {event.name}</p>
            <div className="bg-slate-50 rounded-2xl p-4 text-left space-y-3 mb-6">
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">Event</span>
                <span className="font-semibold text-slate-900">{event.name}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">Date</span>
                <span className="font-semibold text-slate-900">
                  {event.event_date ? new Date(event.event_date+'T12:00:00').toLocaleDateString('en-US',{weekday:'short',month:'long',day:'numeric'}) : ''}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">Ticket</span>
                <span className="font-semibold text-slate-900">{confirmation.tier?.name}</span>
              </div>
              {confirmation.is_paid && confirmation.payment && (
                <>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-500">Paid</span>
                    <span className="font-bold text-emerald-700">${confirmation.payment.amount_charged?.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-xs text-slate-400">
                    <span>Card</span>
                    <span>{confirmation.payment.card_brand} ••••{confirmation.payment.card_last_four}</span>
                  </div>
                </>
              )}
            </div>
            <p className="text-xs text-slate-400 mb-5">A confirmation has been sent to your email.</p>
            <button onClick={onClose} className="w-full py-4 bg-slate-900 text-white rounded-2xl font-bold text-base hover:bg-slate-800 transition-colors" data-testid="checkout-done-btn">
              Done
            </button>
          </div>
        )}

        {/* ── TIER SELECTION ── */}
        {step === 'select' && (
          <div className="p-6">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-xl font-black text-slate-900">Save My Spot</h2>
              <button onClick={onClose} className="w-9 h-9 bg-slate-100 rounded-full flex items-center justify-center hover:bg-slate-200">
                <X className="w-4 h-4 text-slate-600" />
              </button>
            </div>

            {/* Event info strip */}
            <div className="bg-slate-50 rounded-2xl p-3 flex items-center gap-3 mb-5">
              <div className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 text-xl" style={{background:'linear-gradient(135deg,#1e3a5f,#3b82f6)'}}>
                🎟️
              </div>
              <div className="min-w-0">
                <p className="font-bold text-slate-900 truncate text-sm">{event.name}</p>
                <p className="text-xs text-slate-500">
                  {event.event_date ? new Date(event.event_date+'T12:00:00').toLocaleDateString('en-US',{weekday:'short',month:'short',day:'numeric'}) : ''} · {event.location?.split(',')[0]}
                </p>
              </div>
            </div>

            {/* Tier options */}
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Choose your ticket</p>
            <div className="space-y-2.5 mb-6">
              {tiers.map(tier => (
                <button
                  key={tier.id}
                  onClick={() => setSelectedTier(tier)}
                  className="w-full text-left p-4 rounded-2xl border-2 transition-all"
                  style={{
                    borderColor: selectedTier?.id === tier.id ? '#1e3a5f' : '#e2e8f0',
                    background: selectedTier?.id === tier.id ? '#f0f4ff' : 'white',
                  }}
                  data-testid={`tier-${tier.id}`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0"
                        style={{ borderColor: selectedTier?.id === tier.id ? '#1e3a5f' : '#cbd5e1',
                          background: selectedTier?.id === tier.id ? '#1e3a5f' : 'white' }}>
                        {selectedTier?.id === tier.id && <Check className="w-3 h-3 text-white" />}
                      </div>
                      <div>
                        <p className="font-bold text-slate-900 text-sm">{tier.name}</p>
                        {tier.description && <p className="text-xs text-slate-500 mt-0.5 leading-snug">{tier.description}</p>}
                      </div>
                    </div>
                    <span className="text-lg font-black flex-shrink-0 ml-3" style={{color: tier.price === 0 ? '#16a34a' : '#0f172a'}}>
                      {tier.price === 0 ? 'Free' : `$${tier.price}`}
                    </span>
                  </div>
                  {tier.spots_remaining !== undefined && tier.spots_remaining <= 30 && (
                    <p className="text-[11px] text-amber-600 font-semibold mt-2 ml-8">
                      Only {tier.spots_remaining} spots left!
                    </p>
                  )}
                </button>
              ))}
            </div>

            {/* Sticky CTA */}
            <button
              onClick={() => setStep('review')}
              disabled={!selectedTier}
              className="w-full py-4 rounded-2xl font-bold text-base text-white transition-all disabled:opacity-40"
              style={{ background: selectedTier ? '#1e3a5f' : '#94a3b8' }}
              data-testid="checkout-next-btn"
            >
              {isFree || selectedTier?.price === 0 ? 'Continue — Free' : `Continue — $${selectedTier?.price}`}
              <ChevronRight className="inline w-5 h-5 ml-1" />
            </button>
          </div>
        )}

        {/* ── PAYMENT REVIEW ── */}
        {step === 'review' && (
          <div className="p-6">
            <div className="flex items-center gap-3 mb-5">
              <button onClick={() => setStep('select')} className="w-9 h-9 bg-slate-100 rounded-full flex items-center justify-center">
                <ArrowLeft className="w-4 h-4 text-slate-600" />
              </button>
              <h2 className="text-xl font-black text-slate-900">
                {price === 0 ? 'Confirm Registration' : 'Confirm & Pay'}
              </h2>
            </div>

            {/* Order summary */}
            <div className="bg-slate-50 rounded-2xl p-4 mb-4 space-y-2.5">
              <div className="flex justify-between text-sm">
                <span className="text-slate-600">{selectedTier?.name}</span>
                <span className="font-semibold">{price === 0 ? 'Free' : `$${price.toFixed(2)}`}</span>
              </div>
              {price > 0 && (
                <label className="flex items-center justify-between cursor-pointer py-1">
                  <span className="text-sm text-slate-600 flex-1 mr-4">Cover processing fee so 100% goes to the church</span>
                  <div className="relative flex-shrink-0">
                    <input type="checkbox" checked={coverFee} onChange={e => setCoverFee(e.target.checked)} className="sr-only" data-testid="cover-fee-toggle"/>
                    <div className={`w-11 h-6 rounded-full transition-colors ${coverFee ? 'bg-blue-600' : 'bg-slate-300'}`}/>
                    <div className={`absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${coverFee ? 'translate-x-5' : 'translate-x-0.5'}`}/>
                  </div>
                </label>
              )}
              {price > 0 && coverFee && (
                <div className="flex justify-between text-xs text-slate-500">
                  <span>Processing fee</span>
                  <span>+${processingFee.toFixed(2)}</span>
                </div>
              )}
              {price > 0 && (
                <div className="flex justify-between font-bold text-base pt-2 border-t border-slate-200">
                  <span>Total</span>
                  <span>${totalCharged.toFixed(2)}</span>
                </div>
              )}
            </div>

            {/* Payment method */}
            {price > 0 && (
              <div className="mb-5">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Payment</p>
                {savedCards.length > 0 ? (
                  <div className="space-y-2">
                    {savedCards.map(card => (
                      <button key={card.id} onClick={() => setSelectedCard(card)}
                        className="w-full flex items-center gap-3 p-3.5 rounded-xl border-2 text-left transition-all"
                        style={{ borderColor: selectedCard?.id === card.id ? '#1e3a5f' : '#e2e8f0',
                          background: selectedCard?.id === card.id ? '#f0f4ff' : 'white' }}>
                        <CreditCard className="w-5 h-5 text-slate-500 flex-shrink-0" />
                        <div className="flex-1">
                          <span className="text-sm font-semibold text-slate-800">{card.card_brand || 'Card'} ••••{card.card_last_four}</span>
                          {card.is_default && <span className="ml-2 text-[10px] bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded font-semibold">Default</span>}
                        </div>
                        {selectedCard?.id === card.id && <Check className="w-4 h-4 text-blue-700 flex-shrink-0" />}
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-sm text-amber-800">
                    No saved card on file. Add a payment method in your profile first.
                  </div>
                )}
              </div>
            )}

            {/* Security note */}
            {price > 0 && (
              <div className="flex items-center gap-2 text-xs text-slate-400 mb-5">
                <Lock className="w-3.5 h-3.5" />
                <span>Secured by Solomon Pay · Never stored, always encrypted</span>
              </div>
            )}

            {/* Final CTA */}
            <button
              onClick={handleConfirm}
              disabled={loading || (price > 0 && !selectedCard)}
              className="w-full py-4 rounded-2xl font-bold text-base text-white transition-all disabled:opacity-50 flex items-center justify-center gap-2"
              style={{ background: loading ? '#64748b' : '#1e3a5f' }}
              data-testid="checkout-confirm-btn"
            >
              {loading ? (
                <><Loader2 className="w-5 h-5 animate-spin" /> Processing...</>
              ) : price === 0 ? (
                <>Save My Spot — Free <Check className="w-5 h-5" /></>
              ) : (
                <>Confirm & Pay ${totalCharged.toFixed(2)} <Lock className="w-4 h-4" /></>
              )}
            </button>
            <p className="text-center text-xs text-slate-400 mt-3">You won't be charged until you tap "Confirm & Pay"</p>
          </div>
        )}
      </motion.div>
    </div>
  );
}

export default function PortalEvents() {
  const { user, memberData, tenant } = useOutletContext();
  const [events, setEvents] = useState([]);
  const [myEvents, setMyEvents] = useState([]);
  const [filter, setFilter] = useState('all');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [checkoutEvent, setCheckoutEvent] = useState(null);   // triggers checkout sheet

  useEffect(() => { fetchEvents(); fetchMyEvents(); }, []);

  const pollEvents = useCallback(() => { fetchEvents(); fetchMyEvents(); }, []);
  usePolling(pollEvents, 30000);

  const fetchEvents = async () => {
    try {
      const res = await fetch(`${API_URL}/portal/events`);
      if (res.ok) setEvents(await res.json());
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const fetchMyEvents = async () => {
    try {
      const token = sessionStorage.getItem('session_token');
      const res = await fetch(`${API_URL}/portal/my-events`, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
      if (res.ok) { const data = await res.json(); setMyEvents(data.events || []); }
    } catch (e) { console.error(e); }
  };

  const registeredEventIds = myEvents.map(e => e.id);

  // Open checkout sheet — handles both free and paid events
  const handleRegister = (eventId) => {
    const event = events.find ? events.find(e => e.id === eventId) : events[eventId];
    const evt = Array.isArray(events) ? events.find(e => e.id === eventId) : null;
    if (evt) {
      setCheckoutEvent(evt);
      setSelectedEvent(null);  // close detail modal if open
    } else {
      // fallback: direct free register if event not found in local state
      doRegister(eventId);
    }
  };

  const doRegister = async (eventId) => {
    try {
      const token = sessionStorage.getItem('session_token');
      const res = await fetch(`${API_URL}/portal/events/${eventId}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: JSON.stringify({}),
      });
      const data = await res.json();
      if (res.ok) { toast.success(data.message || "You're registered!"); fetchEvents(); fetchMyEvents(); }
      else toast.error(data.detail || 'Failed to register');
    } catch { toast.error('Failed to register'); }
  };

  const handleCancelRegistration = async (eventId) => {
    if (!confirm('Cancel your registration for this event?')) return;
    try {
      const res = await fetch(`${API_URL}/portal/events/${eventId}/register`, {
        method: 'DELETE'
      });
      if (res.ok) { toast.success('Registration cancelled'); fetchEvents(); fetchMyEvents(); }
      else toast.error('Failed to cancel registration');
    } catch { toast.error('Failed to cancel registration'); }
  };

  const formatDate = (dateStr) => {
    const d = new Date(dateStr);
    return {
      month: d.toLocaleDateString('en-US', { month: 'short' }).toUpperCase(),
      day: d.getDate(),
      time: d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }),
      full: d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }),
      weekday: d.toLocaleDateString('en-US', { weekday: 'long' }),
    };
  };

  const handleShare = (event) => {
    const shareText = `I'm attending ${event.name} at ${tenant?.name || 'our church'}! Join me: `;
    if (navigator.share) {
      navigator.share({ title: event.name, text: shareText, url: window.location.href });
    } else {
      navigator.clipboard.writeText(shareText + window.location.href);
      toast.success('Link copied to clipboard!');
    }
  };

  const filterTabs = [
    { id: 'all', label: 'All' },
    { id: 'week', label: 'This Week' },
    { id: 'month', label: 'This Month' },
    { id: 'registered', label: 'My Events' },
  ];

  const filteredEvents = events.filter(event => {
    if (filter === 'registered') return registeredEventIds.includes(event.id);
    if (categoryFilter !== 'all') return event.category?.toLowerCase() === categoryFilter.toLowerCase();
    return true;
  });

  const nextMajorEvent = events.find(e => e.is_featured) || events[0];

  const getCapacityInfo = (event) => {
    if (!event.capacity) return null;
    const count = event.registration_count || 0;
    const pct = Math.min(100, Math.round((count / event.capacity) * 100));
    const isFull = count >= event.capacity;
    return { count, capacity: event.capacity, pct, isFull, waitlist: event.waitlist_count || 0 };
  };

  return (
    <div className="portal-events" data-testid="portal-events">
      {/* Hero Banner */}
      {nextMajorEvent && (
        <div className="events-hero" data-testid="events-hero">
          <div className="events-hero-overlay" />
          <div className="events-hero-content">
            <span className="events-hero-tag">Coming Up</span>
            <h1>{nextMajorEvent.name}</h1>
            <p className="events-hero-date">
              {nextMajorEvent.start_datetime ? formatDate(nextMajorEvent.start_datetime).full : nextMajorEvent.event_date ? formatDate(nextMajorEvent.event_date).full : 'TBD'}
              {nextMajorEvent.location ? ` • ${nextMajorEvent.location}` : ''}
            </p>
            {nextMajorEvent.registration_count > 0 && (
              <p className="events-hero-count">{nextMajorEvent.registration_count} people registered</p>
            )}
            <div className="events-hero-actions">
              {!registeredEventIds.includes(nextMajorEvent.id) ? (
                <button className="events-hero-btn primary" onClick={() => handleRegister(nextMajorEvent.id)} data-testid="hero-register-btn">
                  Save My Spot
                </button>
              ) : (
                <span className="events-hero-registered"><CheckCircle className="w-5 h-5" /> You're Registered!</span>
              )}
              <button className="events-hero-btn secondary" onClick={() => handleShare(nextMajorEvent)}>
                <Share2 className="w-4 h-4" /> Share
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="portal-page-header">
        <h2 className="portal-page-title">Upcoming Events</h2>
      </div>

      {/* Category Pills */}
      <div className="events-category-tabs">
        {EVENT_CATEGORIES.map(cat => (
          <button key={cat.id} onClick={() => setCategoryFilter(cat.id)} className={`events-cat-tab ${categoryFilter === cat.id ? 'active' : ''}`}>
            {cat.label}
          </button>
        ))}
      </div>

      {/* Filter Tabs */}
      <div className="portal-filter-tabs">
        {filterTabs.map(tab => (
          <button key={tab.id} onClick={() => setFilter(tab.id)} className={`portal-filter-tab ${filter === tab.id ? 'active' : ''}`}>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Events Grid */}
      <div className="portal-events-grid">
        {loading ? (
          <p className="text-slate-500 text-sm py-8 text-center col-span-full">Loading events...</p>
        ) : filteredEvents.length === 0 ? (
          <p className="text-slate-500 text-sm py-8 text-center col-span-full">No events found.</p>
        ) : (
          filteredEvents.map((event, i) => {
            const isRegistered = registeredEventIds.includes(event.id);
            const dateInfo = event.start_datetime ? formatDate(event.start_datetime) : event.event_date ? formatDate(event.event_date) : { month: '?', day: '?', time: '' };
            const capInfo = getCapacityInfo(event);
            const tiers = event.ticket_tiers || [];

            return (
              <motion.div
                key={event.id}
                className="portal-event-card"
                data-testid={`event-card-${event.id}`}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.04 }}
              >
                <div className="portal-event-date-chip">
                  <span className="portal-event-month">{dateInfo.month}</span>
                  <span className="portal-event-day">{dateInfo.day}</span>
                </div>

                <div className="portal-event-card-content">
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <h3 className="portal-event-card-title">{event.name}</h3>
                    {/* Price badge — immediately visible */}
                    {event.price > 0 ? (
                      <span className="flex-shrink-0 inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-blue-600 text-white" data-testid={`event-price-${event.id}`}>
                        <Ticket className="w-3 h-3" />${event.price}
                      </span>
                    ) : event.requires_registration ? (
                      <span className="flex-shrink-0 inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-700">
                        Free
                      </span>
                    ) : null}
                  </div>

                  <div className="portal-event-card-meta">
                    {event.location && (
                      <span className="portal-event-card-info"><MapPin className="w-3.5 h-3.5" /> {event.location}</span>
                    )}
                    {(event.start_time || dateInfo.time) && (
                      <span className="portal-event-card-info"><Clock className="w-3.5 h-3.5" /> {event.start_time || dateInfo.time}</span>
                    )}
                    {event.registration_count > 0 && (
                      <span className="portal-event-card-info"><Users className="w-3.5 h-3.5" /> {event.registration_count} attending</span>
                    )}
                    {event.category && (
                      <span className="portal-event-card-info" style={{ background: '#eff6ff', color: '#3b82f6', padding: '1px 8px', borderRadius: '99px', fontSize: '11px', fontWeight: '600' }}>
                        {event.category}
                      </span>
                    )}
                  </div>

                  {/* Capacity Bar */}
                  {capInfo && (
                    <div data-testid={`event-capacity-${event.id}`} style={{ margin: '8px 0' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#64748b', fontWeight: '500', marginBottom: '4px' }}>
                        <span>{capInfo.count} / {capInfo.capacity} spots</span>
                        {capInfo.isFull && <span style={{ color: '#ef4444', fontWeight: '600' }}>FULL</span>}
                      </div>
                      <div style={{ height: '4px', background: '#e5e7eb', borderRadius: '2px', overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: `${capInfo.pct}%`, background: capInfo.isFull ? '#ef4444' : '#3b82f6', borderRadius: '2px', transition: 'width 0.3s' }} />
                      </div>
                      {capInfo.waitlist > 0 && (
                        <span style={{ fontSize: '10px', color: '#f59e0b', fontWeight: '600', marginTop: '2px', display: 'block' }}>
                          {capInfo.waitlist} on waitlist
                        </span>
                      )}
                    </div>
                  )}

                  {/* Ticket Tiers */}
                  {tiers.length > 0 && (
                    <div data-testid={`event-tiers-${event.id}`} style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', margin: '6px 0' }}>
                      {tiers.map((tier, ti) => (
                        <span key={ti} style={{
                          fontSize: '10px', fontWeight: '600', padding: '2px 8px', borderRadius: '99px',
                          background: tier.price === 0 ? '#f0fdf4' : tier.name?.toLowerCase().includes('vip') ? '#fef3c7' : '#f1f5f9',
                          color: tier.price === 0 ? '#16a34a' : tier.name?.toLowerCase().includes('vip') ? '#d97706' : '#475569',
                        }}>
                          <Ticket className="w-3 h-3 inline mr-0.5" style={{ verticalAlign: '-2px' }} />
                          {tier.name}{tier.price > 0 ? ` $${tier.price}` : ' Free'}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Actions */}
                  <div className="portal-event-card-actions">
                    {isRegistered ? (
                      <>
                        <span className="portal-registered-badge"><CheckCircle className="w-4 h-4" /> Registered</span>
                        <button onClick={() => handleCancelRegistration(event.id)} className="portal-event-btn secondary" style={{ color: '#dc2626' }}>
                          <X className="w-3 h-3" /> Cancel
                        </button>
                      </>
                    ) : (
                      <>
                        <button className="portal-event-btn secondary" onClick={() => setSelectedEvent(event)}>View Details</button>
                        {(event.registration_required || event.requires_registration) && (
                          <button onClick={() => handleRegister(event.id)} className="portal-event-btn primary" data-testid={`register-event-${event.id}`}>
                            {capInfo?.isFull ? 'Join Waitlist' : 'Register'}
                          </button>
                        )}
                      </>
                    )}
                    <button onClick={() => handleShare(event)} style={{ marginLeft: 'auto', background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', padding: '4px' }}>
                      <Share2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </motion.div>
            );
          })
        )}
      </div>

      {/* Event Detail Modal */}
      <AnimatePresence>
        {selectedEvent && (
          <motion.div
            className="fixed inset-0 z-[9998] flex items-center justify-center p-4"
            style={{ background: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(4px)' }}
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={() => setSelectedEvent(null)}
          >
            <motion.div
              className="bg-white rounded-2xl w-full max-w-lg overflow-hidden"
              initial={{ y: 30, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 30, opacity: 0 }}
              onClick={e => e.stopPropagation()}
              data-testid="event-detail-modal"
            >
              {/* Modal Header */}
              <div style={{ background: '#0f172a', padding: '24px', color: '#fff', position: 'relative' }}>
                <button onClick={() => setSelectedEvent(null)} style={{ position: 'absolute', top: '12px', right: '12px', background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: '50%', width: '32px', height: '32px', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', color: '#fff' }}>
                  <X className="w-4 h-4" />
                </button>
                {selectedEvent.category && (
                  <span style={{ fontSize: '11px', background: 'rgba(59,130,246,0.2)', color: '#93c5fd', padding: '2px 10px', borderRadius: '99px', fontWeight: '600' }}>{selectedEvent.category}</span>
                )}
                <h2 style={{ fontSize: '20px', fontWeight: '700', margin: '8px 0 4px' }}>{selectedEvent.name}</h2>
                <p style={{ fontSize: '13px', color: '#94a3b8' }}>
                  {selectedEvent.event_date ? formatDate(selectedEvent.event_date).full : 'TBD'}
                  {selectedEvent.location ? ` • ${selectedEvent.location}` : ''}
                </p>
              </div>

              <div style={{ padding: '20px' }}>
                {selectedEvent.description && (
                  <p style={{ fontSize: '14px', color: '#475569', lineHeight: 1.6, marginBottom: '16px' }}>{selectedEvent.description}</p>
                )}

                {/* Details */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '16px' }}>
                  {selectedEvent.start_time && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', color: '#475569' }}>
                      <Clock className="w-4 h-4" style={{ color: '#3b82f6' }} /> {selectedEvent.start_time}{selectedEvent.end_time ? ` - ${selectedEvent.end_time}` : ''}
                    </div>
                  )}
                  {selectedEvent.location && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', color: '#475569' }}>
                      <MapPin className="w-4 h-4" style={{ color: '#3b82f6' }} /> {selectedEvent.location}
                    </div>
                  )}
                  {selectedEvent.registration_count > 0 && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', color: '#475569' }}>
                      <Users className="w-4 h-4" style={{ color: '#3b82f6' }} /> {selectedEvent.registration_count} registered
                    </div>
                  )}
                </div>

                {/* Capacity in modal */}
                {(() => {
                  const cap = getCapacityInfo(selectedEvent);
                  if (!cap) return null;
                  return (
                    <div style={{ background: '#f8fafc', borderRadius: '10px', padding: '12px', marginBottom: '16px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', fontWeight: '600', marginBottom: '6px' }}>
                        <span style={{ color: '#475569' }}>{cap.count} / {cap.capacity} spots filled</span>
                        {cap.isFull && <span style={{ color: '#ef4444' }}>This event is full — join the waitlist?</span>}
                      </div>
                      <div style={{ height: '6px', background: '#e5e7eb', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: `${cap.pct}%`, background: cap.isFull ? '#ef4444' : '#3b82f6', borderRadius: '3px' }} />
                      </div>
                      {cap.waitlist > 0 && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginTop: '6px', fontSize: '11px', color: '#f59e0b', fontWeight: '600' }}>
                          <AlertCircle className="w-3 h-3" /> {cap.waitlist} on waitlist
                        </div>
                      )}
                    </div>
                  );
                })()}

                {/* Ticket Tiers in modal */}
                {(selectedEvent.ticket_tiers || []).length > 0 && (
                  <div style={{ marginBottom: '16px' }}>
                    <h4 style={{ fontSize: '13px', fontWeight: '600', color: '#0f172a', marginBottom: '8px' }}>Ticket Options</h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      {selectedEvent.ticket_tiers.map((tier, i) => (
                        <div key={tier.name || tier.id || i} style={{
                          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                          padding: '10px 12px', borderRadius: '8px',
                          border: '1px solid #e5e7eb', background: '#fff',
                        }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <Ticket className="w-4 h-4" style={{ color: tier.name?.toLowerCase().includes('vip') ? '#d97706' : '#3b82f6' }} />
                            <div>
                              <div style={{ fontSize: '13px', fontWeight: '600', color: '#0f172a' }}>{tier.name}</div>
                              {tier.description && <div style={{ fontSize: '11px', color: '#94a3b8' }}>{tier.description}</div>}
                            </div>
                          </div>
                          <span style={{ fontSize: '14px', fontWeight: '700', color: tier.price === 0 ? '#16a34a' : '#0f172a' }}>
                            {tier.price === 0 ? 'Free' : `$${tier.price}`}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Register Button */}
                {!registeredEventIds.includes(selectedEvent.id) ? (
                  (selectedEvent.registration_required || selectedEvent.requires_registration) && (
                    <button
                      data-testid="modal-register-btn"
                      onClick={() => { handleRegister(selectedEvent.id); setSelectedEvent(null); }}
                      style={{
                        width: '100%', padding: '12px', background: '#3b82f6', color: '#fff',
                        border: 'none', borderRadius: '10px', fontSize: '14px', fontWeight: '600', cursor: 'pointer',
                        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px',
                      }}
                    >
                      {getCapacityInfo(selectedEvent)?.isFull ? (
                        <><AlertCircle className="w-4 h-4" /> Join Waitlist</>
                      ) : (
                        <><CheckCircle className="w-4 h-4" /> Save My Spot</>
                      )}
                    </button>
                  )
                ) : (
                  <div style={{ textAlign: 'center', padding: '12px', background: '#f0fdf4', borderRadius: '10px', color: '#16a34a', fontWeight: '600', fontSize: '14px' }}>
                    <CheckCircle className="w-4 h-4 inline mr-1" style={{ verticalAlign: '-2px' }} /> You're Registered!
                  </div>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Paid Event Checkout Sheet */}
      <AnimatePresence>
        {checkoutEvent && (
          <PaidCheckoutSheet
            event={checkoutEvent}
            user={user}
            onClose={() => setCheckoutEvent(null)}
            onSuccess={() => { fetchEvents(); fetchMyEvents(); }}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
