import { useEffect, useState, useCallback } from 'react';
import { usePolling } from '@/hooks/usePolling';
import { Coffee, Plus, Save, ShoppingBag, Users, Clock, Edit, Trash2 } from 'lucide-react';
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

const defaultItemForm = {
  name: '',
  description: '',
  category: '',
  price: '',
  image_url: '',
  is_featured: false,
  is_active: true,
};

export default function CafeAdminPage() {
  const [items, setItems] = useState([]);
  const [orders, setOrders] = useState([]);
  const [summary, setSummary] = useState(null);
  const [settings, setSettings] = useState({
    pickup_start: '',
    pickup_end: '',
    pickup_interval_minutes: 15,
    location: '',
    is_active: true,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [itemForm, setItemForm] = useState(defaultItemForm);

  const fetchCafeData = async () => {
    setLoading(true);
    try {
      const [itemsRes, ordersRes, summaryRes, settingsRes] = await Promise.all([
        fetch(`${API_URL}/admin/cafe/items`, { credentials: 'include' }),
        fetch(`${API_URL}/admin/cafe/orders?limit=8`, { credentials: 'include' }),
        fetch(`${API_URL}/admin/cafe/summary`, { credentials: 'include' }),
        fetch(`${API_URL}/admin/cafe/settings`, { credentials: 'include' })
      ]);

      if (itemsRes.ok) {
        const data = await itemsRes.json();
        setItems(data.items || []);
      }
      if (ordersRes.ok) {
        const data = await ordersRes.json();
        setOrders(data.orders || []);
      }
      if (summaryRes.ok) {
        const data = await summaryRes.json();
        setSummary(data);
      }
      if (settingsRes.ok) {
        const data = await settingsRes.json();
        setSettings(data.settings || settings);
      }
    } catch (error) {
      toast.error('Failed to load cafe data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCafeData();
  }, []);

  // Real-time polling every 30 seconds
  usePolling(useCallback(() => fetchCafeData(), []), 30000);

  const openModal = (item) => {
    if (item) {
      setEditingItem(item);
      setItemForm({
        name: item.name || '',
        description: item.description || '',
        category: item.category || '',
        price: item.price || '',
        image_url: item.image_url || '',
        is_featured: item.is_featured || false,
        is_active: item.is_active ?? true,
      });
    } else {
      setEditingItem(null);
      setItemForm(defaultItemForm);
    }
    setModalOpen(true);
  };

  const saveItem = async () => {
    if (!itemForm.name.trim()) {
      toast.error('Item name is required');
      return;
    }
    if (!itemForm.price) {
      toast.error('Price is required');
      return;
    }
    setSaving(true);
    try {
      const payload = {
        ...itemForm,
        price: Number(itemForm.price),
      };
      const res = await fetch(`${API_URL}/admin/cafe/items${editingItem ? `/${editingItem.id}` : ''}`, {
        method: editingItem ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        toast.success(editingItem ? 'Item updated' : 'Item added');
        setModalOpen(false);
        setEditingItem(null);
        setItemForm(defaultItemForm);
        fetchCafeData();
      } else {
        toast.error('Failed to save item');
      }
    } catch (error) {
      toast.error('Failed to save item');
    } finally {
      setSaving(false);
    }
  };

  const deleteItem = async (itemId) => {
    if (!confirm('Delete this menu item?')) return;
    try {
      const res = await fetch(`${API_URL}/admin/cafe/items/${itemId}`, {
        method: 'DELETE',
        credentials: 'include'
      });
      if (res.ok) {
        toast.success('Item deleted');
        fetchCafeData();
      } else {
        toast.error('Failed to delete item');
      }
    } catch (error) {
      toast.error('Failed to delete item');
    }
  };

  const saveSettings = async () => {
    setSaving(true);
    try {
      const res = await fetch(`${API_URL}/admin/cafe/settings`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(settings)
      });
      if (res.ok) {
        toast.success('Cafe settings updated');
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
    <div className="cafe-admin" data-testid="cafe-admin-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Abundant Cafe</h1>
          <p className="page-subtitle">Manage menu items, pickup windows, and cafe orders.</p>
        </div>
        <Button onClick={() => openModal(null)} className="cafe-add-btn" data-testid="add-cafe-item">
          <Plus className="w-4 h-4" /> Add Menu Item
        </Button>
      </div>

      <div className="cafe-stats" data-testid="cafe-stats">
        <div className="cafe-stat-card" data-testid="cafe-stat-items">
          <Coffee className="w-4 h-4" />
          <div>
            <span>Menu Items</span>
            <strong>{summary?.items_total ?? 0}</strong>
          </div>
        </div>
        <div className="cafe-stat-card" data-testid="cafe-stat-active">
          <Coffee className="w-4 h-4" />
          <div>
            <span>Active Items</span>
            <strong>{summary?.active_items ?? 0}</strong>
          </div>
        </div>
        <div className="cafe-stat-card" data-testid="cafe-stat-orders">
          <ShoppingBag className="w-4 h-4" />
          <div>
            <span>Orders</span>
            <strong>{summary?.orders_count ?? 0}</strong>
          </div>
        </div>
        <div className="cafe-stat-card" data-testid="cafe-stat-members">
          <Users className="w-4 h-4" />
          <div>
            <span>Members</span>
            <strong>{summary?.member_count ?? 0}</strong>
          </div>
        </div>
        <div className="cafe-stat-card" data-testid="cafe-stat-revenue">
          <ShoppingBag className="w-4 h-4" />
          <div>
            <span>Revenue</span>
            <strong>{formatCurrency(summary?.revenue ?? 0)}</strong>
          </div>
        </div>
      </div>

      <div className="cafe-grid">
        <div className="cafe-card" data-testid="cafe-settings-card">
          <div className="cafe-card-header">
            <Clock className="w-4 h-4" />
            <div>
              <h3>Pickup Window</h3>
              <p>Set cafe availability and pickup timing.</p>
            </div>
          </div>
          <div className="cafe-settings-form">
            <Input
              value={settings.pickup_start || ''}
              onChange={(e) => setSettings((prev) => ({ ...prev, pickup_start: e.target.value }))}
              placeholder="Pickup start (e.g., 7:30 AM)"
              data-testid="cafe-pickup-start"
            />
            <Input
              value={settings.pickup_end || ''}
              onChange={(e) => setSettings((prev) => ({ ...prev, pickup_end: e.target.value }))}
              placeholder="Pickup end (e.g., 10:30 AM)"
              data-testid="cafe-pickup-end"
            />
            <Input
              type="number"
              value={settings.pickup_interval_minutes || 15}
              onChange={(e) => setSettings((prev) => ({ ...prev, pickup_interval_minutes: Number(e.target.value) }))}
              placeholder="Interval (minutes)"
              data-testid="cafe-pickup-interval"
            />
            <Input
              value={settings.location || ''}
              onChange={(e) => setSettings((prev) => ({ ...prev, location: e.target.value }))}
              placeholder="Pickup location"
              data-testid="cafe-pickup-location"
            />
            <div className="cafe-toggle-row">
              <label>
                <input
                  type="checkbox"
                  checked={settings.is_active ?? true}
                  onChange={(e) => setSettings((prev) => ({ ...prev, is_active: e.target.checked }))}
                  data-testid="cafe-active-toggle"
                />
                Cafe Open
              </label>
            </div>
            <Button onClick={saveSettings} disabled={saving} data-testid="cafe-settings-save">
              <Save className="w-4 h-4" /> Save Settings
            </Button>
          </div>
        </div>

        <div className="cafe-card" data-testid="cafe-orders-card">
          <div className="cafe-card-header">
            <ShoppingBag className="w-4 h-4" />
            <div>
              <h3>Recent Orders</h3>
              <p>Latest cafe pickups requested by members.</p>
            </div>
          </div>
          <div className="cafe-orders">
            {orders.length === 0 ? (
              <div className="cafe-empty" data-testid="cafe-orders-empty">No cafe orders yet.</div>
            ) : (
              orders.map((order) => (
                <div key={order.id} className="cafe-order" data-testid={`cafe-order-${order.id}`}>
                  <div>
                    <strong>{order.items?.[0]?.name || 'Order'}{order.items?.length > 1 ? ` +${order.items.length - 1}` : ''}</strong>
                    <span>{order.pickup_time || 'Pickup'} · {formatCurrency(order.total || 0)}</span>
                  </div>
                  <span className="cafe-order-status">{order.status || 'placed'}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      <div className="cafe-menu" data-testid="cafe-menu">
        <h2>Menu Items</h2>
        {loading ? (
          <div className="cafe-empty">Loading menu...</div>
        ) : (
          <div className="cafe-menu-grid">
            {items.map((item) => (
              <div key={item.id} className="cafe-menu-card" data-testid={`cafe-item-${item.id}`}>
                <div className="cafe-menu-image">
                  <img src={item.image_url || 'https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=900&q=80'} alt={item.name} />
                  {item.is_featured && <span className="cafe-badge">Featured</span>}
                </div>
                <div className="cafe-menu-body">
                  <h3>{item.name}</h3>
                  <p>{item.description || 'Menu description'}</p>
                  <div className="cafe-menu-meta">
                    <span>{formatCurrency(item.price || 0)}</span>
                    <span>{item.category || 'General'}</span>
                  </div>
                </div>
                <div className="cafe-menu-actions">
                  <Button variant="outline" onClick={() => openModal(item)} data-testid={`edit-cafe-${item.id}`}>
                    <Edit className="w-4 h-4" /> Edit
                  </Button>
                  <Button variant="ghost" onClick={() => deleteItem(item.id)} data-testid={`delete-cafe-${item.id}`}>
                    <Trash2 className="w-4 h-4 text-red-500" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="cafe-modal" data-testid="cafe-item-modal">
          <DialogHeader>
            <DialogTitle>{editingItem ? 'Edit Menu Item' : 'Add Menu Item'}</DialogTitle>
            <DialogDescription>Build your cafe menu with coffee and snacks.</DialogDescription>
          </DialogHeader>
          <div className="cafe-form">
            <Input
              value={itemForm.name}
              onChange={(e) => setItemForm((prev) => ({ ...prev, name: e.target.value }))}
              placeholder="Item name"
              data-testid="cafe-item-name"
            />
            <Textarea
              value={itemForm.description}
              onChange={(e) => setItemForm((prev) => ({ ...prev, description: e.target.value }))}
              placeholder="Short description"
              data-testid="cafe-item-description"
            />
            <div className="cafe-form-row">
              <Input
                type="number"
                value={itemForm.price}
                onChange={(e) => setItemForm((prev) => ({ ...prev, price: e.target.value }))}
                placeholder="Price"
                data-testid="cafe-item-price"
              />
              <Input
                value={itemForm.category}
                onChange={(e) => setItemForm((prev) => ({ ...prev, category: e.target.value }))}
                placeholder="Category"
                data-testid="cafe-item-category"
              />
            </div>
            <Input
              value={itemForm.image_url}
              onChange={(e) => setItemForm((prev) => ({ ...prev, image_url: e.target.value }))}
              placeholder="Image URL"
              data-testid="cafe-item-image"
            />
            <div className="cafe-toggle-row">
              <label>
                <input
                  type="checkbox"
                  checked={itemForm.is_featured}
                  onChange={(e) => setItemForm((prev) => ({ ...prev, is_featured: e.target.checked }))}
                  data-testid="cafe-item-featured"
                />
                Featured
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={itemForm.is_active}
                  onChange={(e) => setItemForm((prev) => ({ ...prev, is_active: e.target.checked }))}
                  data-testid="cafe-item-active"
                />
                Active
              </label>
            </div>
            <div className="cafe-form-actions">
              <Button onClick={saveItem} disabled={saving} data-testid="cafe-item-save">
                {saving ? 'Saving...' : 'Save Item'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
