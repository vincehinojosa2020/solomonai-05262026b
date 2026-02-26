import { useEffect, useMemo, useState } from 'react';
import { ShoppingBag, Search, Plus, Minus, X, ArrowRight } from 'lucide-react';
import { API_URL, formatCurrency } from '@/lib/utils';
import { toast } from 'sonner';

export default function PortalMerch() {
  const [products, setProducts] = useState([]);
  const [merchUrl, setMerchUrl] = useState('');
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState('All');
  const [cartOpen, setCartOpen] = useState(false);
  const [cartItems, setCartItems] = useState([]);

  useEffect(() => {
    const fetchMerch = async () => {
      try {
        const [productsRes, settingsRes] = await Promise.all([
          fetch(`${API_URL}/portal/merch/products`, { credentials: 'include' }),
          fetch(`${API_URL}/portal/merch/settings`, { credentials: 'include' })
        ]);
        if (productsRes.ok) {
          const data = await productsRes.json();
          setProducts(data.products || []);
        }
        if (settingsRes.ok) {
          const data = await settingsRes.json();
          setMerchUrl(data.merch_embed_url || '');
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
          }))
        })
      });
      if (res.ok) {
        toast.success('Order placed!');
        setCartItems([]);
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
          <span className="portal-tag">Merch</span>
          <h1>Church Merch Store</h1>
          <p>Shop curated merch, music, and accessories without leaving the member portal.</p>
        </div>
        <button
          className="portal-merch-cart-btn"
          onClick={() => setCartOpen(true)}
          data-testid="merch-cart-button"
        >
          <ShoppingBag className="w-4 h-4" /> Cart ({cartCount})
        </button>
      </div>

      <div className="portal-merch-embed" data-testid="merch-embed">
        {merchUrl ? (
          <iframe
            title="Merch Store"
            src={merchUrl}
            className="portal-merch-iframe"
            data-testid="merch-iframe"
          />
        ) : (
          <div className="portal-merch-empty" data-testid="merch-iframe-empty">Store embed unavailable.</div>
        )}
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
          <div className="portal-merch-cart-footer">
            <div>
              <span>Total</span>
              <strong data-testid="merch-cart-total">{formatCurrency(cartTotal)}</strong>
            </div>
            <button
              className="portal-merch-checkout"
              onClick={checkout}
              data-testid="merch-checkout-btn"
            >
              Place Order
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
