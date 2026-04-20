import { useEffect, useState } from 'react';
import { Plus, Package, Tags, Users, ShoppingBag, Edit, Trash2, Save, Link2 } from 'lucide-react';
import { API_URL, formatCurrency } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { toast } from 'sonner';
import { safeIframeSrc } from '@/utils/sanitize';

// Allowed hosts for merch store preview iframe
const MERCH_ALLOWED_HOSTS = [
  'shopify.com',
  'myshopify.com',
  'squarespace.com',
  'square.site',
  'bigcartel.com',
  'printful.com',
  'printify.com',
  'solomonai.us',
];

const defaultProductForm = {
  name: '',
  description: '',
  price: '',
  category: '',
  image_url: '',
  inventory: 0,
  is_featured: false,
  is_active: true,
};

export default function MerchAdminPage() {
  const [products, setProducts] = useState([]);
  const [orders, setOrders] = useState([]);
  const [summary, setSummary] = useState(null);
  const [merchUrl, setMerchUrl] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [productForm, setProductForm] = useState(defaultProductForm);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [productsRes, summaryRes, ordersRes, settingsRes] = await Promise.all([
        fetch(`${API_URL}/admin/merch/products`),
        fetch(`${API_URL}/admin/merch/summary`),
        fetch(`${API_URL}/admin/merch/orders?limit=8`),
        fetch(`${API_URL}/admin/merch/settings`)
      ]);

      if (productsRes.ok) {
        const data = await productsRes.json();
        setProducts(data.products || []);
      }
      if (summaryRes.ok) {
        const data = await summaryRes.json();
        setSummary(data);
      }
      if (ordersRes.ok) {
        const data = await ordersRes.json();
        setOrders(data.orders || []);
      }
      if (settingsRes.ok) {
        const data = await settingsRes.json();
        setMerchUrl(data.merch_embed_url || '');
      }
    } catch (error) {
      toast.error('Failed to load merch data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAll();
  }, []);

  const openModal = (product) => {
    if (product) {
      setEditingProduct(product);
      setProductForm({
        name: product.name || '',
        description: product.description || '',
        price: product.price || '',
        category: product.category || '',
        image_url: product.image_url || '',
        inventory: product.inventory || 0,
        is_featured: product.is_featured || false,
        is_active: product.is_active ?? true,
      });
    } else {
      setEditingProduct(null);
      setProductForm(defaultProductForm);
    }
    setModalOpen(true);
  };

  const saveProduct = async () => {
    if (!productForm.name.trim()) {
      toast.error('Product name is required');
      return;
    }
    if (!productForm.price) {
      toast.error('Price is required');
      return;
    }
    setSaving(true);
    try {
      const payload = {
        ...productForm,
        price: Number(productForm.price),
        inventory: Number(productForm.inventory || 0)
      };
      const res = await fetch(`${API_URL}/admin/merch/products${editingProduct ? `/${editingProduct.id}` : ''}`, {
        method: editingProduct ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        toast.success(editingProduct ? 'Product updated' : 'Product created');
        setModalOpen(false);
        setEditingProduct(null);
        setProductForm(defaultProductForm);
        fetchAll();
      } else {
        toast.error('Failed to save product');
      }
    } catch (error) {
      toast.error('Failed to save product');
    } finally {
      setSaving(false);
    }
  };

  const deleteProduct = async (productId) => {
    if (!confirm('Delete this product?')) return;
    try {
      const res = await fetch(`${API_URL}/admin/merch/products/${productId}`, {
        method: 'DELETE',
        
      });
      if (res.ok) {
        toast.success('Product deleted');
        fetchAll();
      } else {
        toast.error('Failed to delete product');
      }
    } catch (error) {
      toast.error('Failed to delete product');
    }
  };

  const saveSettings = async () => {
    if (!merchUrl.trim()) {
      toast.error('Merch embed URL is required');
      return;
    }
    setSaving(true);
    try {
      const res = await fetch(`${API_URL}/admin/merch/settings`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        
        body: JSON.stringify({ merch_embed_url: merchUrl.trim() })
      });
      if (res.ok) {
        toast.success('Merch settings updated');
      } else {
        toast.error('Failed to save settings');
      }
    } catch (error) {
      toast.error('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="merch-admin" data-testid="merch-admin-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Merch Store</h1>
          <p className="page-subtitle">Curate products, manage orders, and embed your store experience.</p>
        </div>
        <Button onClick={() => openModal(null)} className="merch-add-btn" data-testid="add-merch-btn">
          <Plus className="w-4 h-4" /> Add Product
        </Button>
      </div>

      <div className="merch-stats" data-testid="merch-stats">
        <div className="merch-stat-card" data-testid="merch-stat-products">
          <Package className="w-4 h-4" />
          <div>
            <span>Products</span>
            <strong>{summary?.products_total ?? 0}</strong>
          </div>
        </div>
        <div className="merch-stat-card" data-testid="merch-stat-featured">
          <Tags className="w-4 h-4" />
          <div>
            <span>Featured</span>
            <strong>{summary?.featured_products ?? 0}</strong>
          </div>
        </div>
        <div className="merch-stat-card" data-testid="merch-stat-orders">
          <ShoppingBag className="w-4 h-4" />
          <div>
            <span>Orders</span>
            <strong>{summary?.orders_count ?? 0}</strong>
          </div>
        </div>
        <div className="merch-stat-card" data-testid="merch-stat-members">
          <Users className="w-4 h-4" />
          <div>
            <span>Members</span>
            <strong>{summary?.member_count ?? 0}</strong>
          </div>
        </div>
        <div className="merch-stat-card" data-testid="merch-stat-revenue">
          <ShoppingBag className="w-4 h-4" />
          <div>
            <span>Revenue</span>
            <strong>{formatCurrency(summary?.revenue ?? 0)}</strong>
          </div>
        </div>
      </div>

      <div className="merch-grid">
        <div className="merch-card" data-testid="merch-settings-card">
          <div className="merch-card-header">
            <Link2 className="w-4 h-4" />
            <div>
              <h3>Embed Store URL</h3>
              <p>Paste the storefront URL you want members to experience inside Solomon AI.</p>
            </div>
          </div>
          <div className="merch-settings-form">
            <Input
              value={merchUrl}
              onChange={(e) => setMerchUrl(e.target.value)}
              placeholder="https://store.yourchurch.org"
              data-testid="merch-url-input"
            />
            <Button onClick={saveSettings} disabled={saving} data-testid="merch-settings-save">
              <Save className="w-4 h-4" /> Save
            </Button>
          </div>
          <div className="merch-preview" data-testid="merch-preview">
            {merchUrl ? (
              <iframe
                title="Merch Preview"
                src={safeIframeSrc(merchUrl, MERCH_ALLOWED_HOSTS)}
                className="merch-iframe"
                data-testid="merch-iframe"
              />
            ) : (
              <div className="merch-empty" data-testid="merch-empty">Add a URL to preview the store.</div>
            )}
          </div>
        </div>

        <div className="merch-card" data-testid="merch-orders-card">
          <div className="merch-card-header">
            <ShoppingBag className="w-4 h-4" />
            <div>
              <h3>Recent Orders</h3>
              <p>Latest merch activity from your members.</p>
            </div>
          </div>
          <div className="merch-orders">
            {orders.length === 0 ? (
              <div className="merch-empty" data-testid="merch-orders-empty">No orders yet.</div>
            ) : (
              orders.map((order) => (
                <div key={order.id} className="merch-order" data-testid={`merch-order-${order.id}`}>
                  <div>
                    <strong>{order.items?.[0]?.name || 'Order'}{order.items?.length > 1 ? ` +${order.items.length - 1}` : ''}</strong>
                    <span>{order.items?.length || 0} items · {formatCurrency(order.total || 0)}</span>
                  </div>
                  <span className="merch-order-status">{order.status || 'placed'}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      <div className="merch-products" data-testid="merch-products">
        <h2>Product Catalog</h2>
        {loading ? (
          <div className="merch-empty">Loading products...</div>
        ) : (
          <div className="merch-product-grid">
            {products.map((product) => (
              <div key={product.id} className="merch-product-card" data-testid={`merch-product-${product.id}`}>
                <div className="merch-product-image">
                  <img src={product.image_url || 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=900&q=80'} alt={product.name} />
                  {product.is_featured && <span className="merch-product-badge">Featured</span>}
                </div>
                <div className="merch-product-body">
                  <h3>{product.name}</h3>
                  <p>{product.description || 'No description provided.'}</p>
                  <div className="merch-product-meta">
                    <span>{formatCurrency(product.price || 0)}</span>
                    <span>{product.category || 'General'}</span>
                    <span>{product.inventory || 0} in stock</span>
                  </div>
                </div>
                <div className="merch-product-actions">
                  <Button variant="outline" onClick={() => openModal(product)} data-testid={`edit-merch-${product.id}`}>
                    <Edit className="w-4 h-4" /> Edit
                  </Button>
                  <Button variant="ghost" onClick={() => deleteProduct(product.id)} data-testid={`delete-merch-${product.id}`}>
                    <Trash2 className="w-4 h-4 text-red-500" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="merch-modal" data-testid="merch-product-modal">
          <DialogHeader>
            <DialogTitle>{editingProduct ? 'Edit Product' : 'Add Product'}</DialogTitle>
            <DialogDescription>Build your merch catalog with apparel, mugs, or accessories.</DialogDescription>
          </DialogHeader>
          <div className="merch-form">
            <Input
              value={productForm.name}
              onChange={(e) => setProductForm((prev) => ({ ...prev, name: e.target.value }))}
              placeholder="Product name"
              data-testid="merch-name-input"
            />
            <Textarea
              value={productForm.description}
              onChange={(e) => setProductForm((prev) => ({ ...prev, description: e.target.value }))}
              placeholder="Short description"
              data-testid="merch-description-input"
            />
            <div className="merch-form-row">
              <Input
                type="number"
                value={productForm.price}
                onChange={(e) => setProductForm((prev) => ({ ...prev, price: e.target.value }))}
                placeholder="Price"
                data-testid="merch-price-input"
              />
              <Input
                value={productForm.category}
                onChange={(e) => setProductForm((prev) => ({ ...prev, category: e.target.value }))}
                placeholder="Category"
                data-testid="merch-category-input"
              />
            </div>
            <Input
              value={productForm.image_url}
              onChange={(e) => setProductForm((prev) => ({ ...prev, image_url: e.target.value }))}
              placeholder="Image URL"
              data-testid="merch-image-input"
            />
            <Input
              type="number"
              value={productForm.inventory}
              onChange={(e) => setProductForm((prev) => ({ ...prev, inventory: e.target.value }))}
              placeholder="Inventory"
              data-testid="merch-inventory-input"
            />
            <div className="merch-toggle-row">
              <label>
                <input
                  type="checkbox"
                  checked={productForm.is_featured}
                  onChange={(e) => setProductForm((prev) => ({ ...prev, is_featured: e.target.checked }))}
                  data-testid="merch-featured-toggle"
                />
                Featured
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={productForm.is_active}
                  onChange={(e) => setProductForm((prev) => ({ ...prev, is_active: e.target.checked }))}
                  data-testid="merch-active-toggle"
                />
                Published
              </label>
            </div>
            <div className="merch-form-actions">
              <Button onClick={saveProduct} disabled={saving} data-testid="merch-save-btn">
                {saving ? 'Saving...' : 'Save Product'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
