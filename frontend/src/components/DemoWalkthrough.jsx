import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronRight, ChevronLeft, X, Sparkles } from 'lucide-react';

const MEMBER_STEPS = [
  {
    target: '[data-testid="portal-nav-kids-check-in"]',
    title: 'Kids Check-In',
    body: 'Start here! Tap to check in your child for Sunday School.',
    position: 'bottom',
    route: '/portal',
  },
  {
    target: '.kc-child-card',
    title: 'Your Children',
    body: 'You\'ll see your registered children here. Baby Hinojosa is ready to check in!',
    position: 'bottom',
    route: '/portal/kids',
  },
  {
    target: '[data-testid^="checkin-btn-"]',
    title: 'Tap Check In',
    body: 'Hit this button to check in your child. A QR code and pickup code will appear.',
    position: 'left',
    route: '/portal/kids',
  },
  {
    target: '[data-testid^="qr-code-"], [data-testid="checkin-qr-code"]',
    title: 'Your QR Code',
    body: 'Show this QR code to the admin at pickup. They\'ll scan it to release your child safely.',
    position: 'top',
    route: '/portal/kids',
  },
  {
    target: '.kc-pickup-code .kc-code-value',
    title: 'Pickup Code',
    body: 'This 3-digit code is your backup. The admin can also type it in manually.',
    position: 'top',
    route: '/portal/kids',
  },
];

const ADMIN_STEPS = [
  {
    target: 'a[href*="kids"]',
    title: 'Kids Check-In Admin',
    body: 'This is your command center. See all checked-in children in real-time.',
    position: 'right',
    route: null,
  },
  {
    target: '.kca-stat-big',
    title: 'Live Counter',
    body: 'This updates every 2 seconds. You\'ll see the count go up when a parent checks in.',
    position: 'bottom',
    route: null,
  },
  {
    target: '.kca-child-card',
    title: 'Checked-In Children',
    body: 'Each card shows the child\'s name, pickup code, check-in time, and parent info.',
    position: 'bottom',
    route: null,
  },
  {
    target: '[data-testid="checkout-mode-select"], .kca-checkout-tab',
    title: 'Check Out Options',
    body: 'Two ways to check out: Scan the parent\'s QR code with your camera, or type the 3-digit code.',
    position: 'bottom',
    route: null,
  },
  {
    target: '[data-testid="scan-qr-btn"]',
    title: 'Scan QR Code',
    body: 'Tap to open your camera. Point it at the parent\'s phone screen to scan their QR code.',
    position: 'right',
    route: null,
  },
  {
    target: '[data-testid="manual-code-btn"]',
    title: 'Manual Code Entry',
    body: 'If scanning doesn\'t work, tap here and type the 3-digit pickup code instead.',
    position: 'left',
    route: null,
  },
];

