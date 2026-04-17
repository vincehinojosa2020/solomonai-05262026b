import { motion } from 'framer-motion';
import { QrCode, Camera, Keyboard, Shield } from 'lucide-react';

export function CheckOutTab({
  checkoutMode, setCheckoutMode,
  pickupCode, setPickupCode,
  verifyResult, handleVerifyPickup,
  scannerActive, setScannerActive,
  scannerRef, handleManualInput,
  scanResult, setScanResult,
  handleCheckout
}) {
  return (
    <motion.div
      key="checkout"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="kca-checkout-section"
    >
      {checkoutMode === 'choose' && (
        <div className="kca-checkout-choose" role="group" aria-label="Choose checkout method">
          <h3 style={{ fontSize: 18, fontWeight: 700, color: '#1e293b', marginBottom: 16 }}>How would you like to check out?</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, maxWidth: 400 }}>
            <button
              className="kca-method-btn"
              onClick={() => { setCheckoutMode('scan'); setScannerActive(true); }}
              data-testid="checkout-scan-btn"
              aria-label="Scan QR code for checkout"
            >
              <Camera className="w-6 h-6" />
              <span>Scan QR</span>
            </button>
            <button
              className="kca-method-btn"
              onClick={() => setCheckoutMode('manual')}
              data-testid="checkout-manual-btn"
              aria-label="Enter pickup code manually"
            >
              <Keyboard className="w-6 h-6" />
              <span>Manual Code</span>
            </button>
          </div>
        </div>
      )}

      {checkoutMode === 'scan' && (
        <div className="kca-scanner-section">
          <div ref={scannerRef} id="qr-reader" style={{ width: '100%', maxWidth: 400, margin: '0 auto', borderRadius: 12, overflow: 'hidden' }} />
          {scanResult && (
            <div className="kca-scan-result" role="status" aria-live="polite">
              <Shield className="w-5 h-5" />
              <span>Code scanned: {scanResult}</span>
            </div>
          )}
          <button className="kca-back-btn" onClick={() => { setCheckoutMode('choose'); setScannerActive(false); setScanResult(null); }}>
            Back to options
          </button>
        </div>
      )}

      {checkoutMode === 'manual' && (
        <div className="kca-manual-checkout">
          <h3 style={{ marginBottom: 12, fontWeight: 700, color: '#1e293b' }}>Enter Pickup Code</h3>
          <div className="kca-code-input-row">
            <input
              type="text"
              placeholder="Enter 6-character pickup code"
              value={pickupCode}
              onChange={(e) => setPickupCode(e.target.value.toUpperCase())}
              className="kca-code-input"
              maxLength={6}
              data-testid="pickup-code-input"
              aria-label="Pickup code"
            />
            <button
              className="kca-verify-btn"
              onClick={handleVerifyPickup}
              disabled={pickupCode.length < 4}
              data-testid="verify-pickup-btn"
              aria-label="Verify pickup code"
            >
              <Shield className="w-4 h-4" /> Verify
            </button>
          </div>
          {verifyResult && (
            <div className={`kca-verify-result ${verifyResult.valid ? 'valid' : 'invalid'}`} role="status" aria-live="polite">
              {verifyResult.valid ? (
                <>
                  <p style={{ fontWeight: 600, margin: '0 0 4px 0' }}>Match found: {verifyResult.child_name}</p>
                  <p style={{ fontSize: 13, color: '#64748b', margin: '0 0 8px 0' }}>Parent: {verifyResult.parent_name}</p>
                  <button className="kca-complete-checkout-btn" onClick={() => handleCheckout(verifyResult.checkin_id)} data-testid="complete-checkout-btn">
                    Complete Checkout
                  </button>
                </>
              ) : (
                <p style={{ color: '#dc2626', fontWeight: 600 }}>Invalid pickup code. Please try again.</p>
              )}
            </div>
          )}
          <button className="kca-back-btn" onClick={() => { setCheckoutMode('choose'); setPickupCode(''); }} style={{ marginTop: 12 }}>
            Back to options
          </button>
        </div>
      )}
    </motion.div>
  );
}
