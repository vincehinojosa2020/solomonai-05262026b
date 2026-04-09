import { useEffect, useMemo, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { ShoppingBag, Search, Plus, Minus, X, ArrowRight, Heart } from 'lucide-react';
import { API_URL, formatCurrency } from '@/lib/utils';
import { toast } from 'sonner';
import MerchRecommender from '@/components/MerchRecommender';
import SolomonPayForm from '@/components/SolomonPayForm';
import MultiPaymentSelector from '@/components/MultiPaymentSelector';

export default function PortalMerch() {
  const { tenant } = useOutletContext();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState('All');
  const [cartOpen, setCartOpen] = useState(false);
  const [cartItems, setCartItems] = useState([]);
  const [offeringAmount, setOfferingAmount] = useState(0);
  const [showPaymentStep, setShowPaymentStep] = useState(false);
  const [selectedPayment, setSelectedPayment] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [roundUp, setRoundUp] = useState(false);
  const [coverFees, setCoverFees] = useState(false);

  useEffect(() => {
    const fetchMerch = async () => {
      try {
        const productsRes = await fetch(`${API_URL}/portal/merch/products`);
        if (productsRes.ok) {
          const data = await productsRes.json();
          setProducts(data.products || []);
        }
      } catch (error) {
        console.error('Failed to load merch', error);
      } finally {
        setLoading(false);
      }
    };
    fetchMerch();
  }, []);

  const categories = useMemo(() => {
    const cats = new Set(['All']);
    products.forEach((product) => {
      if (product.category) cats.add(product.category);
    });
    return Array.from(cats);
  }, [products]);

  const filteredProducts = useMemo(() => {
    return products.filter((product) => {
      const matchesCategory = activeCategory === 'All' || product.category === activeCategory;
      const query = searchQuery.toLowerCase();
      const matchesSearch = !query || product.name?.toLowerCase().includes(query) || product.description?.toLowerCase().includes(query);
      return matchesCategory && matchesSearch;
    });
  }, [products, activeCategory, searchQuery]);

  const cartCount = cartItems.reduce((sum, item) => sum + item.quantity, 0);

  const addToCart = (product) => {
    setCartItems((prev) => {
      const existing = prev.find((item) => item.id === product.id);
      if (existing) {
        return prev.map((item) => item.id === product.id ? { ...item, quantity: item.quantity + 1 } : item);
      }
      return [...prev, { ...product, quantity: 1 }];
    });
    setCartOpen(true);
  };

  const updateQuantity = (productId, delta) => {
    setCartItems((prev) => {
      return prev
        .map((item) => item.id === productId ? { ...item, quantity: Math.max(item.quantity + delta, 0) } : item)
        .filter((item) => item.quantity > 0);
    });
  };

  const cartTotal = cartItems.reduce((sum, item) => sum + item.price * item.quantity, 0);
  const subtotalWithOffering = cartTotal + offeringAmount;
  const roundUpAmount = roundUp ? Math.ceil(subtotalWithOffering) - subtotalWithOffering : 0;
  const preFeesTotal = subtotalWithOffering + roundUpAmount;
  const processingFee = coverFees ? Math.round((preFeesTotal * 0.019 + 0.30) * 100) / 100 : 0;
  const orderTotal = Math.round((preFeesTotal + processingFee) * 100) / 100;

  const checkout = async () => {
    if (cartItems.length === 0) {
      toast.error('Your cart is empty');
      return;
    }
    // If saved card selected, process directly
    if (selectedPayment?.type === 'card_on_file' && selectedPayment?.token) {
      setProcessing(true);
      try {
        const token = sessionStorage.getItem('session_token');
        const payRes = await fetch(`${API_URL}/solomonpay/process`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
          body: JSON.stringify({
            amount: orderTotal,
            payment_method_type: 'card',
            token: selectedPayment.token,
            cover_fees: coverFees,
            description: `Merch order - ${cartItems.map(i => i.name).join(', ')}`,
            fund_name: 'Merch Revenue',
          }),
        });
        if (!payRes.ok) throw new Error('Payment failed');
        const res = await fetch(`${API_URL}/portal/merch/orders`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
          body: JSON.stringify({
            items: cartItems.map((item) => ({ product_id: item.id, name: item.name, price: item.price, quantity: item.quantity, image_url: item.image_url })),
            offering_amount: offeringAmount,
          }),
        });
        if (res.ok) {
          toast.success(`Order placed! Charged ${selectedPayment.card_brand} ••••${selectedPayment.card_last_four}`);
          setCartItems([]); setOfferingAmount(0); setCartOpen(false); setShowPaymentStep(false); setRoundUp(false); setCoverFees(false);
        } else throw new Error('Order failed');
      } catch { toast.error('Unable to place order'); }
      setProcessing(false);
      return;
    }
    // Otherwise show card entry form
    setShowPaymentStep(true);
  };

  const handleMerchPaymentSuccess = async (cardData) => {
    try {
      const payRes = await fetch(`${API_URL}/solomonpay/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...cardData,
          amount: orderTotal,
          context: 'merch_order',
          description: `Merch order - ${cartItems.map(i => i.name).join(', ')}`,
        }),
      });
      if (!payRes.ok) throw new Error('Payment failed');

      const res = await fetch(`${API_URL}/portal/merch/orders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          items: cartItems.map((item) => ({
            product_id: item.id, name: item.name, price: item.price,
            quantity: item.quantity, image_url: item.image_url
          })),
          offering_amount: offeringAmount
        })
      });
      if (res.ok) {
        toast.success(offeringAmount > 0 ? 'Order placed with offering! God bless!' : 'Order placed!');
        setCartItems([]); setOfferingAmount(0); setCartOpen(false); setShowPaymentStep(false);
      } else {
        throw new Error('Order failed');
      }
    } catch (error) {
      toast.error('Unable to place order');
      setShowPaymentStep(false);
    }
  };

  return (
    <div className="portal-merch" data-testid="portal-merch-page">
      <div className="portal-merch-header">
        <div>
          <span className="portal-tag">Shop</span>
          <h1>{tenant?.name || 'Abundant'} Store</h1>
          <p>Rep your church with exclusive merch, apparel, and accessories.</p>
          <div className="portal-merch-delivery" data-testid="merch-delivery-note">
            Free pickup available at {tenant?.city || 'church'} campus.
          </div>
        </div>
        <button
          className="portal-merch-cart-btn"
          onClick={() => setCartOpen(true)}
          data-testid="merch-cart-button"
        >
          <ShoppingBag className="w-4 h-4" /> Cart ({cartCount})
        </button>
      </div>

      <div className="portal-merch-controls">
        <div className="portal-merch-search">
          <Search className="w-4 h-4" />
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search merch"
            data-testid="merch-search-input"
          />
        </div>
        <div className="portal-merch-categories" data-testid="merch-categories">
          {categories.map((category) => (
            <button
              key={category}
              className={`portal-merch-category ${activeCategory === category ? 'active' : ''}`}
              onClick={() => setActiveCategory(category)}
              data-testid={`merch-category-${category.toLowerCase().replace(/\s+/g, '-')}`}
            >
              {category}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="portal-merch-empty" data-testid="merch-loading">Loading merch...</div>
      ) : filteredProducts.length === 0 ? (
        <div className="portal-merch-empty" data-testid="merch-empty">No merch available yet.</div>
      ) : (
        <div className="portal-merch-grid" data-testid="merch-product-grid">
          {filteredProducts.map((product) => (
            <div key={product.id} className="portal-merch-card" data-testid={`merch-product-${product.id}`}
            >
              <div className="portal-merch-image">
                <img src={product.image_url || 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=900&q=80'} alt={product.name} />
                {product.is_featured && <span className="portal-merch-badge">Featured</span>}
              </div>
              <div className="portal-merch-body">
                <h3>{product.name}</h3>
                <p>{product.description || 'Exclusive merch item'}</p>
                <div className="portal-merch-meta">
                  <span>{formatCurrency(product.price || 0)}</span>
                  <span>{product.category || 'General'}</span>
                </div>
                <button
                  className="portal-merch-add"
                  onClick={() => addToCart(product)}
                  data-testid={`merch-add-${product.id}`}
                >
                  Add to cart
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {cartOpen && (
        <div className="portal-merch-cart" data-testid="merch-cart">
          <div className="portal-merch-cart-header">
            <h3>Your Cart</h3>
            <button onClick={() => setCartOpen(false)} data-testid="merch-cart-close">
              <X className="w-4 h-4" />
            </button>
          </div>
          {cartItems.length === 0 ? (
            <div className="portal-merch-empty" data-testid="merch-cart-empty">Your cart is empty.</div>
          ) : (
            <div className="portal-merch-cart-items">
              {cartItems.map((item) => (
                <div key={item.id} className="portal-merch-cart-item" data-testid={`merch-cart-item-${item.id}`}>
                  <img src={item.image_url || 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=900&q=80'} alt={item.name} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <strong style={{ display: 'block', marginBottom: 4 }}>{item.name}</strong>
                    <span style={{ color: '#64748b', fontSize: 13 }}>{formatCurrency(item.price)}</span>
                  </div>
                  <div className="portal-merch-qty">
                    <button onClick={() => updateQuantity(item.id, -1)} data-testid={`merch-qty-minus-${item.id}`}>
                      <Minus className="w-3 h-3" />
                    </button>
                    <span>{item.quantity}</span>
                    <button onClick={() => updateQuantity(item.id, 1)} data-testid={`merch-qty-plus-${item.id}`}>
                      <Plus className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Giving Moment — Frank Luntz Style */}
          <div className="portal-merch-offering" data-testid="merch-offering-section">
            <div className="offering-header">
              <Heart className="w-4 h-4" />
              <span className="offering-label">You're already investing in something you believe in.</span>
            </div>
            <p className="offering-subtitle">
              Why not make it count twice? Add a tithe or offering and turn this purchase into a kingdom investment.
            </p>
            <div className="offering-amounts">
              {[10, 25, 50, 100].map((amount) => (
                <button
                  key={amount}
                  className={`offering-btn ${offeringAmount === amount ? 'active' : ''}`}
                  onClick={() => setOfferingAmount(offeringAmount === amount ? 0 : amount)}
                  data-testid={`merch-offering-${amount}`}
                >
                  ${amount}
                </button>
              ))}
              <button
                className={`offering-btn custom ${offeringAmount > 0 && ![10, 25, 50, 100].includes(offeringAmount) ? 'active' : ''}`}
                onClick={() => {
                  const custom = prompt('Enter your gift amount:');
                  if (custom && !isNaN(parseFloat(custom)) && parseFloat(custom) > 0) {
                    setOfferingAmount(parseFloat(custom));
                  }
                }}
                data-testid="merch-offering-custom"
              >
                Other
              </button>
              <button
                className={`offering-btn skip ${offeringAmount === 0 ? 'active' : ''}`}
                onClick={() => setOfferingAmount(0)}
                data-testid="merch-offering-skip"
              >
                Not today
              </button>
            </div>
            {offeringAmount > 0 && (
              <div className="offering-selected" style={{ fontStyle: 'italic' }}>
                <span>{formatCurrency(offeringAmount)} added — generosity looks good on you.</span>
                <button onClick={() => setOfferingAmount(0)} className="offering-remove">Remove</button>
              </div>
            )}
          </div>

          <div className="portal-merch-cart-footer">
            {/* Round Up — Luntz Style */}
            {cartTotal > 0 && Math.ceil(subtotalWithOffering) !== subtotalWithOffering && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 8, marginBottom: 8, cursor: 'pointer' }}
                onClick={() => setRoundUp(!roundUp)} data-testid="merch-roundup-toggle"
              >
                <div style={{
                  width: 18, height: 18, borderRadius: 4, border: `2px solid ${roundUp ? '#16a34a' : '#d1d5db'}`,
                  background: roundUp ? '#16a34a' : '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center',
                  transition: 'all 0.2s', flexShrink: 0
                }}>
                  {roundUp && <span style={{ color: '#fff', fontSize: 11, fontWeight: 700 }}>&#10003;</span>}
                </div>
                <div style={{ flex: 1 }}>
                  <p style={{ fontSize: 12, fontWeight: 700, color: '#166534', margin: 0 }}>
                    Round up to {formatCurrency(Math.ceil(subtotalWithOffering))}
                  </p>
                  <p style={{ fontSize: 10, color: '#4ade80', margin: 0 }}>
                    Small change, big kingdom impact.
                  </p>
                </div>
              </div>
            )}

            {/* Cover Fees — Luntz Style */}
            {preFeesTotal > 0 && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', background: coverFees ? '#eff6ff' : '#f8fafc', border: `1px solid ${coverFees ? '#93c5fd' : '#e2e8f0'}`, borderRadius: 8, marginBottom: 10, cursor: 'pointer', transition: 'all 0.2s' }}
                onClick={() => setCoverFees(!coverFees)} data-testid="merch-cover-fees-toggle"
              >
                <div style={{
                  width: 18, height: 18, borderRadius: 4, border: `2px solid ${coverFees ? '#2563eb' : '#d1d5db'}`,
                  background: coverFees ? '#2563eb' : '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center',
                  transition: 'all 0.2s', flexShrink: 0
                }}>
                  {coverFees && <span style={{ color: '#fff', fontSize: 11, fontWeight: 700 }}>&#10003;</span>}
                </div>
                <div style={{ flex: 1 }}>
                  <p style={{ fontSize: 12, fontWeight: 700, color: coverFees ? '#1e40af' : '#374151', margin: 0 }}>
                    Cover the fee ({formatCurrency(Math.round((preFeesTotal * 0.019 + 0.30) * 100) / 100)})
                  </p>
                  <p style={{ fontSize: 10, color: coverFees ? '#60a5fa' : '#9ca3af', margin: 0 }}>
                    100% of your generosity reaches the church. Not one penny lost.
                  </p>
                </div>
              </div>
            )}

            <div className="cart-line">
              <span>Subtotal</span>
              <span>{formatCurrency(cartTotal)}</span>
            </div>
            {offeringAmount > 0 && (
              <div className="cart-line offering" style={{ color: '#d97706', fontWeight: 600 }}>
                <span>Your Tithe &amp; Offering</span>
                <span>{formatCurrency(offeringAmount)}</span>
              </div>
            )}
            {roundUp && roundUpAmount > 0 && (
              <div className="cart-line" style={{ color: '#16a34a', fontWeight: 600 }}>
                <span>Round Up Gift</span>
                <span>{formatCurrency(roundUpAmount)}</span>
              </div>
            )}
            {coverFees && processingFee > 0 && (
              <div className="cart-line" style={{ color: '#2563eb', fontWeight: 600 }}>
                <span>Processing Fee Covered</span>
                <span>{formatCurrency(processingFee)}</span>
              </div>
            )}
            <div className="cart-line total">
              <span>Total</span>
              <strong data-testid="merch-cart-total">{formatCurrency(orderTotal)}</strong>
            </div>
            {showPaymentStep ? (
              <div style={{ padding: '0 4px' }}>
                <SolomonPayForm
                  amount={orderTotal}
                  onSuccess={handleMerchPaymentSuccess}
                  onCancel={() => setShowPaymentStep(false)}
                  context="merch_order"
                />
              </div>
            ) : (
              <div className="space-y-3" style={{ padding: '0 4px' }}>
                <MultiPaymentSelector
                  amount={cartTotal}
                  onSelect={(pm) => setSelectedPayment(pm)}
                  showCash={false}
                />
                <button
                  className="portal-merch-checkout"
                  onClick={checkout}
                  disabled={processing}
                  data-testid="merch-checkout-btn"
                  style={processing ? { opacity: 0.6, cursor: 'not-allowed' } : {}}
                >
                  {processing ? 'Processing...' : (offeringAmount > 0 ? 'Pay with SolomonPay & Give' : 'Pay with SolomonPay')}
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Merch Recommender Chatbot */}
      <MerchRecommender />
    </div>
  );
}
