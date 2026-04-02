import { useState, useEffect, useRef } from 'react';
import { MessageSquare, X, Send, Sparkles, ChevronRight, Loader2, Trash2, Mic, Check, XCircle, ShoppingBag, Heart, Users, Calendar, Baby } from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

const ACTION_ICONS = {
  cafe_order: ShoppingBag,
  merch_order: ShoppingBag,
  donation: Heart,
  recurring_giving: Heart,
  event_registration: Calendar,
  group_join: Users,
  checkin: Baby,
};

const ACTION_COLORS = {
  cafe_order: 'from-amber-500/20 to-orange-500/20 border-amber-500/30',
  merch_order: 'from-indigo-500/20 to-purple-500/20 border-indigo-500/30',
  donation: 'from-emerald-500/20 to-green-500/20 border-emerald-500/30',
  recurring_giving: 'from-emerald-500/20 to-teal-500/20 border-emerald-500/30',
  event_registration: 'from-blue-500/20 to-cyan-500/20 border-blue-500/30',
  group_join: 'from-violet-500/20 to-purple-500/20 border-violet-500/30',
  checkin: 'from-pink-500/20 to-rose-500/20 border-pink-500/30',
};

const ActionConfirmCard = ({ action, onConfirm, onCancel, isExecuting }) => {
  const Icon = ACTION_ICONS[action.action_type] || Sparkles;
  const colorClass = ACTION_COLORS[action.action_type] || 'from-gray-500/20 to-gray-500/20 border-gray-500/30';

  return (
    <div
      className={`bg-gradient-to-br ${colorClass} border rounded-lg p-3 my-2 animate-in slide-in-from-bottom-2`}
      data-testid="solomon-action-confirm-card"
    >
      <div className="flex items-start gap-2 mb-2">
        <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center shrink-0">
          <Icon className="w-4 h-4 text-white/80" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-white/60 uppercase tracking-wide">Confirm Action</p>
          <p className="text-sm text-white/90 mt-0.5">{action.display_summary}</p>
        </div>
      </div>
      <div className="flex gap-2 mt-2">
        <button
          onClick={onConfirm}
          disabled={isExecuting}
          className="flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 bg-white/15 hover:bg-white/25 text-white text-xs font-medium rounded-md transition-colors disabled:opacity-50"
          data-testid="solomon-action-confirm-btn"
        >
          {isExecuting ? (
            <Loader2 className="w-3 h-3 animate-spin" />
          ) : (
            <Check className="w-3 h-3" />
          )}
          {isExecuting ? 'Processing...' : 'Confirm'}
        </button>
        <button
          onClick={onCancel}
          disabled={isExecuting}
          className="flex items-center justify-center gap-1.5 px-3 py-1.5 bg-white/5 hover:bg-white/10 text-white/60 text-xs font-medium rounded-md transition-colors disabled:opacity-50"
          data-testid="solomon-action-cancel-btn"
        >
          <XCircle className="w-3 h-3" />
          Cancel
        </button>
      </div>
    </div>
  );
};

