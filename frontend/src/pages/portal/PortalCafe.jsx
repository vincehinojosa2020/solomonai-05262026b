import { useEffect, useMemo, useState } from 'react';
import { Search, Plus, Minus, X, ArrowRight, Clock, ShoppingCart, MapPin, ChevronRight } from 'lucide-react';
import { useOutletContext } from 'react-router-dom';
import { API_URL, formatCurrency } from '@/lib/utils';
import { toast } from 'sonner';

const parseTime = (value) => {
  if (!value) return null;
  const parts = value.trim().split(' ');
  const timePart = parts[0];
  const period = (parts[1] || '').toUpperCase();
  const [hoursStr, minutesStr] = timePart.split(':');
  let hours = Number(hoursStr);
  const minutes = Number(minutesStr || 0);
  if (Number.isNaN(hours) || Number.isNaN(minutes)) return null;
  if (period === 'PM' && hours < 12) hours += 12;
  if (period === 'AM' && hours === 12) hours = 0;
  return hours * 60 + minutes;
};

const formatSlot = (minutes) => {
  const hours24 = Math.floor(minutes / 60) % 24;
  const minutesPart = minutes % 60;
  const period = hours24 >= 12 ? 'PM' : 'AM';
  const hours12 = hours24 % 12 === 0 ? 12 : hours24 % 12;
  return `${hours12}:${minutesPart.toString().padStart(2, '0')} ${period}`;
};