export default function DemoWalkthrough({ userRole, userName, onNavigate }) {
  const [active, setActive] = useState(false);
  const [step, setStep] = useState(0);
  const [dismissed, setDismissed] = useState(false);
  const [showWelcome, setShowWelcome] = useState(false);

  const storageKey = `solomon_walkthrough_${userRole}`;
  const loginCountKey = `solomon_login_count_${userRole}`;
  const steps = userRole === 'church_admin' ? ADMIN_STEPS : MEMBER_STEPS;

  useEffect(() => {
    const count = parseInt(sessionStorage.getItem(loginCountKey) || '0', 10);
    const seen = sessionStorage.getItem(storageKey);
    if (!seen && count < 2) {
      const timer = setTimeout(() => setShowWelcome(true), 1500);
      return () => clearTimeout(timer);
    }
  }, [storageKey, loginCountKey]);

  const startWalkthrough = () => {
    setShowWelcome(false);
    setActive(true);
    setStep(0);
    // Navigate to the first step's route if needed
    if (steps[0].route && onNavigate) {
      onNavigate(steps[0].route);
    }
  };

  const skipAll = () => {
    setShowWelcome(false);
    setActive(false);
    setDismissed(true);
    sessionStorage.setItem(storageKey, 'true');
  };

  const nextStep = useCallback(() => {
    if (step < steps.length - 1) {
      const next = step + 1;
      setStep(next);
      if (steps[next].route && onNavigate) {
        onNavigate(steps[next].route);
      }
    } else {
      setActive(false);
      sessionStorage.setItem(storageKey, 'true');
    }
  }, [step, steps, onNavigate, storageKey]);

  const prevStep = () => {
    if (step > 0) {
      const prev = step - 1;
      setStep(prev);
      if (steps[prev].route && onNavigate) {
        onNavigate(steps[prev].route);
      }
    }
  };

  // Find target element position
  const [tooltipPos, setTooltipPos] = useState({ top: 0, left: 0 });
  const [targetRect, setTargetRect] = useState(null);

  useEffect(() => {
    if (!active) return;
    const currentStep = steps[step];
    if (!currentStep) return;

    const findTarget = () => {
      const el = document.querySelector(currentStep.target);
      if (el) {
        const rect = el.getBoundingClientRect();
        setTargetRect(rect);

        let top, left;
        switch (currentStep.position) {
          case 'bottom':
            top = rect.bottom + 12;
            left = rect.left + rect.width / 2;
            break;
          case 'top':
            top = rect.top - 12;
            left = rect.left + rect.width / 2;
            break;
          case 'left':
            top = rect.top + rect.height / 2;
            left = rect.left - 12;
            break;
          case 'right':
            top = rect.top + rect.height / 2;
            left = rect.right + 12;
            break;
          default:
            top = rect.bottom + 12;
            left = rect.left + rect.width / 2;
        }
        setTooltipPos({ top, left });
      } else {
        setTargetRect(null);
      }
    };

    findTarget();
    const interval = setInterval(findTarget, 500);
    return () => clearInterval(interval);
  }, [active, step, steps]);

  if (dismissed && !active) return null;

  return (
    <>
      {/* Welcome Modal */}
      <AnimatePresence>
        {showWelcome && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{
              position: 'fixed', inset: 0, zIndex: 10000,
              background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              padding: 20,
            }}
            onClick={skipAll}
          >
            <motion.div
              initial={{ scale: 0.85, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.85, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              style={{
                background: 'white', borderRadius: 20, padding: '32px 28px',
                maxWidth: 380, width: '100%', textAlign: 'center',
                boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
              }}
            >
              <div style={{
                width: 64, height: 64, borderRadius: '50%',
                background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                margin: '0 auto 20px',
              }}>
                <Sparkles style={{ color: 'white', width: 32, height: 32 }} />
              </div>
              <h2 style={{ fontSize: 22, fontWeight: 700, margin: '0 0 8px', color: '#0f172a' }}>
                Welcome, {userName}!
              </h2>
              <p style={{ fontSize: 15, color: '#64748b', margin: '0 0 24px', lineHeight: 1.5 }}>
                {userRole === 'church_admin'
                  ? 'Ready to manage Kids Check-In? Let me show you how the QR checkout works.'
                  : 'Ready to check in your child? Let me walk you through the QR code flow.'}
              </p>
              <button
                onClick={startWalkthrough}
                data-testid="start-walkthrough-btn"
                style={{
                  width: '100%', padding: '14px 24px', borderRadius: 12,
                  background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                  color: 'white', border: 'none', fontSize: 16, fontWeight: 600,
                  cursor: 'pointer', marginBottom: 12,
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                }}
              >
                Start Quick Tour
                <ChevronRight style={{ width: 18, height: 18 }} />
              </button>
              <button
                onClick={skipAll}
                data-testid="skip-walkthrough-btn"
                style={{
                  background: 'none', border: 'none', color: '#94a3b8',
                  fontSize: 14, cursor: 'pointer', padding: '8px 16px',
                }}
              >
                I'll figure it out myself
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Walkthrough Overlay */}
      <AnimatePresence>
        {active && (
          <>
            {/* Spotlight overlay */}
            <div
              style={{
                position: 'fixed', inset: 0, zIndex: 9998,
                pointerEvents: 'none',
              }}
            >
              {targetRect && (
                <svg width="100%" height="100%" style={{ position: 'absolute', inset: 0 }}>
                  <defs>
                    <mask id="spotlight-mask">
                      <rect width="100%" height="100%" fill="white" />
                      <rect
                        x={targetRect.left - 8}
                        y={targetRect.top - 8}
                        width={targetRect.width + 16}
                        height={targetRect.height + 16}
                        rx="12"
                        fill="black"
                      />
                    </mask>
                  </defs>
                  <rect
                    width="100%" height="100%"
                    fill="rgba(0,0,0,0.5)"
                    mask="url(#spotlight-mask)"
                  />
                </svg>
              )}
            </div>

            {/* Click blocker (except on target) */}
            <div
              style={{
                position: 'fixed', inset: 0, zIndex: 9999,
                cursor: 'pointer',
              }}
              onClick={nextStep}
            />

            {/* Tooltip */}
            <motion.div
              key={step}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
              style={{
                position: 'fixed',
                top: Math.min(tooltipPos.top, window.innerHeight - 200),
                left: Math.max(16, Math.min(tooltipPos.left - 160, window.innerWidth - 336)),
                zIndex: 10001,
                width: 320,
                background: 'white',
                borderRadius: 16,
                padding: '20px',
                boxShadow: '0 12px 40px rgba(0,0,0,0.25)',
                border: '2px solid #3b82f6',
              }}
              data-testid="walkthrough-tooltip"
            >
              {/* Step indicator */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <div style={{ display: 'flex', gap: 4 }}>
                  {steps.map((_, i) => (
                    <div
                      key={i}
                      style={{
                        width: i === step ? 20 : 8, height: 8, borderRadius: 4,
                        background: i === step ? '#3b82f6' : i < step ? '#93c5fd' : '#e2e8f0',
                        transition: 'all 0.3s',
                      }}
                    />
                  ))}
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); skipAll(); }}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 4, color: '#94a3b8' }}
                  data-testid="close-walkthrough-btn"
                >
                  <X style={{ width: 16, height: 16 }} />
                </button>
              </div>

              <h3 style={{ fontSize: 17, fontWeight: 700, color: '#0f172a', margin: '0 0 6px' }}>
                {steps[step].title}
              </h3>
              <p style={{ fontSize: 14, color: '#475569', margin: '0 0 16px', lineHeight: 1.5 }}>
                {steps[step].body}
              </p>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <button
                  onClick={(e) => { e.stopPropagation(); prevStep(); }}
                  disabled={step === 0}
                  style={{
                    padding: '8px 14px', borderRadius: 8, border: '1px solid #e2e8f0',
                    background: 'white', cursor: step === 0 ? 'default' : 'pointer',
                    opacity: step === 0 ? 0.4 : 1, fontSize: 13, color: '#475569',
                    display: 'flex', alignItems: 'center', gap: 4,
                  }}
                >
                  <ChevronLeft style={{ width: 14, height: 14 }} /> Back
                </button>
                <span style={{ fontSize: 12, color: '#94a3b8' }}>
                  {step + 1} / {steps.length}
                </span>
                <button
                  onClick={(e) => { e.stopPropagation(); nextStep(); }}
                  data-testid="walkthrough-next-btn"
                  style={{
                    padding: '8px 16px', borderRadius: 8, border: 'none',
                    background: '#3b82f6', color: 'white', cursor: 'pointer',
                    fontSize: 13, fontWeight: 600,
                    display: 'flex', alignItems: 'center', gap: 4,
                  }}
                >
                  {step === steps.length - 1 ? 'Done!' : 'Next'}
                  {step < steps.length - 1 && <ChevronRight style={{ width: 14, height: 14 }} />}
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
