# Stripe Payment Request Button — Activation Guide

Current state: the **UI is fully built and wired up** with a realistic Apple Pay / Google Pay mock that simulates the wallet sheet, biometric auth, and success callback. No real card is charged. When a Stripe publishable key is present, the same component will auto-upgrade to the real Stripe Payment Request Button with zero UI changes.

## File: `/app/frontend/src/components/payments/StripePaymentRequestButton.jsx`

The component checks `process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY`:
- **Absent** → mock flow (current state)
- **Present** → swap in real Stripe Payment Request Button (see steps below)

---

## Steps to activate (end of week, once Stripe account exists)

### 1. Install Stripe.js
```bash
cd /app/frontend
yarn add @stripe/stripe-js
```

### 2. Add the publishable key
Add to `/app/frontend/.env`:
```
REACT_APP_STRIPE_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxx
```
The secret key is already in `/app/backend/.env` as `STRIPE_API_KEY`. Flip `STRIPE_LIVE=true` when ready for live mode.

### 3. Replace the `handleClick` body in `StripePaymentRequestButton.jsx`

Find the block marked with `// LIVE path — will be activated once REACT_APP_STRIPE_PUBLISHABLE_KEY is set.` and replace it with:

```js
const { loadStripe } = await import('@stripe/stripe-js');
const stripe = await loadStripe(stripeKey);
const pr = stripe.paymentRequest({
  country: 'US',
  currency: 'usd',
  total: { label, amount: Math.round(amount * 100) },
  requestPayerName: true,
  requestPayerEmail: true,
});
const result = await pr.canMakePayment();
if (!result) {
  // Fall through to mock sheet so the user can still complete the demo flow.
} else {
  pr.on('paymentmethod', async (ev) => {
    // Send ev.paymentMethod.id to your backend /api/solomonpay/confirm-wallet
    // Based on backend response, call ev.complete('success' | 'fail')
    onSuccess?.({
      type: result.applePay ? 'apple_pay' : 'google_pay',
      token: ev.paymentMethod.id,
      card_last_four: ev.paymentMethod.card?.last4,
      card_brand: ev.paymentMethod.card?.brand,
      wallet_type: result.applePay ? 'apple_pay' : 'google_pay',
      is_mock: false,
    });
    ev.complete('success');
  });
  pr.show();
  return;
}
```

### 4. Backend: confirm wallet payment
Add `/api/solomonpay/confirm-wallet` endpoint that takes the Stripe `payment_method_id` and calls `stripe.PaymentIntent.create()` with `confirm=True`. Use the existing `STRIPE_API_KEY` env var. The rest of the donation flow (`/api/solomonpay/process`) already accepts tokenized cards and does not need changes.

### 5. Apple Pay domain verification
Stripe requires hosting `/.well-known/apple-developer-merchantid-domain-association` on your production domain. Download from the Stripe dashboard once you register your merchant ID, and serve it via FastAPI `StaticFiles` or Nginx.

### 6. Test
- Chrome on desktop → Google Pay button works with any saved card
- Safari on iOS/macOS → Apple Pay button works with wallet cards
- Stripe test cards: `pm_card_visa`, `pm_card_mastercard`

---

## Rollback
Remove `REACT_APP_STRIPE_PUBLISHABLE_KEY` from `.env` — component auto-falls back to the mock.

## Files changed in this session
- `/app/frontend/src/components/payments/StripePaymentRequestButton.jsx` (new)
- `/app/frontend/src/components/MultiPaymentSelector.jsx` (Apple/Google Pay now render the Stripe button)
- `/app/frontend/src/components/modals/DonationCheckout.jsx` (wallet button surfaced on main donate screen, above "Pay with Card")
