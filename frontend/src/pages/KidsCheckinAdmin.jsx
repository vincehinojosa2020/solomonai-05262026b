import { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Search, RefreshCw, UserCheck, UserX, Clock, 
  AlertCircle, CheckCircle2, Phone, User, Users,
  QrCode, Sparkles, Shield, Cross, Plus, Mail, PartyPopper,
  Camera, Keyboard
} from 'lucide-react';
import { SectionTutorial, TUTORIALS } from '@/components/SectionTutorial';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

// Colorful Bible-themed avatar styles (warm, vibrant - no rainbow)
const AVATAR_COLORS = [
  { bg: 'linear-gradient(135deg, #E11D48 0%, #F43F5E 100%)', emoji: '🦁', character: 'Daniel' },
  { bg: 'linear-gradient(135deg, #7C3AED 0%, #A78BFA 100%)', emoji: '🐑', character: 'David' },
  { bg: 'linear-gradient(135deg, #0891B2 0%, #22D3EE 100%)', emoji: '🌊', character: 'Moses' },
  { bg: 'linear-gradient(135deg, #EA580C 0%, #FB923C 100%)', emoji: '⭐', character: 'Abraham' },
  { bg: 'linear-gradient(135deg, #059669 0%, #34D399 100%)', emoji: '🕊️', character: 'Noah' },
  { bg: 'linear-gradient(135deg, #2563EB 0%, #60A5FA 100%)', emoji: '🐋', character: 'Jonah' },
  { bg: 'linear-gradient(135deg, #DB2777 0%, #F472B6 100%)', emoji: '👑', character: 'Esther' },
  { bg: 'linear-gradient(135deg, #CA8A04 0%, #FACC15 100%)', emoji: '💪', character: 'Samson' },
];

const getAvatarStyle = (name) => {
  const index = (name?.charCodeAt(0) || 0) % AVATAR_COLORS.length;
  return AVATAR_COLORS[index];
};

const getAge = (birthdate) => {
  if (!birthdate) return null;
  const today = new Date();
  const birth = new Date(birthdate);
  let age = today.getFullYear() - birth.getFullYear();
  const monthDiff = today.getMonth() - birth.getMonth();
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
    age--;
  }
  return age;
};

const formatAge = (birthdate) => {
  const age = getAge(birthdate);
  if (age === null) return 'Age not set';
  if (age === 0) return 'Under 1 year';
  if (age === 1) return '1 year old';
  return `${age} years old`;
};

