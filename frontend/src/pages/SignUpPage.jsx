import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Eye, EyeOff, Check, X, Shield, Lock, Mail, User, Phone, ArrowRight, Loader2, Building2 } from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

// Password requirements checker
const checkPasswordRequirements = (password) => {
  return {
    minLength: password.length >= 8,
    hasUppercase: /[A-Z]/.test(password),
    hasLowercase: /[a-z]/.test(password),
    hasNumber: /\d/.test(password),
    hasSpecial: /[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;'`~]/.test(password),
  };
};

const PasswordRequirement = ({ met, text }) => (
  <div className={`signup-req ${met ? 'met' : ''}`}>
    {met ? <Check className="w-3.5 h-3.5" /> : <X className="w-3.5 h-3.5" />}
    <span>{text}</span>
  </div>
);

export default function SignUpPage() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    password: '',
    confirmPassword: '',
    churchId: '',  // Added church selection
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [emailAvailable, setEmailAvailable] = useState(null);
  const [checkingEmail, setCheckingEmail] = useState(false);
  const [churches, setChurches] = useState([]);
  const [loadingChurches, setLoadingChurches] = useState(true);

  // Fetch available churches on mount
  useEffect(() => {
    const fetchChurches = async () => {
      try {
        const res = await fetch(`${API_URL}/tenants/list`);
        if (res.ok) {
          const data = await res.json();
          setChurches(data.filter(t => t.subscription_status === 'active'));
        }
      } catch (error) {
        console.error('Failed to fetch churches:', error);
      } finally {
        setLoadingChurches(false);
      }
    };
    fetchChurches();
  }, []);

  const passwordReqs = checkPasswordRequirements(formData.password);
  const allRequirementsMet = Object.values(passwordReqs).every(Boolean);
  const passwordsMatch = formData.password === formData.confirmPassword && formData.confirmPassword.length > 0;

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Reset email availability when email changes
    if (name === 'email') {
      setEmailAvailable(null);
    }
  };

  const checkEmailAvailability = async () => {
    if (!formData.email || !formData.email.includes('@')) return;
    
    setCheckingEmail(true);
    try {
      const res = await fetch(`${API_URL}/auth/check-email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: formData.email }),
      });
      const data = await res.json();
      setEmailAvailable(data.available);
    } catch (error) {
      console.error('Email check failed:', error);
    } finally {
      setCheckingEmail(false);
    }
  };

  const handleGoogleSignUp = () => {
    window.location.href = `${API_URL}/auth/google`;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!allRequirementsMet) {
      toast.error('Please meet all password requirements');
      return;
    }
    
    if (!passwordsMatch) {
      toast.error('Passwords do not match');
      return;
    }
    
    if (emailAvailable === false) {
      toast.error('This email is already registered');
      return;
    }

    setIsLoading(true);
    try {
      const res = await fetch(`${API_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          email: formData.email,
          password: formData.password,
          confirm_password: formData.confirmPassword,
          first_name: formData.firstName,
          last_name: formData.lastName,
          phone: formData.phone || null,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || 'Registration failed');
      }

      toast.success('Welcome to Abundant Church!');
      
      // Store user info
      localStorage.setItem('samson_user', JSON.stringify({
        user_id: data.user_id,
        email: data.email,
        name: data.name,
        role: data.role,
      }));

      // Redirect to portal
      navigate('/portal');
    } catch (error) {
      toast.error(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="signup-page" data-testid="signup-page">
      <div className="signup-sidebar">
        <div className="signup-brand">
          <h1 className="signup-logo">SAMS<span>O</span>N</h1>
          <p className="signup-tagline">Enterprise Church Management System</p>
        </div>
        
        <div className="signup-features">
          <div className="signup-feature">
            <Shield className="w-5 h-5" />
            <div>
              <h3>Bank-Level Security</h3>
              <p>256-bit encryption protects your data</p>
            </div>
          </div>
          <div className="signup-feature">
            <Lock className="w-5 h-5" />
            <div>
              <h3>SOC 2 Compliant</h3>
              <p>Enterprise security standards</p>
            </div>
          </div>
        </div>
        
        <p className="signup-version">Version 1.0.0 • Build 2026.02</p>
      </div>

      <div className="signup-main">
        <div className="signup-container">
          <div className="signup-header">
            <h2>Create Your Account</h2>
            <p>Join Abundant Church and start your journey</p>
          </div>

          {/* Google Sign Up */}
          <button 
            onClick={handleGoogleSignUp}
            className="signup-google-btn"
            data-testid="google-signup-btn"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Continue with Google
          </button>

          <div className="signup-divider">
            <span>or sign up with email</span>
          </div>

          <form onSubmit={handleSubmit} className="signup-form">
            {/* Church Selector */}
            <div className="signup-field">
              <label>Select Your Church</label>
              <div className="signup-input-wrapper">
                <Building2 className="signup-input-icon" />
                <select
                  name="churchId"
                  value={formData.churchId}
                  onChange={handleChange}
                  required
                  className="signup-select"
                  data-testid="signup-church"
                >
                  <option value="">Choose your church...</option>
                  {churches.map((church) => (
                    <option key={church.id} value={church.id}>
                      {church.name} — {church.city}, {church.state}
                    </option>
                  ))}
                </select>
              </div>
              {loadingChurches && (
                <span className="signup-hint">Loading churches...</span>
              )}
            </div>

            {/* Name Row */}
            <div className="signup-row">
              <div className="signup-field">
                <label>First Name</label>
                <div className="signup-input-wrapper">
                  <User className="signup-input-icon" />
                  <input
                    type="text"
                    name="firstName"
                    value={formData.firstName}
                    onChange={handleChange}
                    placeholder="John"
                    required
                    data-testid="signup-firstname"
                  />
                </div>
              </div>
              <div className="signup-field">
                <label>Last Name</label>
                <div className="signup-input-wrapper">
                  <User className="signup-input-icon" />
                  <input
                    type="text"
                    name="lastName"
                    value={formData.lastName}
                    onChange={handleChange}
                    placeholder="Smith"
                    required
                    data-testid="signup-lastname"
                  />
                </div>
              </div>
            </div>

            {/* Email */}
            <div className="signup-field">
              <label>Email Address</label>
              <div className="signup-input-wrapper">
                <Mail className="signup-input-icon" />
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  onBlur={checkEmailAvailability}
                  placeholder="john@example.com"
                  required
                  data-testid="signup-email"
                />
                {checkingEmail && <Loader2 className="signup-input-status checking" />}
                {emailAvailable === true && <Check className="signup-input-status available" />}
                {emailAvailable === false && <X className="signup-input-status taken" />}
              </div>
              {emailAvailable === false && (
                <p className="signup-field-error">This email is already registered. <Link to="/login">Sign in instead?</Link></p>
              )}
            </div>

            {/* Phone (Optional) */}
            <div className="signup-field">
              <label>Phone Number <span className="optional">(optional)</span></label>
              <div className="signup-input-wrapper">
                <Phone className="signup-input-icon" />
                <input
                  type="tel"
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  placeholder="(555) 123-4567"
                  data-testid="signup-phone"
                />
              </div>
            </div>

            {/* Password */}
            <div className="signup-field">
              <label>Password</label>
              <div className="signup-input-wrapper">
                <Lock className="signup-input-icon" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="Create a strong password"
                  required
                  data-testid="signup-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="signup-toggle-pw"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              
              {/* Password Requirements */}
              {formData.password.length > 0 && (
                <div className="signup-requirements" data-testid="password-requirements">
                  <PasswordRequirement met={passwordReqs.minLength} text="At least 8 characters" />
                  <PasswordRequirement met={passwordReqs.hasUppercase} text="One uppercase letter" />
                  <PasswordRequirement met={passwordReqs.hasLowercase} text="One lowercase letter" />
                  <PasswordRequirement met={passwordReqs.hasNumber} text="One number" />
                  <PasswordRequirement met={passwordReqs.hasSpecial} text="One special character (!@#$%^&*)" />
                </div>
              )}
            </div>

            {/* Confirm Password */}
            <div className="signup-field">
              <label>Confirm Password</label>
              <div className="signup-input-wrapper">
                <Lock className="signup-input-icon" />
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  placeholder="Confirm your password"
                  required
                  data-testid="signup-confirm-password"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="signup-toggle-pw"
                >
                  {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
                {formData.confirmPassword.length > 0 && (
                  passwordsMatch ? 
                    <Check className="signup-input-status available" /> : 
                    <X className="signup-input-status taken" />
                )}
              </div>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={isLoading || !allRequirementsMet || !passwordsMatch}
              className="signup-submit-btn"
              data-testid="signup-submit"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Creating Account...
                </>
              ) : (
                <>
                  Create Account
                  <ArrowRight className="w-5 h-5" />
                </>
              )}
            </button>
          </form>

          <p className="signup-login-link">
            Already have an account? <Link to="/login">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
