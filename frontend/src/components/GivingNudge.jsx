import { useState } from 'react';
import { Heart, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

/**
 * Reusable Giving Nudge Component (Module 10 - v3.0)
 * 
 * A warm, never-pushy offering prompt that can be used across all transaction moments:
 * - After café order confirmation
 * - After merch checkout
 * - After event registration
 * - After watching a sermon (90%+ completion)
 * - Dashboard nudge for lapsed givers
 * 
 * Philosophy: The nudge must be warm, never pushy, always optional, always dismissable.
 */

const PRESET_AMOUNTS = [5, 10, 20];

export default function GivingNudge({
  churchName = 'our church',
  context = 'order', // 'order' | 'event' | 'sermon' | 'reminder'
  onAmountSelect,
  onDismiss,
  className = ''
}) {
  const [selectedAmount, setSelectedAmount] = useState(0);
  const [customAmount, setCustomAmount] = useState('');
  const [showCustom, setShowCustom] = useState(false);

  const contextMessages = {
    order: {
      title: 'Add an Offering?',
      subtitle: `Your generosity helps ${churchName} do more.`,
      cta: 'Add to Order',
    },
    event: {
      title: 'Support This Event',
      subtitle: 'Help cover event costs with a small offering.',
      cta: 'Add Offering',
    },
    sermon: {
      title: 'Moved by Today\'s Message?',
      subtitle: 'Your gift helps spread the Word.',
      cta: 'Give Now',
    },
    reminder: {
      title: 'We Miss You!',
      subtitle: `It's been a while since your last gift. ${churchName} is grateful for your support.`,
      cta: 'Give Today',
    },
  };

  const message = contextMessages[context] || contextMessages.order;

  const handleAmountClick = (amount) => {
    if (selectedAmount === amount) {
      setSelectedAmount(0);
      onAmountSelect?.(0);
    } else {
      setSelectedAmount(amount);
      setShowCustom(false);
      onAmountSelect?.(amount);
    }
  };

  const handleCustomSubmit = () => {
    const amount = parseFloat(customAmount);
    if (!isNaN(amount) && amount > 0) {
      setSelectedAmount(amount);
      onAmountSelect?.(amount);
    }
  };

  return (
    <div className={`giving-nudge ${className}`} data-testid="giving-nudge">
      <div className="giving-nudge-header">
        <Heart className="giving-nudge-icon" />
        <span className="giving-nudge-title">{message.title}</span>
        {onDismiss && (
          <button 
            className="giving-nudge-dismiss" 
            onClick={onDismiss}
            aria-label="Dismiss"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
      
      <p className="giving-nudge-subtitle">{message.subtitle}</p>
      
      <div className="giving-nudge-amounts">
        {PRESET_AMOUNTS.map((amount) => (
          <button
            key={amount}
            className={`giving-nudge-btn ${selectedAmount === amount ? 'active' : ''}`}
            onClick={() => handleAmountClick(amount)}
            data-testid={`giving-nudge-${amount}`}
          >
            ${amount}
          </button>
        ))}
        <button
          className={`giving-nudge-btn custom ${showCustom ? 'active' : ''}`}
          onClick={() => setShowCustom(!showCustom)}
          data-testid="giving-nudge-custom"
        >
          Custom
        </button>
      </div>

      <AnimatePresence>
        {showCustom && (
          <motion.div
            className="giving-nudge-custom-input"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
          >
            <div className="giving-nudge-custom-row">
              <span>$</span>
              <input
                type="number"
                placeholder="Enter amount"
                value={customAmount}
                onChange={(e) => setCustomAmount(e.target.value)}
                min="1"
                step="0.01"
                data-testid="giving-nudge-custom-input"
              />
              <button 
                className="giving-nudge-custom-submit"
                onClick={handleCustomSubmit}
              >
                Set
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {selectedAmount > 0 && (
        <div className="giving-nudge-selected">
          <span>Offering: ${selectedAmount.toFixed(2)}</span>
          <button 
            className="giving-nudge-clear"
            onClick={() => {
              setSelectedAmount(0);
              onAmountSelect?.(0);
            }}
          >
            No thanks
          </button>
        </div>
      )}

      <p className="giving-nudge-footer">
        100% of your offering goes directly to {churchName}
      </p>
    </div>
  );
}

// Export named variations for specific contexts
export const CafeGivingNudge = (props) => (
  <GivingNudge context="order" {...props} />
);

export const MerchGivingNudge = (props) => (
  <GivingNudge context="order" {...props} />
);

export const EventGivingNudge = (props) => (
  <GivingNudge context="event" {...props} />
);

export const SermonGivingNudge = (props) => (
  <GivingNudge context="sermon" {...props} />
);

export const ReminderGivingNudge = (props) => (
  <GivingNudge context="reminder" {...props} />
);