export default function KidsCheckinAdmin() {
  const [activeTab, setActiveTab] = useState('checkedin');
  const [checkins, setCheckins] = useState([]);
  const [allKids, setAllKids] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [pickupCode, setPickupCode] = useState('');
  const [verifyResult, setVerifyResult] = useState(null);
  const [showCheckoutModal, setShowCheckoutModal] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [showRegisterFamily, setShowRegisterFamily] = useState(false);
  const [lastCheckinCount, setLastCheckinCount] = useState(0);
  const [newCheckinAlert, setNewCheckinAlert] = useState(false);
  const [scannerActive, setScannerActive] = useState(false);
  const [checkoutMode, setCheckoutMode] = useState('choose');
  const [scanResult, setScanResult] = useState(null);
  const scannerRef = useRef(null);
  const html5QrCodeRef = useRef(null);
  const [showManualCheckin, setShowManualCheckin] = useState(false);
  const [manualSearch, setManualSearch] = useState('');
  const [manualClassroom, setManualClassroom] = useState('Sunday School');
  
  // New family registration form
  const [newFamily, setNewFamily] = useState({
    parentName: '',
    parentEmail: '',
    parentPhone: '',
    childName: '',
    childBirthdate: '',
    childAllergies: '',
    childNotes: ''
  });

  const fetchData = useCallback(async () => {
    try {
      const [checkinsRes, kidsRes] = await Promise.all([
        fetch(`${API_URL}/admin/kids/checkins?status=checked_in`),
        fetch(`${API_URL}/admin/kids/all`)
      ]);
      
      if (checkinsRes.ok) {
        const data = await checkinsRes.json();
        const newCheckins = data.checkins || [];
        
        // Alert if new check-in detected
        if (newCheckins.length > lastCheckinCount && lastCheckinCount > 0) {
          const newKid = newCheckins.find(c => !checkins.find(old => old.id === c.id));
          if (newKid) {
            setNewCheckinAlert(true);
            toast.success(
              <div className="flex items-center gap-2">
                <span className="text-lg">🎉</span>
                <span><strong>{newKid.child_name}</strong> just checked in!</span>
              </div>,
              { duration: 5000 }
            );
            // Play notification sound (optional)
            try {
              const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2teleUUxPlOv1sqmcE0yQnzX2bCJYjg1Wazm4rqWe1s8Pnam4uSxiGctCVKm3eGofkMfOIOy2sqdeEUeO3rL3re0');
              audio.volume = 0.3;
              audio.play().catch(() => {});
            } catch (e) {}
            setTimeout(() => setNewCheckinAlert(false), 3000);
          }
        }
        setLastCheckinCount(newCheckins.length);
        setCheckins(newCheckins);
      }
      
      if (kidsRes.ok) {
        const data = await kidsRes.json();
        setAllKids(data.children || []);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  }, [lastCheckinCount, checkins]);

  useEffect(() => {
    fetchData();
    // Auto-refresh every 2 seconds for production-ready real-time updates
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, []);
  
  // Register new family
  const handleRegisterFamily = async () => {
    if (!newFamily.parentName || !newFamily.parentEmail || !newFamily.childName) {
      toast.error('Please fill in parent name, email, and child name');
      return;
    }
    
    try {
      const res = await fetch(`${API_URL}/admin/kids/register-family`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        
        body: JSON.stringify(newFamily)
      });
      
      if (res.ok) {
        const data = await res.json();
        toast.success(
          <div className="flex flex-col">
            <span className="font-bold">Family Registered! ✝️</span>
            <span className="text-sm">Welcome {newFamily.parentName} & {newFamily.childName}</span>
          </div>,
          { duration: 5000 }
        );
        setShowRegisterFamily(false);
        setNewFamily({
          parentName: '',
          parentEmail: '',
          parentPhone: '',
          childName: '',
          childBirthdate: '',
          childAllergies: '',
          childNotes: ''
        });
        fetchData();
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Registration failed');
      }
    } catch (error) {
      toast.error('Error registering family');
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
    toast.success('Refreshed!');
  };

  const handleDirectCheckin = async (child) => {
    try {
      const res = await fetch(`${API_URL}/admin/kids/${child.id}/checkin`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        
        body: JSON.stringify({ classroom: manualClassroom || 'Sunday School' })
      });
      
      if (res.ok) {
        const data = await res.json();
        toast.success(
          <div className="flex flex-col">
            <span className="font-bold">{child.name} checked in!</span>
            <span className="text-sm">Pickup Code: <strong className="text-amber-500">{data.pickup_code}</strong></span>
          </div>,
          { duration: 8000 }
        );
        setShowManualCheckin(false);
        setManualSearch('');
        fetchData();
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Check-in failed');
      }
    } catch (error) {
      toast.error('Error during check-in');
    }
  };

  const handleVerifyCode = async () => {
    if (!pickupCode.trim()) {
      toast.error('Please enter a pickup code');
      return;
    }
    
    try {
      const res = await fetch(`${API_URL}/admin/kids/verify-pickup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        
        body: JSON.stringify({ code: pickupCode })
      });
      
      if (res.ok) {
        const data = await res.json();
        setVerifyResult(data);
        if (!data.valid) {
          toast.error('Invalid pickup code');
        }
      }
    } catch (error) {
      toast.error('Error verifying code');
    }
  };

  const handleCheckout = async (checkinId) => {
    try {
      const res = await fetch(`${API_URL}/admin/kids/checkins/${checkinId}/checkout`, {
        method: 'POST',
        
      });
      
      if (res.ok) {
        toast.success('Child checked out safely!');
        setShowCheckoutModal(null);
        setVerifyResult(null);
        setPickupCode('');
        setScanResult(null);
        setCheckoutMode('choose');
        fetchData();
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Checkout failed');
      }
    } catch (error) {
      toast.error('Error during checkout');
    }
  };

  const startQrScanner = async () => {
    setScannerActive(true);
    setCheckoutMode('scan');
    setScanResult(null);
    
    // Dynamic import to avoid SSR issues
    try {
      const { Html5Qrcode } = await import('html5-qrcode');
      
      // Wait for DOM element
      await new Promise(r => setTimeout(r, 300));
      
      if (!document.getElementById('qr-reader')) return;
      
      const html5QrCode = new Html5Qrcode('qr-reader');
      html5QrCodeRef.current = html5QrCode;
      
      await html5QrCode.start(
        { facingMode: 'environment' },
        { fps: 10, qrbox: { width: 250, height: 250 } },
        async (decodedText) => {
          // Stop scanner on success
          try { await html5QrCode.stop(); } catch(e) {}
          setScannerActive(false);
          
          // Process the QR code
          try {
            const res = await fetch(`${API_URL}/admin/kids/checkout-by-code`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ pickup_code: decodedText })
            });
            
            if (res.ok) {
              const data = await res.json();
              setScanResult({ success: true, ...data });
              toast.success(`${data.child_name} checked out!`);
              fetchData();
            } else {
              const err = await res.json();
              setScanResult({ success: false, message: err.detail || 'Invalid code' });
              toast.error(err.detail || 'Invalid QR code');
            }
          } catch (error) {
            setScanResult({ success: false, message: 'Error processing code' });
          }
        },
        () => {} // ignore scan errors (no QR in frame)
      );
    } catch (err) {
      console.error('QR Scanner error:', err);
      toast.error('Camera access denied or not available. Use manual code entry.');
      setScannerActive(false);
      setCheckoutMode('manual');
    }
  };

  const stopQrScanner = async () => {
    try {
      if (html5QrCodeRef.current) {
        await html5QrCodeRef.current.stop();
        html5QrCodeRef.current = null;
      }
    } catch(e) {}
    setScannerActive(false);
    setCheckoutMode('choose');
  };

  // Cleanup scanner on unmount
  useEffect(() => {
    return () => {
      if (html5QrCodeRef.current) {
        try { html5QrCodeRef.current.stop(); } catch(e) {}
      }
    };
  }, []);

  // Enrich checkins with child data
  const enrichedCheckins = checkins.map(checkin => {
    const child = allKids.find(k => k.id === checkin.child_id);
    return { ...checkin, child };
  });

  // Filter kids for check-in station
  const availableForCheckin = allKids.filter(kid => 
    !checkins.some(c => c.child_id === kid.id) &&
    (kid.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
     kid.parent_name?.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  if (loading) {
    return (
      <div className="kca-loading">
        <div className="kca-loading-spinner">
          <Cross className="w-10 h-10 text-white" />
        </div>
        <p>Loading Kids Check-in...</p>
      </div>
    );
  }

  return (
    <div className={`kca-page ${newCheckinAlert ? 'kca-new-alert' : ''}`} data-testid="kids-checkin-admin">
      {/* New Check-in Alert */}
      {newCheckinAlert && (
        <div className="kca-alert-banner">
          <span>🎉 New Check-in!</span>
        </div>
      )}
      
      {/* Header */}
      <div className="kca-header">
        <div className="kca-header-left">
          <div className="kca-header-icon">
            <span>✝️</span>
            <Sparkles className="kca-sparkle" />
          </div>
          <div>
            <h1>Kids Check-in Station</h1>
            <div className="kca-live-indicator">
              <span className="kca-live-dot"></span>
              <span>LIVE • Updates every 2s</span>
            </div>
          </div>
        </div>
        <div className="kca-header-right">
          <SectionTutorial {...TUTORIALS.checkins} />
          <button 
            className="kca-register-btn"
            onClick={() => setShowManualCheckin(true)}
            data-testid="manual-checkin-btn"
            style={{ background: '#3b82f6', borderColor: '#3b82f6' }}
          >
            <UserCheck className="w-5 h-5" />
            + Manual Check-In
          </button>
          <button 
            className="kca-register-btn"
            onClick={() => setShowRegisterFamily(true)}
            data-testid="register-family-btn"
          >
            <Plus className="w-5 h-5" />
            Register New Family
          </button>
          <div className="kca-stat-box">
            <span className="kca-stat-number">{checkins.length}</span>
            <span className="kca-stat-label">Checked In</span>
          </div>
          <button 
            className="kca-refresh-btn"
            onClick={handleRefresh}
            disabled={refreshing}
          >
            <RefreshCw className={`w-5 h-5 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="kca-tabs">
        <button 
          className={`kca-tab ${activeTab === 'checkedin' ? 'active' : ''}`}
          onClick={() => setActiveTab('checkedin')}
          data-testid="tab-checked-in"
        >
          <UserCheck className="w-5 h-5" />
          <span>Currently Checked In</span>
          <span className="kca-tab-count">{checkins.length}</span>
        </button>
        <button 
          className={`kca-tab ${activeTab === 'checkin' ? 'active' : ''}`}
          onClick={() => setActiveTab('checkin')}
          data-testid="tab-check-in"
        >
          <Users className="w-5 h-5" />
          <span>Check In</span>
        </button>
        <button 
          className={`kca-tab ${activeTab === 'checkout' ? 'active' : ''}`}
          onClick={() => setActiveTab('checkout')}
          data-testid="tab-checkout"
        >
          <QrCode className="w-5 h-5" />
          <span>Check Out</span>
        </button>
      </div>

      {/* Tab Content */}
      <div className="kca-content">
        <AnimatePresence mode="wait">
          {/* Currently Checked In Tab */}
          {activeTab === 'checkedin' && (
            <motion.div
              key="checkedin"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="kca-checkedin-grid"
            >
              {enrichedCheckins.length === 0 ? (
                <div className="kca-empty">
                  <span className="kca-empty-emoji">🏠</span>
                  <h3>No Children Checked In</h3>
                  <p>Check in children using the "Check In" tab</p>
                </div>
              ) : (
                enrichedCheckins.map((checkin) => {
                  const avatarStyle = getAvatarStyle(checkin.child?.name || 'A');
                  return (
                    <motion.div
                      key={checkin.id}
                      className="kca-child-card"
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      data-testid={`checked-in-card-${checkin.id}`}
                    >
                      <div className="kca-card-status">
                        <CheckCircle2 className="w-4 h-4" />
                        <span>Checked In</span>
                      </div>
                      
                      <div 
                        className="kca-card-avatar"
                        style={{ background: avatarStyle.bg }}
                      >
                        <span className="kca-avatar-letter">
                          {checkin.child?.name?.charAt(0) || '?'}
                        </span>
                        <span className="kca-avatar-emoji">{avatarStyle.emoji}</span>
                      </div>
                      
                      <h3>{checkin.child?.name || 'Unknown'}</h3>
                      <p className="kca-card-age">
                        <span>🎂</span> {formatAge(checkin.child?.birthdate)}
                      </p>
                      
                      {checkin.child?.allergies && (
                        <div className="kca-allergy-badge">
                          <AlertCircle className="w-3 h-3" />
                          {checkin.child.allergies}
                        </div>
                      )}
                      
                      <div className="kca-pickup-code">
                        <span className="kca-code-label">Pickup Code</span>
                        <span className="kca-code-value">{checkin.pickup_code}</span>
                      </div>
                      
                      <div className="kca-card-meta">
                        <div className="kca-meta-item">
                          <Clock className="w-3 h-3" />
                          {new Date(checkin.checked_in_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </div>
                        <div className="kca-meta-item">
                          <User className="w-3 h-3" />
                          {checkin.child?.parent_name || 'Unknown'}
                        </div>
                      </div>
                      
                      <button
                        className="kca-checkout-btn"
                        onClick={() => setShowCheckoutModal(checkin)}
                        data-testid={`checkout-btn-${checkin.id}`}
                      >
                        <UserX className="w-4 h-4" />
                        Check Out
                      </button>
                    </motion.div>
                  );
                })
              )}
            </motion.div>
          )}

          {/* Check In Tab */}
          {activeTab === 'checkin' && (
            <motion.div
              key="checkin"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <div className="kca-search-box">
                <Search className="w-5 h-5" />
                <input
                  type="text"
                  placeholder="Search by child or parent name..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  data-testid="search-kids-input"
                />
              </div>
              
              <div className="kca-kids-list">
                {availableForCheckin.length === 0 ? (
                  <div className="kca-empty">
                    <span className="kca-empty-emoji">✅</span>
                    <h3>All Registered Kids Are Checked In!</h3>
                    <p>Or no kids match your search criteria</p>
                  </div>
                ) : (
                  availableForCheckin.map((kid) => {
                    const avatarStyle = getAvatarStyle(kid.name);
                    return (
                      <div 
                        key={kid.id} 
                        className="kca-kid-row"
                        data-testid={`kid-row-${kid.id}`}
                      >
                        <div 
                          className="kca-kid-avatar"
                          style={{ background: avatarStyle.bg }}
                        >
                          {kid.name.charAt(0)}
                        </div>
                        <div className="kca-kid-info">
                          <h4>{kid.name}</h4>
                          <div className="kca-kid-details">
                            <span>🎂 {formatAge(kid.birthdate)}</span>
                            <span>👤 {kid.parent_name}</span>
                            {kid.allergies && (
                              <span className="kca-allergy-small">
                                <AlertCircle className="w-3 h-3" />
                                {kid.allergies}
                              </span>
                            )}
                          </div>
                        </div>
                        <button
                          className="kca-checkin-btn"
                          onClick={() => handleDirectCheckin(kid)}
                          data-testid={`direct-checkin-btn-${kid.id}`}
                        >
                          <UserCheck className="w-4 h-4" />
                          Check In
                        </button>
                      </div>
                    );
                  })
                )}
              </div>
            </motion.div>
          )}

          {/* Check Out Tab */}
          {activeTab === 'checkout' && (
            <motion.div
              key="checkout"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="kca-checkout-tab"
            >
              {/* Mode Selection */}
              {checkoutMode === 'choose' && !scanResult && (
                <div className="kca-checkout-modes" data-testid="checkout-mode-select">
                  <h2 style={{textAlign:'center', marginBottom: 8}}>Check Out a Child</h2>
                  <p style={{textAlign:'center', color:'#64748b', marginBottom: 24}}>Choose how to verify the pickup code</p>
                  <div style={{display:'flex', gap: 16, justifyContent:'center', flexWrap:'wrap'}}>
                    <button
                      className="kca-mode-btn"
                      onClick={startQrScanner}
                      data-testid="scan-qr-btn"
                      style={{display:'flex', flexDirection:'column', alignItems:'center', gap: 12, padding: '24px 32px', background:'#f0fdf4', border:'2px solid #22c55e', borderRadius: 16, cursor:'pointer', minWidth: 180}}
                    >
                      <Camera className="w-10 h-10" style={{color:'#22c55e'}} />
                      <span style={{fontWeight: 600, fontSize: 16}}>Scan QR Code</span>
                      <span style={{fontSize: 12, color:'#64748b'}}>Camera permission required</span>
                    </button>
                    <button
                      className="kca-mode-btn"
                      onClick={() => setCheckoutMode('manual')}
                      data-testid="manual-code-btn"
                      style={{display:'flex', flexDirection:'column', alignItems:'center', gap: 12, padding: '24px 32px', background:'#eff6ff', border:'2px solid #3b82f6', borderRadius: 16, cursor:'pointer', minWidth: 180}}
                    >
                      <Keyboard className="w-10 h-10" style={{color:'#3b82f6'}} />
                      <span style={{fontWeight: 600, fontSize: 16}}>Enter Code Manually</span>
                      <span style={{fontSize: 12, color:'#64748b'}}>Type the 3-digit code</span>
                    </button>
                  </div>
                </div>
              )}

              {/* QR Scanner Mode */}
              {checkoutMode === 'scan' && (
                <div className="kca-scanner-section" data-testid="qr-scanner-section">
                  <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom: 16}}>
                    <h2>Scan Parent's QR Code</h2>
                    <button onClick={stopQrScanner} style={{padding:'8px 16px', background:'#ef4444', color:'white', border:'none', borderRadius:8, cursor:'pointer'}}>
                      Stop Scanner
                    </button>
                  </div>
                  <div id="qr-reader" style={{width: '100%', maxWidth: 400, margin: '0 auto', borderRadius: 12, overflow:'hidden'}}></div>
                  <p style={{textAlign:'center', marginTop: 12, color:'#64748b'}}>
                    Point the camera at the QR code on the parent's phone
                  </p>
                  <button
                    onClick={() => { stopQrScanner(); setCheckoutMode('manual'); }}
                    style={{display:'block', margin:'16px auto', padding:'10px 20px', background:'none', border:'1px solid #cbd5e1', borderRadius:8, cursor:'pointer', color:'#475569'}}
                  >
                    Switch to manual code entry
                  </button>
                </div>
              )}

              {/* Manual Code Entry Mode */}
              {checkoutMode === 'manual' && !scanResult && (
                <div className="kca-verify-section" data-testid="manual-code-section">
                  <div className="kca-verify-icon">
                    <Keyboard className="w-12 h-12" />
                  </div>
                  <h2>Enter Pickup Code</h2>
                  <p>Parents show their 3-digit pickup code from the app</p>
                  
                  <div className="kca-verify-input-group">
                    <input
                      type="text"
                      placeholder="Enter 3-digit code"
                      value={pickupCode}
                      onChange={(e) => setPickupCode(e.target.value)}
                      className="kca-verify-input"
                      maxLength={6}
                      inputMode="numeric"
                      style={{fontSize: 24, textAlign:'center', letterSpacing: 8}}
                      data-testid="pickup-code-input"
                    />
                    <button 
                      className="kca-verify-btn"
                      onClick={handleVerifyCode}
                      data-testid="verify-code-btn"
                    >
                      Verify Code
                    </button>
                  </div>
                  <button
                    onClick={() => { setCheckoutMode('choose'); setPickupCode(''); setVerifyResult(null); }}
                    style={{display:'block', margin:'16px auto', padding:'10px 20px', background:'none', border:'1px solid #cbd5e1', borderRadius:8, cursor:'pointer', color:'#475569'}}
                  >
                    Back to checkout options
                  </button>
                </div>
              )}

              {/* Scan Result */}
              {scanResult && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="kca-verify-result valid"
                  style={{textAlign:'center'}}
                >
                  {scanResult.success ? (
                    <>
                      <CheckCircle2 className="w-16 h-16" style={{color:'#22c55e', margin:'0 auto 16px'}} />
                      <h3 style={{fontSize: 20, marginBottom: 8}}>{scanResult.child_name} Checked Out!</h3>
                      <p style={{color:'#64748b'}}>Checkout time: {new Date(scanResult.checkout_time).toLocaleTimeString()}</p>
                    </>
                  ) : (
                    <>
                      <AlertCircle className="w-16 h-16" style={{color:'#ef4444', margin:'0 auto 16px'}} />
                      <h3>{scanResult.message || 'Invalid Code'}</h3>
                    </>
                  )}
                  <button
                    onClick={() => { setScanResult(null); setCheckoutMode('choose'); }}
                    style={{marginTop: 20, padding:'12px 24px', background:'#3b82f6', color:'white', border:'none', borderRadius:10, cursor:'pointer', fontSize: 16}}
                  >
                    Check Out Another Child
                  </button>
                </motion.div>
              )}

              {/* Verification Result (for manual code) */}
              <AnimatePresence>
                {verifyResult && checkoutMode === 'manual' && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    className={`kca-verify-result ${verifyResult.valid ? 'valid' : 'invalid'}`}
                  >
                    {verifyResult.valid ? (
                      <>
                        <div className="kca-result-header">
                          <CheckCircle2 className="w-8 h-8 text-green-500" />
                          <h3>Valid Pickup Code</h3>
                        </div>
                        
                        <div className="kca-result-child">
                          <div 
                            className="kca-result-avatar"
                            style={{ background: getAvatarStyle(verifyResult.child?.name || 'A').bg }}
                          >
                            {verifyResult.child?.name?.charAt(0) || '?'}
                          </div>
                          <div className="kca-result-info">
                            <h4>{verifyResult.child?.name}</h4>
                            <p>🎂 {formatAge(verifyResult.child?.birthdate)}</p>
                            {verifyResult.child?.allergies && (
                              <div className="kca-allergy-badge">
                                <AlertCircle className="w-3 h-3" />
                                {verifyResult.child.allergies}
                              </div>
                            )}
                          </div>
                        </div>
                        
                        <div className="kca-result-parent">
                          <h5>Authorized Pickup</h5>
                          <div className="kca-parent-info">
                            <span><User className="w-4 h-4" /> {verifyResult.parent?.name}</span>
                            {verifyResult.parent?.phone && (
                              <span><Phone className="w-4 h-4" /> {verifyResult.parent.phone}</span>
                            )}
                          </div>
                        </div>
                        
                        <button
                          className="kca-release-btn"
                          onClick={() => handleCheckout(verifyResult.checkin.id)}
                          data-testid="release-child-btn"
                        >
                          <Shield className="w-5 h-5" />
                          Release Child to Parent
                        </button>
                      </>
                    ) : (
                      <div className="kca-invalid-result">
                        <AlertCircle className="w-12 h-12 text-red-500" />
                        <h3>Invalid Pickup Code</h3>
                        <p>This code doesn't match any checked-in child. Please verify and try again.</p>
                      </div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Checkout Confirmation Modal */}
      <AnimatePresence>
        {showCheckoutModal && (
          <motion.div
            className="kca-modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowCheckoutModal(null)}
          >
            <motion.div
              className="kca-modal"
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="kca-modal-icon">
                <PartyPopper className="w-10 h-10" />
              </div>
              <h2>Check Out {showCheckoutModal.child?.name}?</h2>
              <p>Pickup Code: <strong>{showCheckoutModal.pickup_code}</strong></p>
              <p className="kca-modal-warning">
                Please verify the parent's identity before releasing the child
              </p>
              
              <div className="kca-modal-parent">
                <User className="w-4 h-4" />
                <span>{showCheckoutModal.child?.parent_name}</span>
                {showCheckoutModal.child?.parent_phone && (
                  <>
                    <Phone className="w-4 h-4" />
                    <span>{showCheckoutModal.child.parent_phone}</span>
                  </>
                )}
              </div>
              
              <div className="kca-modal-actions">
                <button 
                  className="kca-modal-cancel"
                  onClick={() => setShowCheckoutModal(null)}
                >
                  Cancel
                </button>
                <button 
                  className="kca-modal-confirm"
                  onClick={() => handleCheckout(showCheckoutModal.id)}
                  data-testid="confirm-checkout-btn"
                >
                  <CheckCircle2 className="w-5 h-5" />
                  Confirm Checkout
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
        
        
        {/* Manual Check-In Modal */}
        {showManualCheckin && (
          <motion.div
            className="kca-modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowManualCheckin(false)}
          >
            <motion.div
              className="kca-modal kca-register-modal"
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              data-testid="manual-checkin-modal"
            >
              <div className="kca-modal-icon" style={{ background: '#eff6ff' }}>
                <UserCheck className="w-10 h-10" style={{ color: '#3b82f6' }} />
              </div>
              <h2>Manual Check-In</h2>
              <p className="kca-modal-subtitle">Search for a child and check them in directly</p>
              
              <div style={{ marginTop: 16 }}>
                <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
                  <input
                    type="text"
                    placeholder="Search child or parent name..."
                    value={manualSearch}
                    onChange={(e) => setManualSearch(e.target.value)}
                    style={{ flex: 1, padding: '10px 14px', borderRadius: 10, border: '2px solid #e2e8f0', fontSize: 14 }}
                    data-testid="manual-checkin-search"
                  />
                  <select
                    value={manualClassroom}
                    onChange={(e) => setManualClassroom(e.target.value)}
                    style={{ padding: '10px 14px', borderRadius: 10, border: '2px solid #e2e8f0', fontSize: 14 }}
                    data-testid="manual-checkin-classroom"
                  >
                    <option>Sunday School</option>
                    <option>Nursery</option>
                    <option>Preschool</option>
                    <option>Elementary</option>
                    <option>Youth Room</option>
                  </select>
                </div>
                
                <div style={{ maxHeight: 300, overflowY: 'auto' }}>
                  {allKids.filter(kid => 
                    !checkins.some(c => c.child_id === kid.id) &&
                    (kid.name?.toLowerCase().includes(manualSearch.toLowerCase()) ||
                     kid.parent_name?.toLowerCase().includes(manualSearch.toLowerCase()))
                  ).map(kid => {
                    const avatarStyle = getAvatarStyle(kid.name);
                    return (
                      <div key={kid.id} style={{
                        display: 'flex', alignItems: 'center', gap: 12, padding: '10px 12px',
                        borderRadius: 10, border: '1px solid #e2e8f0', marginBottom: 8,
                        background: '#f8fafc'
                      }} data-testid={`manual-kid-${kid.id}`}>
                        <div style={{
                          width: 40, height: 40, borderRadius: '50%', display: 'flex',
                          alignItems: 'center', justifyContent: 'center', color: 'white',
                          fontWeight: 700, fontSize: 16, background: avatarStyle.bg
                        }}>
                          {kid.name?.charAt(0)}
                        </div>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontWeight: 600, fontSize: 14, color: '#1e293b' }}>{kid.name}</div>
                          <div style={{ fontSize: 12, color: '#64748b' }}>{kid.parent_name} &middot; {formatAge(kid.birthdate)}</div>
                        </div>
                        <button
                          onClick={() => handleDirectCheckin(kid)}
                          style={{
                            padding: '8px 16px', background: '#3b82f6', color: 'white',
                            border: 'none', borderRadius: 8, fontSize: 13, fontWeight: 600,
                            cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6
                          }}
                          data-testid={`manual-checkin-kid-${kid.id}`}
                        >
                          <UserCheck style={{ width: 16, height: 16 }} />
                          Check In
                        </button>
                      </div>
                    );
                  })}
                  {allKids.filter(kid => 
                    !checkins.some(c => c.child_id === kid.id) &&
                    (kid.name?.toLowerCase().includes(manualSearch.toLowerCase()) ||
                     kid.parent_name?.toLowerCase().includes(manualSearch.toLowerCase()))
                  ).length === 0 && (
                    <div style={{ textAlign: 'center', padding: 24, color: '#94a3b8' }}>
                      No available children found
                    </div>
                  )}
                </div>
              </div>
              
              <div className="kca-modal-actions" style={{ marginTop: 16 }}>
                <button className="kca-modal-cancel" onClick={() => setShowManualCheckin(false)}>Close</button>
              </div>
            </motion.div>
          </motion.div>
        )}
        
        {/* Register New Family Modal */}
        {showRegisterFamily && (
          <motion.div
            className="kca-modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowRegisterFamily(false)}
          >
            <motion.div
              className="kca-modal kca-register-modal"
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              data-testid="register-family-modal"
            >
              <div className="kca-modal-icon kca-modal-icon-green">
                <Users className="w-10 h-10" />
              </div>
              <h2>Register New Family ✝️</h2>
              <p className="kca-modal-subtitle">Welcome a new family to Sunday School!</p>
              
              <div className="kca-register-form">
                <div className="kca-form-section">
                  <h3><User className="w-4 h-4" /> Parent Information</h3>
                  <div className="kca-form-row">
                    <input
                      type="text"
                      placeholder="Parent Name *"
                      value={newFamily.parentName}
                      onChange={(e) => setNewFamily(prev => ({ ...prev, parentName: e.target.value }))}
                      data-testid="parent-name-input"
                    />
                    <input
                      type="email"
                      placeholder="Email *"
                      value={newFamily.parentEmail}
                      onChange={(e) => setNewFamily(prev => ({ ...prev, parentEmail: e.target.value }))}
                      data-testid="parent-email-input"
                    />
                  </div>
                  <input
                    type="tel"
                    placeholder="Phone Number"
                    value={newFamily.parentPhone}
                    onChange={(e) => setNewFamily(prev => ({ ...prev, parentPhone: e.target.value }))}
                    data-testid="parent-phone-input"
                  />
                </div>
                
                <div className="kca-form-section">
                  <h3><Sparkles className="w-4 h-4" /> Child Information</h3>
                  <div className="kca-form-row">
                    <input
                      type="text"
                      placeholder="Child Name *"
                      value={newFamily.childName}
                      onChange={(e) => setNewFamily(prev => ({ ...prev, childName: e.target.value }))}
                      data-testid="child-name-input"
                    />
                    <input
                      type="date"
                      placeholder="Birthdate"
                      value={newFamily.childBirthdate}
                      onChange={(e) => setNewFamily(prev => ({ ...prev, childBirthdate: e.target.value }))}
                      data-testid="child-birthdate-input"
                    />
                  </div>
                  <input
                    type="text"
                    placeholder="Allergies (if any)"
                    value={newFamily.childAllergies}
                    onChange={(e) => setNewFamily(prev => ({ ...prev, childAllergies: e.target.value }))}
                  />
                  <textarea
                    placeholder="Special notes (e.g., special needs, preferences)"
                    value={newFamily.childNotes}
                    onChange={(e) => setNewFamily(prev => ({ ...prev, childNotes: e.target.value }))}
                    rows={2}
                  />
                </div>
              </div>
              
              <div className="kca-modal-actions">
                <button 
                  className="kca-modal-cancel"
                  onClick={() => setShowRegisterFamily(false)}
                >
                  Cancel
                </button>
                <button 
                  className="kca-modal-confirm kca-modal-confirm-green"
                  onClick={handleRegisterFamily}
                  data-testid="submit-register-btn"
                >
                  <CheckCircle2 className="w-5 h-5" />
                  Register Family
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
