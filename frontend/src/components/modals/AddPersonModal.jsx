import { useState } from 'react';
import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { toast } from 'sonner';
import { API_URL } from '@/lib/utils';

export default function AddPersonModal({ onClose, onSuccess }) {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    mobile_phone: '',
    membership_status: 'visitor',
    gender: '',
    campus: 'Main Campus',
  });
  const [errors, setErrors] = useState({});

  const handleChange = (field, value) => {
    setFormData({ ...formData, [field]: value });
    if (errors[field]) {
      setErrors({ ...errors, [field]: null });
    }
  };

  const validate = () => {
    const newErrors = {};
    if (!formData.first_name.trim()) {
      newErrors.first_name = 'First name is required';
    }
    if (!formData.last_name.trim()) {
      newErrors.last_name = 'Last name is required';
    }
    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/people`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error('Failed to create person');
      }

      toast.success('Person added successfully', {
        description: `${formData.first_name} ${formData.last_name} has been added.`,
      });
      onSuccess();
    } catch (error) {
      console.error('Failed to create person:', error);
      toast.error('Failed to add person', {
        description: 'Please try again.',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="slide-panel-overlay" onClick={onClose} data-testid="add-person-modal-overlay">
      <div className="slide-panel" onClick={(e) => e.stopPropagation()} data-testid="add-person-modal">
        <div className="slide-panel-header">
          <h2 className="slide-panel-title">Add Person</h2>
          <button
            onClick={onClose}
            className="p-1.5 rounded-md hover:bg-slate-100 transition-colors"
            data-testid="close-modal-btn"
          >
            <X className="w-5 h-5 text-slate-400" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="slide-panel-content">
          <div className="space-y-5">
            {/* Name Row */}
            <div className="grid grid-cols-2 gap-4">
              <div className="form-group">
                <Label htmlFor="first_name" className="form-label">First Name *</Label>
                <Input
                  id="first_name"
                  value={formData.first_name}
                  onChange={(e) => handleChange('first_name', e.target.value)}
                  className={errors.first_name ? 'border-red-500' : ''}
                  data-testid="first-name-input"
                />
                {errors.first_name && <p className="form-error">{errors.first_name}</p>}
              </div>
              <div className="form-group">
                <Label htmlFor="last_name" className="form-label">Last Name *</Label>
                <Input
                  id="last_name"
                  value={formData.last_name}
                  onChange={(e) => handleChange('last_name', e.target.value)}
                  className={errors.last_name ? 'border-red-500' : ''}
                  data-testid="last-name-input"
                />
                {errors.last_name && <p className="form-error">{errors.last_name}</p>}
              </div>
            </div>

            {/* Email */}
            <div className="form-group">
              <Label htmlFor="email" className="form-label">Email</Label>
              <Input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => handleChange('email', e.target.value)}
                placeholder="john@example.com"
                className={errors.email ? 'border-red-500' : ''}
                data-testid="email-input"
              />
              {errors.email && <p className="form-error">{errors.email}</p>}
            </div>

            {/* Phone */}
            <div className="form-group">
              <Label htmlFor="mobile_phone" className="form-label">Mobile Phone</Label>
              <Input
                id="mobile_phone"
                value={formData.mobile_phone}
                onChange={(e) => handleChange('mobile_phone', e.target.value)}
                placeholder="(555) 123-4567"
                data-testid="phone-input"
              />
            </div>

            {/* Status & Gender Row */}
            <div className="grid grid-cols-2 gap-4">
              <div className="form-group">
                <Label className="form-label">Membership Status</Label>
                <Select
                  value={formData.membership_status}
                  onValueChange={(v) => handleChange('membership_status', v)}
                >
                  <SelectTrigger data-testid="status-select">
                    <SelectValue placeholder="Select status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="visitor">Visitor</SelectItem>
                    <SelectItem value="regular">Regular Attendee</SelectItem>
                    <SelectItem value="member">Member</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="form-group">
                <Label className="form-label">Gender</Label>
                <Select
                  value={formData.gender}
                  onValueChange={(v) => handleChange('gender', v)}
                >
                  <SelectTrigger data-testid="gender-select">
                    <SelectValue placeholder="Select gender" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="male">Male</SelectItem>
                    <SelectItem value="female">Female</SelectItem>
                    <SelectItem value="non_binary">Non-binary</SelectItem>
                    <SelectItem value="prefer_not_to_say">Prefer not to say</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Campus */}
            <div className="form-group">
              <Label className="form-label">Campus</Label>
              <Select
                value={formData.campus}
                onValueChange={(v) => handleChange('campus', v)}
              >
                <SelectTrigger data-testid="campus-select">
                  <SelectValue placeholder="Select campus" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Main Campus">Main Campus</SelectItem>
                  <SelectItem value="North Campus">North Campus</SelectItem>
                  <SelectItem value="South Campus">South Campus</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </form>

        <div className="slide-panel-footer">
          <Button variant="outline" onClick={onClose} data-testid="cancel-btn">
            Cancel
          </Button>
          <Button 
            className="btn-primary" 
            onClick={handleSubmit}
            disabled={loading}
            data-testid="save-person-btn"
          >
            {loading ? 'Saving...' : 'Save Person'}
          </Button>
        </div>
      </div>
    </div>
  );
}