export default function PortalCafe() {
  const { tenant } = useOutletContext();
  const [items, setItems] = useState([]);
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState('All');
  const [cartOpen, setCartOpen] = useState(false);
  const [cartItems, setCartItems] = useState([]);
  const [pickupTime, setPickupTime] = useState('');
  const [orderNotes, setOrderNotes] = useState('');
  const [offeringAmount, setOfferingAmount] = useState(0);

  useEffect(() => {
    const fetchCafe = async () => {
      try {
        const [itemsRes, settingsRes] = await Promise.all([
          fetch(`${API_URL}/portal/cafe/items`),
          fetch(`${API_URL}/portal/cafe/settings`)
        ]);
        if (itemsRes.ok) {
          const data = await itemsRes.json();
          setItems(data.items || []);
        }
        if (settingsRes.ok) {
          const data = await settingsRes.json();
          setSettings(data.settings || null);
        }
      } catch (error) {
        console.error('Failed to load cafe', error);
      } finally {
        setLoading(false);
      }
    };
    fetchCafe();
  }, []);

  const categories = useMemo(() => {
    const set = new Set(['All']);
    items.forEach((item) => { if (item.category) set.add(item.category); });
    return Array.from(set);
  }, [items]);

  const filteredItems = useMemo(() => {
    return items.filter((item) => {
      const matchesCategory = activeCategory === 'All' || item.category === activeCategory;
      const query = searchQuery.toLowerCase();
      const matchesSearch = !query || item.name?.toLowerCase().includes(query) || item.description?.toLowerCase().includes(query);
      return matchesCategory && matchesSearch;
    });
  }, [items, activeCategory, searchQuery]);

  const pickupSlots = useMemo(() => {
    if (!settings) return [];
    const start = parseTime(settings.pickup_start);
    const end = parseTime(settings.pickup_end);
    const interval = settings.pickup_interval_minutes || 15;
    if (start === null || end === null) return [];
    const slots = [];
    for (let time = start; time <= end; time += interval) {
      slots.push(formatSlot(time));
    }
    return slots;
  }, [settings]);

  const cartCount = cartItems.reduce((sum, item) => sum + item.quantity, 0);
  const cartTotal = cartItems.reduce((sum, item) => sum + item.price * item.quantity, 0);
  const orderTotal = cartTotal + offeringAmount;

  const addToCart = (item) => {
    setCartItems((prev) => {
      const existing = prev.find((entry) => entry.id === item.id);
      if (existing) {
        return prev.map((entry) => entry.id === item.id ? { ...entry, quantity: entry.quantity + 1 } : entry);
      }
      return [...prev, { ...item, quantity: 1 }];
    });
    setCartOpen(true);
  };

  const updateQuantity = (itemId, delta) => {
    setCartItems((prev) => {
      return prev
        .map((entry) => entry.id === itemId ? { ...entry, quantity: Math.max(entry.quantity + delta, 0) } : entry)
        .filter((entry) => entry.quantity > 0);
    });
  };

  const placeOrder = async () => {
    if (!pickupTime) { toast.error('Select a pickup time'); return; }
    if (cartItems.length === 0) { toast.error('Your cart is empty'); return; }
    try {
      const res = await fetch(`${API_URL}/portal/cafe/orders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pickup_time: pickupTime,
          notes: orderNotes,
          items: cartItems.map((item) => ({
            item_id: item.id, name: item.name, price: item.price,
            quantity: item.quantity, image_url: item.image_url,
          }))
        })
      });
      if (res.ok) {
        toast.success('Order placed successfully');
        setCartItems([]); setCartOpen(false); setPickupTime(''); setOrderNotes('');
      } else {
        toast.error('Unable to place order');
      }
    } catch { toast.error('Unable to place order'); }
  };

  return (
    <div style={{ maxWidth: 960, margin: '0 auto', padding: '32px 20px' }} data-testid="portal-cafe-page">
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 8 }}>
          <div>
            <p style={{ fontSize: 12, fontWeight: 600, letterSpacing: '0.05em', textTransform: 'uppercase', color: '#6b7280', marginBottom: 4 }}>Church Cafe</p>
            <h1 style={{ fontSize: 28, fontWeight: 700, color: '#111827', letterSpacing: '-0.02em', margin: 0 }} data-testid="cafe-title">
              Pre-order for Sunday
            </h1>
            <p style={{ fontSize: 14, color: '#6b7280', marginTop: 4, lineHeight: 1.5 }}>
              Skip the line. Schedule your pickup before service.
            </p>
          </div>
          <button
            onClick={() => setCartOpen(true)}
            style={{
              display: 'flex', alignItems: 'center', gap: 8, padding: '10px 20px',
              background: '#111827', color: 'white', border: 'none', borderRadius: 8,
              fontSize: 14, fontWeight: 600, cursor: 'pointer', position: 'relative'
            }}
            data-testid="cafe-cart-button"
          >
            <ShoppingCart style={{ width: 16, height: 16 }} />
            Cart
            {cartCount > 0 && (
              <span style={{
                position: 'absolute', top: -6, right: -6, width: 20, height: 20,
                background: '#3b82f6', borderRadius: '50%', fontSize: 11, fontWeight: 700,
                display: 'flex', alignItems: 'center', justifyContent: 'center'
              }}>{cartCount}</span>
            )}
          </button>
        </div>
        {settings && (
          <div style={{ display: 'flex', gap: 16, marginTop: 12 }} data-testid="cafe-info">
            <span style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: '#6b7280' }}>
              <Clock style={{ width: 14, height: 14 }} /> {settings.pickup_start} - {settings.pickup_end}
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: '#6b7280' }}>
              <MapPin style={{ width: 14, height: 14 }} /> {settings.location || 'Lobby pickup counter'}
            </span>
          </div>
        )}
      </div>

      {settings && settings.is_active === false && (
        <div style={{ padding: '16px 20px', background: '#fef3c7', border: '1px solid #fde68a', borderRadius: 8, fontSize: 14, color: '#92400e', marginBottom: 24 }} data-testid="cafe-closed">
          Cafe ordering is currently paused.
        </div>
      )}

      {/* Search & Categories */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 24, flexWrap: 'wrap', alignItems: 'center' }}>
        <div style={{ position: 'relative', flex: '1 1 240px' }}>
          <Search style={{ width: 16, height: 16, position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: '#9ca3af' }} />
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search menu..."
            style={{
              width: '100%', padding: '10px 12px 10px 36px', border: '1px solid #e5e7eb',
              borderRadius: 8, fontSize: 14, color: '#111827', background: '#ffffff',
              outline: 'none'
            }}
            data-testid="cafe-search-input"
          />
        </div>
        <div style={{ display: 'flex', gap: 4 }} data-testid="cafe-categories">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              style={{
                padding: '8px 16px', borderRadius: 6, border: '1px solid',
                borderColor: activeCategory === cat ? '#111827' : '#e5e7eb',
                background: activeCategory === cat ? '#111827' : '#ffffff',
                color: activeCategory === cat ? '#ffffff' : '#374151',
                fontSize: 13, fontWeight: 500, cursor: 'pointer', transition: 'all 0.15s'
              }}
              data-testid={`cafe-category-${cat.toLowerCase().replace(/\s+/g, '-')}`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Items Grid */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: 60, color: '#9ca3af' }} data-testid="cafe-loading">Loading menu...</div>
      ) : filteredItems.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 60, color: '#9ca3af' }} data-testid="cafe-empty">No items available.</div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }} data-testid="cafe-grid">
          {filteredItems.map((item) => (
            <div
              key={item.id}
              style={{
                border: '1px solid #e5e7eb', borderRadius: 10, overflow: 'hidden',
                background: '#ffffff', transition: 'box-shadow 0.2s'
              }}
              data-testid={`cafe-item-${item.id}`}
            >
              <div style={{ height: 160, overflow: 'hidden', position: 'relative' }}>
                <img
                  src={item.image_url || 'https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=900&q=80'}
                  alt={item.name}
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
                {item.is_featured && (
                  <span style={{
                    position: 'absolute', top: 10, left: 10, padding: '4px 10px',
                    background: '#111827', color: '#fff', borderRadius: 4,
                    fontSize: 11, fontWeight: 600, letterSpacing: '0.04em'
                  }}>FEATURED</span>
                )}
              </div>
              <div style={{ padding: 16 }}>
                <h3 style={{ fontSize: 16, fontWeight: 600, color: '#111827', margin: '0 0 4px 0' }}>{item.name}</h3>
                <p style={{ fontSize: 13, color: '#6b7280', margin: '0 0 12px 0', lineHeight: 1.4 }}>
                  {item.description || 'A cafe favorite'}
                </p>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: 16, fontWeight: 700, color: '#111827' }}>{formatCurrency(item.price || 0)}</span>
                  <button
                    onClick={() => addToCart(item)}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 6, padding: '8px 14px',
                      background: '#111827', color: '#fff', border: 'none', borderRadius: 6,
                      fontSize: 13, fontWeight: 600, cursor: 'pointer'
                    }}
                    data-testid={`cafe-add-${item.id}`}
                  >
                    Add <ArrowRight style={{ width: 14, height: 14 }} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Cart Sidebar */}
      {cartOpen && (
        <>
          <div
            style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.3)', zIndex: 50 }}
            onClick={() => setCartOpen(false)}
          />
          <div
            style={{
              position: 'fixed', top: 0, right: 0, bottom: 0, width: 420, maxWidth: '100vw',
              background: '#ffffff', zIndex: 51, display: 'flex', flexDirection: 'column',
              boxShadow: '-4px 0 24px rgba(0,0,0,0.08)'
            }}
            data-testid="cafe-cart"
          >
            {/* Cart Header */}
            <div style={{ padding: '20px 24px', borderBottom: '1px solid #e5e7eb', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <h3 style={{ fontSize: 18, fontWeight: 700, color: '#111827', margin: 0 }}>Your Order</h3>
              <button onClick={() => setCartOpen(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#6b7280' }} data-testid="cafe-cart-close">
                <X style={{ width: 20, height: 20 }} />
              </button>
            </div>

            {/* Cart Items */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '16px 24px' }}>
              {cartItems.length === 0 ? (
                <div style={{ textAlign: 'center', padding: 40, color: '#9ca3af' }} data-testid="cafe-cart-empty">
                  <ShoppingCart style={{ width: 32, height: 32, margin: '0 auto 12px', opacity: 0.4 }} />
                  <p style={{ fontSize: 14 }}>Your cart is empty</p>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {cartItems.map((item) => (
                    <div key={item.id} style={{
                      display: 'flex', alignItems: 'center', gap: 12, padding: '12px 0',
                      borderBottom: '1px solid #f3f4f6'
                    }} data-testid={`cafe-cart-item-${item.id}`}>
                      <img
                        src={item.image_url || 'https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=900&q=80'}
                        alt={item.name}
                        style={{ width: 56, height: 56, borderRadius: 8, objectFit: 'cover' }}
                      />
                      <div style={{ flex: 1 }}>
                        <p style={{ fontSize: 14, fontWeight: 600, color: '#111827', margin: 0 }}>{item.name}</p>
                        <p style={{ fontSize: 13, color: '#6b7280', margin: 0 }}>{formatCurrency(item.price)}</p>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, background: '#f3f4f6', borderRadius: 6, padding: '4px 8px' }}>
                        <button onClick={() => updateQuantity(item.id, -1)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#374151', padding: 2 }} data-testid={`cafe-qty-minus-${item.id}`}>
                          <Minus style={{ width: 14, height: 14 }} />
                        </button>
                        <span style={{ fontSize: 14, fontWeight: 600, minWidth: 20, textAlign: 'center' }}>{item.quantity}</span>
                        <button onClick={() => updateQuantity(item.id, 1)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#374151', padding: 2 }} data-testid={`cafe-qty-plus-${item.id}`}>
                          <Plus style={{ width: 14, height: 14 }} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Cart Footer */}
            <div style={{ padding: '20px 24px', borderTop: '1px solid #e5e7eb', background: '#f9fafb' }}>
              {/* Pickup Time */}
              <div style={{ marginBottom: 12 }}>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#374151', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Pickup Time
                </label>
                <select
                  value={pickupTime}
                  onChange={(e) => setPickupTime(e.target.value)}
                  style={{ width: '100%', padding: '10px 12px', border: '1px solid #e5e7eb', borderRadius: 6, fontSize: 14, background: '#fff' }}
                  data-testid="cafe-pickup-select"
                >
                  <option value="">Select time...</option>
                  {pickupSlots.map((slot) => (<option key={slot} value={slot}>{slot}</option>))}
                </select>
              </div>

              {/* Notes */}
              <div style={{ marginBottom: 16 }}>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#374151', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Notes
                </label>
                <textarea
                  value={orderNotes}
                  onChange={(e) => setOrderNotes(e.target.value)}
                  placeholder="Special instructions..."
                  rows={2}
                  style={{ width: '100%', padding: '10px 12px', border: '1px solid #e5e7eb', borderRadius: 6, fontSize: 14, resize: 'none', background: '#fff' }}
                  data-testid="cafe-notes-input"
                />
              </div>

              {/* Giving Section */}
              <div style={{ padding: '14px 16px', background: '#ffffff', border: '1px solid #e5e7eb', borderRadius: 8, marginBottom: 16 }} data-testid="cafe-giving-nudge">
                <p style={{ fontSize: 12, fontWeight: 600, color: '#374151', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Add a gift</p>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {[5, 10, 20, 50].map((amount) => (
                    <button
                      key={amount}
                      onClick={() => setOfferingAmount(offeringAmount === amount ? 0 : amount)}
                      style={{
                        padding: '6px 14px', borderRadius: 6, fontSize: 13, fontWeight: 600,
                        border: '1px solid', cursor: 'pointer',
                        borderColor: offeringAmount === amount ? '#111827' : '#e5e7eb',
                        background: offeringAmount === amount ? '#111827' : '#fff',
                        color: offeringAmount === amount ? '#fff' : '#374151'
                      }}
                      data-testid={`cafe-offering-${amount}`}
                    >
                      ${amount}
                    </button>
                  ))}
                  <button
                    onClick={() => setOfferingAmount(0)}
                    style={{
                      padding: '6px 14px', borderRadius: 6, fontSize: 13, fontWeight: 500,
                      border: '1px solid #e5e7eb', cursor: 'pointer',
                      background: offeringAmount === 0 ? '#f3f4f6' : '#fff',
                      color: '#6b7280'
                    }}
                    data-testid="cafe-offering-skip"
                  >
                    Skip
                  </button>
                </div>
              </div>

              {/* Totals */}
              <div style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14, color: '#6b7280', marginBottom: 4 }}>
                  <span>Subtotal</span>
                  <span>{formatCurrency(cartTotal)}</span>
                </div>
                {offeringAmount > 0 && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14, color: '#6b7280', marginBottom: 4 }}>
                    <span>Gift to Church</span>
                    <span>{formatCurrency(offeringAmount)}</span>
                  </div>
                )}
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 16, fontWeight: 700, color: '#111827', paddingTop: 8, borderTop: '1px solid #e5e7eb' }}>
                  <span>Total</span>
                  <span data-testid="cafe-cart-total">{formatCurrency(orderTotal)}</span>
                </div>
              </div>

              <button
                onClick={placeOrder}
                style={{
                  width: '100%', padding: '14px 0', background: '#111827', color: '#ffffff',
                  border: 'none', borderRadius: 8, fontSize: 15, fontWeight: 700,
                  cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8
                }}
                data-testid="cafe-checkout-btn"
              >
                Place Order <ChevronRight style={{ width: 16, height: 16 }} />
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
