import { useState, useEffect } from 'react';
import { Settings, Building2, Palette, Users, DollarSign, Mail, Link2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import { API_URL } from '@/lib/utils';

export default function SettingsPage() {
  const [tenant, setTenant] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('general');

  useEffect(() => {
    fetchTenant();
  }, []);

  const fetchTenant = async () => {
    try {
      const response = await fetch(`${API_URL}/tenant`);
      const data = await response.json();
      setTenant(data);
    } catch (error) {
      console.error('Failed to fetch tenant:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-8 bg-slate-200 rounded w-64"></div>
        <div className="h-96 bg-slate-200 rounded-lg"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="settings-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Settings</h1>
          <p className="page-subtitle">Configure your church management platform</p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-white border border-slate-200 p-1">
          <TabsTrigger value="general" data-testid="tab-general">
            <Building2 className="w-4 h-4 mr-2" />
            General
          </TabsTrigger>
          <TabsTrigger value="appearance" data-testid="tab-appearance">
            <Palette className="w-4 h-4 mr-2" />
            Appearance
          </TabsTrigger>
          <TabsTrigger value="giving" data-testid="tab-giving">
            <DollarSign className="w-4 h-4 mr-2" />
            Giving
          </TabsTrigger>
          <TabsTrigger value="integrations" data-testid="tab-integrations">
            <Link2 className="w-4 h-4 mr-2" />
            Integrations
          </TabsTrigger>
          <TabsTrigger value="staff" data-testid="tab-staff">
            <Users className="w-4 h-4 mr-2" />
            Staff & Roles
          </TabsTrigger>
        </TabsList>

        {/* General Settings */}
        <TabsContent value="general" className="space-y-6">
          <div className="bg-white border border-slate-200 rounded-lg p-6">
            <h3 className="font-semibold text-slate-900 mb-6">Church Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="form-group">
                <Label className="form-label">Church Name</Label>
                <Input defaultValue={tenant?.name || 'Abundant Church'} data-testid="church-name-input" />
              </div>
              <div className="form-group">
                <Label className="form-label">Subdomain</Label>
                <div className="flex items-center gap-2">
                  <Input defaultValue={tenant?.subdomain || 'abundant'} className="flex-1" />
                  <span className="text-slate-500">.solomon.ai</span>
                </div>
              </div>
              <div className="form-group">
                <Label className="form-label">Website</Label>
                <Input placeholder="https://www.yourchurch.org" />
              </div>
              <div className="form-group">
                <Label className="form-label">Timezone</Label>
                <Input defaultValue={tenant?.timezone || 'America/Los_Angeles'} />
              </div>
              <div className="form-group col-span-2">
                <Label className="form-label">Address</Label>
                <Input placeholder="1234 Church Street, City, State ZIP" />
              </div>
            </div>
            <div className="mt-6">
              <Button className="btn-primary" data-testid="save-general-btn">Save Changes</Button>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-lg p-6">
            <h3 className="font-semibold text-slate-900 mb-6">Plan Details</h3>
            <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
              <div>
                <p className="font-medium text-slate-900">Enterprise Plan</p>
                <p className="text-sm text-slate-500">Up to 100,000 members</p>
              </div>
              <span className="px-3 py-1 bg-emerald-50 text-emerald-700 rounded-full text-sm font-medium">
                Active
              </span>
            </div>
          </div>
        </TabsContent>

        {/* Appearance Settings */}
        <TabsContent value="appearance" className="space-y-6">
          <div className="bg-white border border-slate-200 rounded-lg p-6">
            <h3 className="font-semibold text-slate-900 mb-6">Brand Colors</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="form-group">
                <Label className="form-label">Primary Color</Label>
                <div className="flex items-center gap-3">
                  <div 
                    className="w-10 h-10 rounded-lg border border-slate-200"
                    style={{ backgroundColor: tenant?.primary_color || '#4f6ef7' }}
                  ></div>
                  <Input defaultValue={tenant?.primary_color || '#4f6ef7'} className="flex-1" />
                </div>
              </div>
              <div className="form-group">
                <Label className="form-label">Accent Color</Label>
                <div className="flex items-center gap-3">
                  <div 
                    className="w-10 h-10 rounded-lg border border-slate-200"
                    style={{ backgroundColor: tenant?.accent_color || '#00c896' }}
                  ></div>
                  <Input defaultValue={tenant?.accent_color || '#00c896'} className="flex-1" />
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-lg p-6">
            <h3 className="font-semibold text-slate-900 mb-6">Logo</h3>
            <div className="border-2 border-dashed border-slate-300 rounded-lg p-8 text-center">
              <p className="text-slate-500 mb-4">Upload your church logo</p>
              <Button variant="outline">Upload Image</Button>
            </div>
          </div>
        </TabsContent>

        {/* Giving Settings */}
        <TabsContent value="giving" className="space-y-6">
          <div className="bg-white border border-slate-200 rounded-lg p-6">
            <h3 className="font-semibold text-slate-900 mb-6">Payment Processing</h3>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 border border-slate-200 rounded-lg">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                    <span className="text-purple-600 font-bold">S</span>
                  </div>
                  <div>
                    <p className="font-medium text-slate-900">Stripe</p>
                    <p className="text-sm text-slate-500">Accept card and ACH payments</p>
                  </div>
                </div>
                <span className="px-3 py-1 bg-emerald-50 text-emerald-700 rounded-full text-sm font-medium">
                  Connected
                </span>
              </div>

              <div className="flex items-center justify-between p-4 border border-slate-200 rounded-lg">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                    <span className="text-blue-600 font-bold">P</span>
                  </div>
                  <div>
                    <p className="font-medium text-slate-900">PayPal</p>
                    <p className="text-sm text-slate-500">Accept PayPal payments</p>
                  </div>
                </div>
                <Button variant="outline" size="sm">Connect</Button>
              </div>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-lg p-6">
            <h3 className="font-semibold text-slate-900 mb-6">Giving Preferences</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-slate-900">Send automatic receipts</p>
                  <p className="text-sm text-slate-500">Email a receipt after each donation</p>
                </div>
                <Switch defaultChecked />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-slate-900">Allow anonymous giving</p>
                  <p className="text-sm text-slate-500">Let donors give without providing info</p>
                </div>
                <Switch defaultChecked />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-slate-900">Enable crypto donations</p>
                  <p className="text-sm text-slate-500">Accept Bitcoin, Ethereum, and more</p>
                </div>
                <Switch defaultChecked />
              </div>
            </div>
          </div>
        </TabsContent>

        {/* Integrations */}
        <TabsContent value="integrations" className="space-y-6">
          <div className="bg-white border border-slate-200 rounded-lg p-6">
            <h3 className="font-semibold text-slate-900 mb-6">Available Integrations</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                { name: 'Stripe', desc: 'Payment processing', status: 'connected' },
                { name: 'Resend', desc: 'Email delivery', status: 'connected' },
                { name: 'Twilio', desc: 'SMS messaging', status: 'available' },
                { name: 'Mailchimp', desc: 'Email marketing', status: 'available' },
                { name: 'QuickBooks', desc: 'Accounting sync', status: 'available' },
                { name: 'Planning Center', desc: 'Import data', status: 'available' },
              ].map((integration) => (
                <div key={integration.name} className="flex items-center justify-between p-4 border border-slate-200 rounded-lg">
                  <div>
                    <p className="font-medium text-slate-900">{integration.name}</p>
                    <p className="text-sm text-slate-500">{integration.desc}</p>
                  </div>
                  {integration.status === 'connected' ? (
                    <span className="px-3 py-1 bg-emerald-50 text-emerald-700 rounded-full text-sm font-medium">
                      Connected
                    </span>
                  ) : (
                    <Button variant="outline" size="sm">Connect</Button>
                  )}
                </div>
              ))}
            </div>
          </div>
        </TabsContent>

        {/* Staff & Roles */}
        <TabsContent value="staff" className="space-y-6">
          <div className="bg-white border border-slate-200 rounded-lg p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="font-semibold text-slate-900">Staff Users</h3>
              <Button className="btn-primary">
                <Users className="w-4 h-4 mr-2" />
                Invite Staff
              </Button>
            </div>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="font-medium">Admin User</td>
                  <td className="text-slate-600">admin@abundant.org</td>
                  <td>
                    <span className="px-2 py-0.5 bg-purple-50 text-purple-700 rounded-full text-xs font-medium">
                      Super Admin
                    </span>
                  </td>
                  <td>
                    <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 rounded-full text-xs font-medium">
                      Active
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="bg-white border border-slate-200 rounded-lg p-6">
            <h3 className="font-semibold text-slate-900 mb-6">Roles & Permissions</h3>
            <div className="space-y-3">
              {[
                { name: 'Super Admin', desc: 'Full access to all features', color: 'purple' },
                { name: 'Pastor', desc: 'Access to people, groups, and communications', color: 'blue' },
                { name: 'Finance', desc: 'Access to giving and reports', color: 'emerald' },
                { name: 'Staff', desc: 'Limited access to people and attendance', color: 'amber' },
              ].map((role) => (
                <div key={role.name} className="flex items-center justify-between p-4 border border-slate-200 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className={`w-3 h-3 rounded-full bg-${role.color}-500`}></div>
                    <div>
                      <p className="font-medium text-slate-900">{role.name}</p>
                      <p className="text-sm text-slate-500">{role.desc}</p>
                    </div>
                  </div>
                  <Button variant="ghost" size="sm">Edit</Button>
                </div>
              ))}
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
