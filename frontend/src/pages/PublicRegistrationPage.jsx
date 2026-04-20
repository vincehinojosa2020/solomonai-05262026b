import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Calendar, MapPin, Clock, Users, CheckCircle, Loader2, AlertCircle, Tag } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';
import { safeImgSrc } from '@/utils/sanitize';

export default function PublicRegistrationPage() {
  const { eventId } = useParams();
  const [event, setEvent] = useState(null);
  const [config, setConfig] = useState(null);
  const [spotsLeft, setSpotsLeft] = useState(null);
  const [isFull, setIsFull] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [submitResult, setSubmitResult] = useState(null);

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [selectedAddOns, setSelectedAddOns] = useState([]);
  const [customAnswers, setCustomAnswers] = useState({});
  const [promoCode, setPromoCode] = useState('');

  useEffect(() => { fetchEvent(); }, [eventId]);

  const fetchEvent = async () => {
    try {
      const res = await fetch(`${API_URL}/register/${eventId}`);
      if (res.ok) {
        const d = await res.json();
        setEvent(d.event);
        setConfig(d.config);
        setSpotsLeft(d.spots_left);
        setIsFull(d.is_full);
        // Auto-select required add-ons
        const requiredIds = (d.config?.add_ons || []).filter(a => a.required).map(a => a.id);
        if (requiredIds.length > 0) setSelectedAddOns(prev => [...new Set([...prev, ...requiredIds])]);
      }
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const toggleAddOn = (addonId) => {
    setSelectedAddOns(prev =>
      prev.includes(addonId) ? prev.filter(id => id !== addonId) : [...prev, addonId]
    );
  };

  const calculateTotal = () => {
    let total = 0;
    if (config?.pricing?.enabled) total += config.pricing.amount || 0;
    if (config?.add_ons) {
      for (const addon of config.add_ons) {
        if (selectedAddOns.includes(addon.id)) total += addon.price || 0;
      }
    }
    return total;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name || !email) { toast.error('Name and email are required'); return; }
    setSubmitting(true);
    try {
      const res = await fetch(`${API_URL}/register/${eventId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          registrants: [{ name, email, phone }],
          add_ons: selectedAddOns,
          custom_answers: customAnswers,
          promo_code: promoCode,
        })
      });
      const d = await res.json();
      if (res.ok) {
        setSubmitted(true);
        setSubmitResult(d);
      } else {
        toast.error(d.detail || 'Registration failed');
      }
    } catch (err) { toast.error('Registration failed'); }
    finally { setSubmitting(false); }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!event) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h2 className="text-lg font-semibold text-slate-700">Event not found</h2>
          <p className="text-sm text-slate-400">This registration link may be invalid or expired.</p>
        </div>
      </div>
    );
  }

  if (submitted) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4" data-testid="reg-success">
        <div className="bg-white rounded-2xl shadow-lg p-8 max-w-md w-full text-center">
          <CheckCircle className="w-16 h-16 text-emerald-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-slate-900 mb-2">
            {submitResult?.status === 'waitlisted' ? 'Added to Waitlist' : 'Registration Confirmed!'}
          </h2>
          <p className="text-slate-500 mb-4">{submitResult?.message}</p>
          {submitResult?.total_amount > 0 && (
            <div className="bg-slate-50 rounded-lg p-3 mb-4">
              <p className="text-sm text-slate-600">Total: <span className="font-bold text-slate-800">${submitResult.total_amount}</span></p>
              <p className="text-xs text-amber-600 mt-1">Payment will be collected via SolomonPay (pending)</p>
            </div>
          )}
          <p className="text-xs text-slate-400">A confirmation will be sent to {email}</p>
        </div>
      </div>
    );
  }

  const total = calculateTotal();
  const eventDate = event.start_datetime ? new Date(event.start_datetime) : null;

  return (
    <div className="min-h-screen bg-slate-50 p-4" data-testid="public-reg-page">
      <div className="max-w-2xl mx-auto">
        {/* Event Header */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden mb-6" data-testid="reg-event-header">
          {event.cover_image_url && (
            <img src={safeImgSrc(event.cover_image_url)} alt={event.name} className="w-full h-48 object-cover" />
          )}
          <div className="p-6">
            <h1 className="text-2xl font-bold text-slate-900 mb-2">{event.name}</h1>
            {event.description && <p className="text-sm text-slate-600 mb-4">{event.description}</p>}
            <div className="flex flex-wrap items-center gap-4 text-sm text-slate-500">
              {eventDate && (
                <span className="flex items-center gap-1.5">
                  <Calendar className="w-4 h-4" />
                  {eventDate.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}
                </span>
              )}
              {event.location && (
                <span className="flex items-center gap-1.5"><MapPin className="w-4 h-4" />{event.location}</span>
              )}
              {spotsLeft !== null && (
                <Badge variant="outline" className={isFull ? 'text-red-600 border-red-200' : 'text-emerald-600 border-emerald-200'}>
                  <Users className="w-3.5 h-3.5 mr-1" />
                  {isFull ? 'Full — Waitlist Available' : `${spotsLeft} spots remaining`}
                </Badge>
              )}
            </div>
          </div>
        </div>

        {/* Registration Form */}
        <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-5" data-testid="reg-form">
          <h2 className="text-lg font-bold text-slate-900">Register</h2>

          {/* Contact Info */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <Label>Full Name *</Label>
              <Input value={name} onChange={e => setName(e.target.value)} placeholder="Your full name" required data-testid="reg-name" />
            </div>
            <div>
              <Label>Email *</Label>
              <Input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@email.com" required data-testid="reg-email" />
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <Label>Phone</Label>
              <Input value={phone} onChange={e => setPhone(e.target.value)} placeholder="(555) 000-0000" data-testid="reg-phone" />
            </div>
          </div>

          {/* Custom Questions */}
          {config?.custom_questions?.length > 0 && (
            <div className="space-y-3 border-t border-slate-100 pt-4">
              <h3 className="text-sm font-semibold text-slate-700">Additional Information</h3>
              {config.custom_questions.map(q => (
                <div key={q.id}>
                  <Label>{q.label} {q.required && '*'}</Label>
                  {q.type === 'select' ? (
                    <select className="w-full rounded-md border border-slate-200 p-2 text-sm"
                      value={customAnswers[q.id] || ''}
                      onChange={e => setCustomAnswers({ ...customAnswers, [q.id]: e.target.value })}
                      required={q.required} data-testid={`reg-q-${q.id}`}>
                      <option value="">Select...</option>
                      {(q.options || []).map(opt => <option key={opt} value={opt}>{opt}</option>)}
                    </select>
                  ) : q.type === 'checkbox' ? (
                    <label className="flex items-center gap-2 text-sm">
                      <input type="checkbox" checked={customAnswers[q.id] || false}
                        onChange={e => setCustomAnswers({ ...customAnswers, [q.id]: e.target.checked })} data-testid={`reg-q-${q.id}`} />
                      Yes
                    </label>
                  ) : (
                    <Input value={customAnswers[q.id] || ''}
                      onChange={e => setCustomAnswers({ ...customAnswers, [q.id]: e.target.value })}
                      required={q.required} data-testid={`reg-q-${q.id}`} />
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Add-ons */}
          {config?.add_ons?.length > 0 && (
            <div className="space-y-3 border-t border-slate-100 pt-4">
              <h3 className="text-sm font-semibold text-slate-700">Add-ons</h3>
              {config.add_ons.map(addon => {
                const isRequired = addon.required;
                const isSelected = selectedAddOns.includes(addon.id);
                return (
                  <label
                    key={addon.id}
                    className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition-all border ${
                      isSelected ? 'bg-blue-50 border-blue-200' : 'bg-slate-50 border-transparent hover:bg-slate-100'
                    }`}
                    data-testid={`addon-${addon.id}`}
                  >
                    <div className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={isSelected || isRequired}
                        onChange={() => !isRequired && toggleAddOn(addon.id)}
                        disabled={isRequired}
                        className="rounded w-4 h-4"
                      />
                      <div>
                        <p className="text-sm font-medium text-slate-700">
                          {addon.name}
                          {isRequired && <span className="text-[10px] ml-1.5 text-red-500 font-medium uppercase">Required</span>}
                        </p>
                        {addon.description && <p className="text-xs text-slate-400 mt-0.5">{addon.description}</p>}
                      </div>
                    </div>
                    <span className="text-sm font-semibold text-slate-700">
                      {addon.price > 0 ? `$${addon.price}` : 'Free'}
                    </span>
                  </label>
                );
              })}
            </div>
          )}

          {/* Promo Code */}
          {config?.pricing?.enabled && (
            <div className="border-t border-slate-100 pt-4">
              <Label className="text-xs text-slate-500 flex items-center gap-1"><Tag className="w-3 h-3" /> Promo Code</Label>
              <Input value={promoCode} onChange={e => setPromoCode(e.target.value.toUpperCase())}
                placeholder="Enter promo code" className="mt-1 font-mono" data-testid="reg-promo" />
            </div>
          )}

          {/* Total */}
          {total > 0 && (
            <div className="bg-blue-50 rounded-xl p-4 flex items-center justify-between" data-testid="reg-total">
              <span className="text-sm font-medium text-slate-700">Total</span>
              <span className="text-xl font-bold text-blue-700">${total.toFixed(2)}</span>
            </div>
          )}

          {/* Submit */}
          <Button type="submit" className="w-full h-12 text-base bg-blue-600 hover:bg-blue-700" disabled={submitting} data-testid="reg-submit">
            {submitting ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : <CheckCircle className="w-5 h-5 mr-2" />}
            {isFull ? 'Join Waitlist' : 'Complete Registration'}
          </Button>

          {total > 0 && (
            <p className="text-xs text-center text-slate-400">Payment processed securely via SolomonPay</p>
          )}
        </form>
      </div>
    </div>
  );
}
