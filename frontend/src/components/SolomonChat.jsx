import { useState, useEffect, useRef } from 'react';
import { MessageSquare, X, Send, Sparkles, ChevronRight, Loader2, Trash2 } from 'lucide-react';
import { API_URL } from '@/lib/utils';

const SolomonChat = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Sample prompts to get started
  const samplePrompts = [
    "How do I access Abundant Pathways?",
    "Where can I watch the latest sermons?",
    "How do I join a group?",
    "What events are coming up?",
    "Where can I find the merch store?",
    "Can I order coffee from Abundant Cafe?",
    "How is my giving making an impact?"
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
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSend = async (message = inputValue) => {
    if (!message.trim() || isLoading) return;

    const userMessage = { role: 'user', content: message };
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await fetch(`${API_URL}/solomon/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: message,
          session_id: sessionId
        })
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
    // Convert markdown-style formatting to HTML
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
        data-testid="samson-fab"
        aria-label="Ask Solomon"
      >
        <Sparkles className="w-5 h-5" />
        <span className="solomon-fab-label">Ask Solomon</span>
      </button>

      {/* Chat Panel */}
      <div className={`solomon-panel ${isOpen ? 'open' : ''}`} data-testid="samson-panel">
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
                data-testid="samson-clear-btn"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
            <button
              onClick={() => setIsOpen(false)}
              className="solomon-close-btn"
              data-testid="samson-close-btn"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="solomon-messages" data-testid="samson-messages">
          {messages.length === 0 ? (
            <div className="solomon-welcome">
              <div className="solomon-welcome-icon">
                <Sparkles className="w-8 h-8" />
              </div>
              <h4>Welcome! I'm Solomon</h4>
              <p>Your AI-powered church analyst. I can help you understand your data, provide pastoral insights, and suggest strategic actions.</p>
              
              <div className="solomon-prompts">
                <p className="solomon-prompts-label">Try asking:</p>
                {samplePrompts.map((prompt, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(prompt)}
                    className="solomon-prompt-btn"
                    data-testid={`samson-prompt-${idx}`}
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
                className={`solomon-message ${msg.role}`}
                data-testid={`samson-message-${idx}`}
              >
                {msg.role === 'assistant' && (
                  <div className="solomon-message-avatar">
                    <Sparkles className="w-3 h-3" />
                  </div>
                )}
                <div className={`solomon-message-content ${msg.isError ? 'error' : ''}`}>
                  <div dangerouslySetInnerHTML={{ __html: formatMessage(msg.content) }} />
                  
                  {/* Action Buttons */}
                  {msg.actions && msg.actions.length > 0 && (
                    <div className="solomon-actions">
                      {msg.actions.map((action, actionIdx) => (
                        <button
                          key={actionIdx}
                          onClick={() => handleActionClick(action)}
                          className="solomon-action-btn"
                          data-testid={`samson-action-${actionIdx}`}
                        >
                          {action.label}
                          <ChevronRight className="w-3 h-3" />
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))
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
            placeholder="Ask Solomon anything about your church..."
            className="solomon-input"
            rows={1}
            disabled={isLoading}
            data-testid="samson-input"
          />
          <button
            onClick={() => handleSend()}
            disabled={!inputValue.trim() || isLoading}
            className="solomon-send-btn"
            data-testid="samson-send-btn"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Backdrop */}
      {isOpen && (
        <div 
          className="solomon-backdrop" 
          onClick={() => setIsOpen(false)}
          data-testid="samson-backdrop"
        />
      )}
    </>
  );
};

export default SolomonChat;