const SolomonChat = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [pendingAction, setPendingAction] = useState(null);
  const [isExecutingAction, setIsExecutingAction] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const recognitionRef = useRef(null);

  const samplePrompts = [
    "Order me a latte from the cafe",
    "Give $50 to missions fund",
    "Sign me up for men's breakfast",
    "Join the young professionals group",
    "How is my giving making an impact?",
    "What events are coming up?",
    "Where can I watch the latest sermons?"
  ];

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  useEffect(() => {
    const handler = () => setIsOpen(true);
    window.addEventListener('solomon:open', handler);
    return () => window.removeEventListener('solomon:open', handler);
  }, []);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setSpeechSupported(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = true;
    recognition.continuous = false;

    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map((result) => result[0].transcript)
        .join('');
      setInputValue(transcript);
      if (event.results[0]?.isFinal) {
        setIsListening(false);
      }
    };

    recognition.onerror = () => {
      setIsListening(false);
      toast.error('Voice input failed. Please try again.');
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;
    setSpeechSupported(true);
  }, []);

  const toggleListening = () => {
    if (!speechSupported) {
      toast.error('Voice input is not supported in this browser.');
      return;
    }
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      return;
    }
    try {
      recognitionRef.current?.start();
      setIsListening(true);
    } catch {
      setIsListening(false);
      toast.error('Unable to start voice input.');
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isOpen, pendingAction]);

  const handleSend = async (message = inputValue) => {
    if (!message.trim() || isLoading) return;

    const userMessage = { role: 'user', content: message };
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setPendingAction(null);

    try {
      const response = await fetch(`${API_URL}/solomon/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, session_id: sessionId })
      });

      if (!response.ok) throw new Error('Failed to get response');

      const data = await response.json();
      setSessionId(data.session_id);

      const assistantMessage = {
        role: 'assistant',
        content: data.response,
        actions: data.actions,
        data: data.data
      };
      setMessages(prev => [...prev, assistantMessage]);

      if (data.pending_action) {
        setPendingAction(data.pending_action);
      }
    } catch (error) {
      console.error('Solomon chat error:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: "I apologize, but I'm having trouble connecting right now. Please try again in a moment.",
        isError: true
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirmAction = async () => {
    if (!pendingAction || isExecutingAction) return;
    setIsExecutingAction(true);

    try {
      const response = await fetch(`${API_URL}/solomon/execute-action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          action_type: pendingAction.action_type,
          params: pendingAction.params
        })
      });

      const result = await response.json();

      if (result.success) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: result.message,
          isActionResult: true,
          navigate: result.navigate
        }]);
        toast.success(result.message);
      } else {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: result.message || 'Action could not be completed.',
          isError: true
        }]);
        toast.error(result.message || 'Action failed');
      }
    } catch (error) {
      console.error('Action execution error:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Failed to execute action. Please try again.',
        isError: true
      }]);
      toast.error('Failed to execute action');
    } finally {
      setPendingAction(null);
      setIsExecutingAction(false);
    }
  };

  const handleCancelAction = () => {
    setPendingAction(null);
    setMessages(prev => [...prev, {
      role: 'assistant',
      content: "No problem! Action cancelled. Is there anything else I can help you with?"
    }]);
  };

  const handleClearChat = async () => {
    if (sessionId) {
      try {
        await fetch(`${API_URL}/solomon/session/${sessionId}`, { method: 'DELETE' });
      } catch (error) {
        console.error('Failed to clear session:', error);
      }
    }
    setMessages([]);
    setSessionId(null);
    setPendingAction(null);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleActionClick = (action) => {
    if (action.action === 'navigate' && action.path) {
      window.location.href = action.path;
    }
  };

  const formatMessage = (content) => {
    let formatted = content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br />');
    return formatted;
  };

  return (
    <>
      {/* Floating Button */}
      <button
        onClick={() => setIsOpen(true)}
        className={`solomon-fab ${isOpen ? 'hidden' : ''}`}
        data-testid="solomon-fab"
        aria-label="Ask Solomon"
      >
        <Sparkles className="w-5 h-5" />
        <span className="solomon-fab-label">Ask Solomon</span>
      </button>

      {/* Chat Panel */}
      <div className={`solomon-panel ${isOpen ? 'open' : ''}`} data-testid="solomon-panel">
        {/* Header */}
        <div className="solomon-header">
          <div className="flex items-center gap-2">
            <div className="solomon-avatar">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h3 className="solomon-title">Solomon</h3>
              <p className="solomon-subtitle">AI Church Assistant</p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            {messages.length > 0 && (
              <button
                onClick={handleClearChat}
                className="solomon-clear-btn"
                title="Clear conversation"
                data-testid="solomon-clear-btn"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
            <button
              onClick={() => setIsOpen(false)}
              className="solomon-close-btn"
              data-testid="solomon-close-btn"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="solomon-messages" data-testid="solomon-messages">
          {messages.length === 0 ? (
            <div className="solomon-welcome">
              <div className="solomon-welcome-icon">
                <Sparkles className="w-8 h-8" />
              </div>
              <h4>Welcome! I'm Solomon</h4>
              <p>Your AI-powered church assistant. I can help you find info, place orders, make donations, register for events, and more — just ask or tap the mic!</p>
              
              <div className="solomon-prompts">
                <p className="solomon-prompts-label">Try saying:</p>
                {samplePrompts.map((prompt, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(prompt)}
                    className="solomon-prompt-btn"
                    data-testid={`solomon-prompt-${idx}`}
                  >
                    <MessageSquare className="w-3 h-3" />
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div
                key={idx}
                className={`solomon-message ${msg.role} ${msg.isActionResult ? 'action-result' : ''}`}
                data-testid={`solomon-message-${idx}`}
              >
                {msg.role === 'assistant' && (
                  <div className={`solomon-message-avatar ${msg.isActionResult ? 'success' : ''}`}>
                    {msg.isActionResult ? <Check className="w-3 h-3" /> : <Sparkles className="w-3 h-3" />}
                  </div>
                )}
                <div className={`solomon-message-content ${msg.isError ? 'error' : ''} ${msg.isActionResult ? 'action-success' : ''}`}>
                  <div dangerouslySetInnerHTML={{ __html: formatMessage(msg.content) }} />
                  
                  {/* Navigation Action Buttons */}
                  {msg.actions && msg.actions.length > 0 && (
                    <div className="solomon-actions">
                      {msg.actions.map((action, actionIdx) => (
                        <button
                          key={actionIdx}
                          onClick={() => handleActionClick(action)}
                          className="solomon-action-btn"
                          data-testid={`solomon-action-${actionIdx}`}
                        >
                          {action.label}
                          <ChevronRight className="w-3 h-3" />
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Navigate button for action results */}
                  {msg.navigate && (
                    <button
                      onClick={() => { window.location.href = msg.navigate; }}
                      className="solomon-action-btn mt-2"
                      data-testid={`solomon-navigate-${idx}`}
                    >
                      View Details
                      <ChevronRight className="w-3 h-3" />
                    </button>
                  )}
                </div>
              </div>
            ))
          )}
          
          {/* Pending Action Confirmation */}
          {pendingAction && (
            <ActionConfirmCard
              action={pendingAction}
              onConfirm={handleConfirmAction}
              onCancel={handleCancelAction}
              isExecuting={isExecutingAction}
            />
          )}

          {isLoading && (
            <div className="solomon-message assistant">
              <div className="solomon-message-avatar">
                <Sparkles className="w-3 h-3" />
              </div>
              <div className="solomon-message-content loading">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Solomon is thinking...</span>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="solomon-input-container">
          <textarea
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={pendingAction ? "Confirm or cancel the action above..." : "Ask Solomon anything..."}
            className="solomon-input"
            rows={1}
            disabled={isLoading || isExecutingAction}
            data-testid="solomon-input"
          />
          <button
            onClick={toggleListening}
            disabled={isLoading || isExecutingAction}
            className={`solomon-mic-btn ${isListening ? 'listening' : ''}`}
            data-testid="solomon-mic-btn"
            aria-label="Voice input"
          >
            <Mic className="w-4 h-4" />
          </button>
          <button
            onClick={() => handleSend()}
            disabled={!inputValue.trim() || isLoading || isExecutingAction}
            className="solomon-send-btn"
            data-testid="solomon-send-btn"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        {isListening && (
          <div className="solomon-mic-status" data-testid="solomon-mic-status">
            Listening... tap mic to stop
          </div>
        )}
      </div>

      {/* Backdrop */}
      {isOpen && (
        <div 
          className="solomon-backdrop" 
          onClick={() => setIsOpen(false)}
          data-testid="solomon-backdrop"
        />
      )}
    </>
  );
};

export default SolomonChat;
