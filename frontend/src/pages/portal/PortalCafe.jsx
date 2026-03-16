import { useEffect, useMemo, useState } from 'react';
import { Coffee, Search, Plus, Minus, X, ArrowRight, Clock } from 'lucide-react';
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
  const [offeringAmount, setOfferingAmount] = useState(0); // New: Offering amount

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
    items.forEach((item) => {
      if (item.category) set.add(item.category);
    });
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
  const orderTotal = cartTotal + offeringAmount; // Total including offering

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
    if (!pickupTime) {
      toast.error('Select a pickup time');
      return;
    }
    if (cartItems.length === 0) {
      toast.error('Your cart is empty');
      return;
    }
    try {
      const res = await fetch(`${API_URL}/portal/cafe/orders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        
        body: JSON.stringify({
          pickup_time: pickupTime,
          notes: orderNotes,
          items: cartItems.map((item) => ({
            item_id: item.id,
            name: item.name,
            price: item.price,
            quantity: item.quantity,
            image_url: item.image_url,
          }))
        })
      });
      if (res.ok) {
        toast.success('Cafe order placed!');
        setCartItems([]);
        setCartOpen(false);
        setPickupTime('');
        setOrderNotes('');
      } else {
        toast.error('Unable to place order');
      }
    } catch (error) {
      toast.error('Unable to place order');
    }
  };

  return (
    <div className="portal-cafe" data-testid="portal-cafe-page">
      <div className="portal-cafe-header">
        <div>
          <span className="portal-tag">Abundant Cafe</span>
          <h1>Order Coffee for Sunday</h1>
          <p>Skip the line and schedule pickup before service starts.</p>
          {settings && (
            <div className="portal-cafe-info" data-testid="cafe-info">
              <span><Clock className="w-4 h-4" /> {settings.pickup_start} - {settings.pickup_end}</span>
              <span>{settings.location || 'Lobby pickup counter'}</span>
            </div>
          )}
        </div>
        <button className="portal-cafe-cart-btn" onClick={() => setCartOpen(true)} data-testid="cafe-cart-button">
          <Coffee className="w-4 h-4" /> Cart ({cartCount})
        </button>
      </div>

      {settings && settings.is_active === false && (
        <div className="portal-cafe-closed" data-testid="cafe-closed">Cafe ordering is currently paused.</div>
      )}

      <div className="portal-cafe-controls">
        <div className="portal-cafe-search">
          <Search className="w-4 h-4" />
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search menu"
            data-testid="cafe-search-input"
          />
        </div>
        <div className="portal-cafe-categories" data-testid="cafe-categories">
          {categories.map((category) => (
            <button
              key={category}
              className={`portal-cafe-category ${activeCategory === category ? 'active' : ''}`}
              onClick={() => setActiveCategory(category)}
              data-testid={`cafe-category-${category.toLowerCase().replace(/\s+/g, '-')}`}
            >
              {category}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="portal-cafe-empty" data-testid="cafe-loading">Loading menu...
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="portal-cafe-empty" data-testid="cafe-empty">No cafe items available yet.</div>
      ) : (
        <div className="portal-cafe-grid" data-testid="cafe-grid">
          {filteredItems.map((item) => (
            <div key={item.id} className="portal-cafe-card" data-testid={`cafe-item-${item.id}`}>
              <div className="portal-cafe-image">
                <img src={item.image_url || 'https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=900&q=80'} alt={item.name} />
                {item.is_featured && <span className="portal-cafe-badge">Featured</span>}
              </div>
              <div className="portal-cafe-body">
                <h3>{item.name}</h3>
                <p>{item.description || 'Cafe favorite'}
                </p>
                <div className="portal-cafe-meta">
                  <span>{formatCurrency(item.price || 0)}</span>
                  <span>{item.category || 'General'}</span>
                </div>
                <button
                  className="portal-cafe-add"
                  onClick={() => addToCart(item)}
                  data-testid={`cafe-add-${item.id}`}
                >
                  Add to order
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {cartOpen && (
        <div className="portal-cafe-cart" data-testid="cafe-cart">
          <div className="portal-cafe-cart-header">
            <h3>Your Cafe Order</h3>
            <button onClick={() => setCartOpen(false)} data-testid="cafe-cart-close">
              <X className="w-4 h-4" />
            </button>
          </div>
          {cartItems.length === 0 ? (
            <div className="portal-cafe-empty" data-testid="cafe-cart-empty">Your cart is empty.</div>
          ) : (
            <div className="portal-cafe-cart-items">
              {cartItems.map((item) => (
                <div key={item.id} className="portal-cafe-cart-item" data-testid={`cafe-cart-item-${item.id}`}>
                  <img src={item.image_url || 'https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=900&q=80'} alt={item.name} />
                  <div>
                    <strong>{item.name}</strong>
                    <span>{formatCurrency(item.price)}</span>
                  </div>
                  <div className="portal-cafe-qty">
                    <button onClick={() => updateQuantity(item.id, -1)} data-testid={`cafe-qty-minus-${item.id}`}>
                      <Minus className="w-3 h-3" />
                    </button>
                    <span>{item.quantity}</span>
                    <button onClick={() => updateQuantity(item.id, 1)} data-testid={`cafe-qty-plus-${item.id}`}>
                      <Plus className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
          <div className="portal-cafe-pickup">
            <label htmlFor="pickup-time">Pickup time</label>
            <select
              id="pickup-time"
              value={pickupTime}
              onChange={(e) => setPickupTime(e.target.value)}
              data-testid="cafe-pickup-select"
            >
              <option value="">Select a pickup time</option>
              {pickupSlots.map((slot) => (
                <option key={slot} value={slot}>{slot}</option>
              ))}
            </select>
          </div>
          <div className="portal-cafe-notes">
            <label htmlFor="cafe-notes">Order notes</label>
            <textarea
              id="cafe-notes"
              value={orderNotes}
              onChange={(e) => setOrderNotes(e.target.value)}
              placeholder="Any special instructions?"
              rows={2}
              data-testid="cafe-notes-input"
            />
          </div>

          {/* Giving Moment - "While You're Here" */}
          <div className="portal-cafe-offering" data-testid="cafe-giving-nudge">
            <div className="offering-header">
              <span className="offering-label">While You're Here</span>
              <span className="offering-subtitle">Would you like to add a gift to your church?</span>
            </div>
            <div className="offering-amounts">
              {[5, 10, 20, 100].map((amount) => (
                <button
                  key={amount}
                  className={`offering-btn ${offeringAmount === amount ? 'active' : ''}`}
                  onClick={() => setOfferingAmount(offeringAmount === amount ? 0 : amount)}
                  data-testid={`cafe-offering-${amount}`}
                >
                  ${amount}
                </button>
              ))}
              <button
                className={`offering-btn custom ${offeringAmount > 0 && ![5, 10, 20, 100].includes(offeringAmount) ? 'active' : ''}`}
                onClick={() => {
                  const custom = prompt('Enter custom gift amount:');
                  if (custom && !isNaN(parseFloat(custom))) {
                    setOfferingAmount(parseFloat(custom));
                  }
                }}
                data-testid="cafe-offering-custom"
              >
                Custom
              </button>
              <button
                className={`offering-btn skip ${offeringAmount === 0 ? 'active' : ''}`}
                onClick={() => setOfferingAmount(0)}
                data-testid="cafe-offering-skip"
              >
                Skip
              </button>
            </div>
            {offeringAmount > 0 && (
              <div className="offering-selected">
                <span>Gift to Church: {formatCurrency(offeringAmount)}</span>
                <button onClick={() => setOfferingAmount(0)} className="offering-remove">Remove</button>
              </div>
            )}
          </div>

          <div className="portal-cafe-cart-footer">
            <div className="cart-subtotal">
              <span>Order Subtotal</span>
              <span>{formatCurrency(cartTotal)}</span>
            </div>
            {offeringAmount > 0 && (
              <div className="cart-offering">
                <span>Gift to Church</span>
                <span>{formatCurrency(offeringAmount)}</span>
              </div>
            )}
            <div className="cart-total">
              <span>Total</span>
              <strong data-testid="cafe-cart-total">{formatCurrency(orderTotal)}</strong>
            </div>
            <button className="portal-cafe-checkout" onClick={placeOrder} data-testid="cafe-checkout-btn">
              {offeringAmount > 0 ? 'Place Order & Give' : 'Place Order'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
