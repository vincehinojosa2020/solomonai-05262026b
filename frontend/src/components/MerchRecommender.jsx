import { useState, useRef, useEffect } from 'react';
import { Sparkles, X, Send, ShoppingBag } from 'lucide-react';

// UI-only recommender — uses pattern matching to suggest products
const RECOMMENDATIONS = {
  shirt: { q: ['shirt', 'tee', 'top', 'wear'], response: 'I\'d recommend our **Faith Over Fear Tee** — it\'s our best seller! Also check out the **Abundant Life Hoodie** for cooler days.' },
  hat: { q: ['hat', 'cap', 'headwear'], response: 'Our **Sunday Best Snapback** is super popular! It comes in navy and black. Perfect for outdoor events.' },
  hoodie: { q: ['hoodie', 'sweatshirt', 'warm', 'cold', 'winter'], response: 'The **Abundant Life Hoodie** is cozy and stylish! Available in charcoal and forest green. Great for worship nights.' },
  gift: { q: ['gift', 'present', 'someone', 'birthday'], response: 'For gifts, our **Journal & Pen Set** is a thoughtful choice! The **Worship Candle** is also a beautiful option.' },
  kids: { q: ['kid', 'child', 'youth', 'young', 'boy', 'girl'], response: 'We have **Kids Faith Tees** in fun colors! The **Adventure Bible Cover** is great for Sunday School too.' },
  mug: { q: ['mug', 'cup', 'coffee', 'drink'], response: 'The **Psalm 23 Mug** is perfect for morning devotions! We also have a **Blessed Tumbler** for on-the-go.' },
  bag: { q: ['bag', 'tote', 'carry'], response: 'Our **Sunday Tote Bag** is spacious and durable — great for carrying your Bible, journal, and more!' },
  new: { q: ['new', 'latest', 'just dropped', 'fresh'], response: 'Just in! Our **Spring Collection** features pastel tees and lightweight hoodies. Check them out above!' },
  popular: { q: ['popular', 'best', 'top', 'favorite', 'recommend'], response: 'Our top 3 right now: 1) **Faith Over Fear Tee** 2) **Abundant Life Hoodie** 3) **Psalm 23 Mug**. All crowd favorites!' },
};

const GREETING = 'Hey there! I\'m Solomon\'s Merch Assistant. Ask me about shirts, hoodies, gifts, or what\'s popular — I\'ll help you find something great!';

function getResponse(input) {
  const lower = input.toLowerCase();
  for (const rec of Object.values(RECOMMENDATIONS)) {
    if (rec.q.some(keyword => lower.includes(keyword))) {
      return rec.response;
    }
  }
  return 'Great question! Browse our collection above — we have tees, hoodies, hats, mugs, bags, and more. Try asking me about **shirts**, **gifts**, or what\'s **popular**!';
}

export default function MerchRecommender() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'assistant', text: GREETING }
  ]);
  const [input, setInput] = useState('');
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    if (!input.trim()) return;
    const userMsg = { role: 'user', text: input.trim() };
    const botMsg = { role: 'assistant', text: getResponse(input) };
    setMessages(prev => [...prev, userMsg, botMsg]);
    setInput('');
  };

  // Format bold text
  const formatText = (text) =>
    text.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
      part.startsWith('**') && part.endsWith('**')
        ? <strong key={i}>{part.slice(2, -2)}</strong>
        : part
    );

  return (
    <>
      {/* Floating button */}
      {!open && (
        <button
          data-testid="merch-recommender-btn"
          onClick={() => setOpen(true)}
          style={{
            position: 'fixed', bottom: '24px', right: '24px', zIndex: 9990,
            width: '56px', height: '56px', borderRadius: '50%',
            background: 'linear-gradient(135deg, #f59e0b, #ef4444)',
            border: 'none', cursor: 'pointer', color: '#fff',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 4px 20px rgba(245,158,11,0.4)',
            transition: 'transform 0.2s',
          }}
          onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.1)'}
          onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
        >
          <Sparkles className="w-6 h-6" />
        </button>
      )}

      {/* Chat panel */}
      {open && (
        <div
          data-testid="merch-recommender-panel"
          style={{
            position: 'fixed', bottom: '24px', right: '24px', zIndex: 9990,
            width: '340px', maxHeight: '460px',
            background: '#fff', borderRadius: '16px',
            border: '1px solid #e2e8f0',
            boxShadow: '0 10px 40px rgba(0,0,0,0.15)',
            display: 'flex', flexDirection: 'column', overflow: 'hidden',
          }}
        >
          {/* Header */}
          <div style={{
            padding: '12px 16px', background: 'linear-gradient(135deg, #f59e0b, #ef4444)',
            color: '#fff', display: 'flex', alignItems: 'center', gap: '8px',
          }}>
            <ShoppingBag className="w-5 h-5" />
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '14px', fontWeight: '700' }}>Solomon Merch</div>
              <div style={{ fontSize: '10px', opacity: 0.8 }}>Your personal shopping assistant</div>
            </div>
            <button
              data-testid="merch-recommender-close"
              onClick={() => setOpen(false)}
              style={{ background: 'rgba(255,255,255,0.2)', border: 'none', borderRadius: '50%', width: '28px', height: '28px', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', color: '#fff' }}
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Messages */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {messages.map((msg, i) => (
              <div
                key={i}
                style={{
                  alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  maxWidth: '85%',
                  padding: '8px 12px',
                  borderRadius: msg.role === 'user' ? '12px 12px 4px 12px' : '12px 12px 12px 4px',
                  background: msg.role === 'user' ? '#f59e0b' : '#f8fafc',
                  color: msg.role === 'user' ? '#fff' : '#1e293b',
                  fontSize: '13px', lineHeight: 1.5,
                  border: msg.role === 'user' ? 'none' : '1px solid #e2e8f0',
                }}
              >
                {formatText(msg.text)}
              </div>
            ))}
            <div ref={endRef} />
          </div>

          {/* Quick suggestions */}
          {messages.length <= 2 && (
            <div style={{ padding: '0 12px 8px', display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              {['What\'s popular?', 'Gift ideas', 'Hoodies'].map(q => (
                <button
                  key={q}
                  onClick={() => { setInput(q); }}
                  data-testid={`merch-quick-${q.toLowerCase().replace(/[^a-z]/g, '')}`}
                  style={{
                    fontSize: '11px', padding: '4px 10px', borderRadius: '99px',
                    border: '1px solid #e5e7eb', background: '#fff', cursor: 'pointer',
                    color: '#475569', fontWeight: '500',
                  }}
                >
                  {q}
                </button>
              ))}
            </div>
          )}

          {/* Input */}
          <div style={{ display: 'flex', gap: '6px', padding: '8px 12px 12px', borderTop: '1px solid #f1f5f9' }}>
            <input
              data-testid="merch-recommender-input"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSend()}
              placeholder="Ask about merch..."
              style={{ flex: 1, padding: '8px 12px', border: '1px solid #e5e7eb', borderRadius: '8px', fontSize: '13px', outline: 'none' }}
            />
            <button
              data-testid="merch-recommender-send"
              onClick={handleSend}
              disabled={!input.trim()}
              style={{
                width: '36px', height: '36px', borderRadius: '8px',
                background: input.trim() ? '#f59e0b' : '#e5e7eb',
                border: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center',
                cursor: input.trim() ? 'pointer' : 'not-allowed',
                color: input.trim() ? '#fff' : '#94a3b8',
              }}
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </>
  );
}
