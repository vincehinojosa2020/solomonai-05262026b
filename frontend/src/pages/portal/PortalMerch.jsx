import { useEffect, useMemo, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { ShoppingBag, Search, Plus, Minus, X, ArrowRight, Heart } from 'lucide-react';
import { API_URL, formatCurrency } from '@/lib/utils';
import { toast } from 'sonner';

export default function PortalMerch() {
  const { tenant } = useOutletContext();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState('All');
  const [cartOpen, setCartOpen] = useState(false);
  const [cartItems, setCartItems] = useState([]);
  const [offeringAmount, setOfferingAmount] = useState(0);

  useEffect(() => {
    const fetchMerch = async () => {
      try {
        const productsRes = await fetch(`${API_URL}/portal/merch/products`, { credentials: 'include' });
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
  const orderTotal = cartTotal + offeringAmount;

  const checkout = async () => {
    if (cartItems.length === 0) {
      toast.error('Your cart is empty');
      return;
    }
    try {
      const res = await fetch(`${API_URL}/portal/merch/orders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          items: cartItems.map((item) => ({
            product_id: item.id,
            name: item.name,
            price: item.price,
            quantity: item.quantity,
            image_url: item.image_url
          })),
          offering_amount: offeringAmount
        })
      });
      if (res.ok) {
        toast.success(offeringAmount > 0 ? 'Order placed with offering! God bless!' : 'Order placed!');
        setCartItems([]);
        setOfferingAmount(0);
        setCartOpen(false);
      } else {
        toast.error('Unable to place order');
      }
    } catch (error) {
      toast.error('Unable to place order');
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
                  <div>
                    <strong>{item.name}</strong>
                    <span>{formatCurrency(item.price)}</span>
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

          {/* Giving Nudge Section */}
          <div className="portal-merch-offering" data-testid="merch-offering-section">
            <div className="offering-header">
              <Heart className="w-4 h-4" />
              <span className="offering-label">Add an Offering?</span>
            </div>
            <p className="offering-subtitle">Your generosity helps {tenant?.name || 'our church'} do more.</p>
            <div className="offering-amounts">
              {[5, 10, 20].map((amount) => (
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
                className={`offering-btn custom ${offeringAmount > 0 && ![5, 10, 20].includes(offeringAmount) ? 'active' : ''}`}
                onClick={() => {
                  const custom = prompt('Enter custom offering amount:');
                  if (custom && !isNaN(parseFloat(custom))) {
                    setOfferingAmount(parseFloat(custom));
                  }
                }}
                data-testid="merch-offering-custom"
              >
                Custom
              </button>
            </div>
            {offeringAmount > 0 && (
              <div className="offering-selected">
                <span>Offering: {formatCurrency(offeringAmount)}</span>
                <button onClick={() => setOfferingAmount(0)} className="offering-remove">No thanks</button>
              </div>
            )}
          </div>

          <div className="portal-merch-cart-footer">
            <div className="cart-line">
              <span>Subtotal</span>
              <span>{formatCurrency(cartTotal)}</span>
            </div>
            {offeringAmount > 0 && (
              <div className="cart-line offering">
                <span>Offering</span>
                <span>{formatCurrency(offeringAmount)}</span>
              </div>
            )}
            <div className="cart-line total">
              <span>Total</span>
              <strong data-testid="merch-cart-total">{formatCurrency(orderTotal)}</strong>
            </div>
            <button
              className="portal-merch-checkout"
              onClick={checkout}
              data-testid="merch-checkout-btn"
            >
              {offeringAmount > 0 ? 'Place Order & Give' : 'Place Order'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
