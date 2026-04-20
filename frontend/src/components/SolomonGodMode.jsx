import { useState, useEffect, useRef, useCallback } from 'react';
import {
  X, Send, Sparkles, ChevronRight, Loader2, Trash2, Mic, MicOff,
  Download, FileText, FileSpreadsheet, BarChart3, TrendingUp,
  Building2, Users, DollarSign, Brain, StopCircle
} from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';
import DOMPurify from 'dompurify';
import { safeRedirect } from '@/utils/sanitize';

const SAMPLE_PROMPTS = [
  { text: "Give me an investor summary of our platform", icon: TrendingUp },
  { text: "Compare church performance — who's growing fastest?", icon: Building2 },
  { text: "What's our blended take rate and how does it compare to Stripe?", icon: DollarSign },
  { text: "Model our ARR at 25 and 50 churches", icon: BarChart3 },
  { text: "Analyze donor retention across the portfolio", icon: Users },
  { text: "Generate a Series A data room summary", icon: FileText },
];

const formatMessage = (content) => {
  if (!content) return '';
  let html = content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/```([\s\S]*?)```/g, '<pre class="bg-slate-800 text-slate-200 rounded-lg p-3 text-xs overflow-x-auto my-2"><code>$1</code></pre>')
    .replace(/\|(.+)\|/g, (match) => {
      const cells = match.split('|').filter(Boolean).map(c => c.trim());
      if (cells.every(c => /^[-:]+$/.test(c))) return '';
      return `<div class="flex gap-4 text-xs py-0.5">${cells.map(c => `<span class="flex-1">${c}</span>`).join('')}</div>`;
    })
    .replace(/^#{1,3}\s+(.+)/gm, '<p class="font-bold text-sm mt-3 mb-1">$1</p>')
    .replace(/^- (.+)/gm, '<div class="flex gap-1.5 text-xs ml-2"><span class="text-blue-400">•</span><span>$1</span></div>')
    .replace(/\n\n/g, '<br/><br/>')
    .replace(/\n/g, '<br/>');
  return html;
};

export default function SolomonGodMode({ isOpen, onClose }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);

  const getAuth = () => {
    const t = sessionStorage.getItem('session_token');
    return t ? { Authorization: `Bearer ${t}` } : {};
  };

  useEffect(() => {
    if (isOpen && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 300);
    }
  }, [isOpen]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const sendMessage = useCallback(async (text) => {
    if (!text?.trim() || loading) return;
    const userMsg = { role: 'user', content: text, ts: Date.now() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/solomon/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuth() },
        body: JSON.stringify({ message: text, session_id: sessionId }),
      });
      if (!res.ok) throw new Error('Failed');
      const data = await res.json();
      setSessionId(data.session_id);

      const assistantMsg = {
        role: 'assistant',
        content: data.response,
        actions: data.actions,
        pending_action: data.pending_action,
        ts: Date.now(),
      };
      setMessages(prev => [...prev, assistantMsg]);

      // Auto-handle report generation actions
      if (data.pending_action?.action_type === 'generate_report') {
        handleReportAction(data.pending_action.params);
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: "I'm having trouble connecting. Let me try again — give me a moment.",
        isError: true, ts: Date.now(),
      }]);
    } finally {
      setLoading(false);
    }
  }, [loading, sessionId]);

  const handleReportAction = async (params) => {
    try {
      const res = await fetch(`${API_URL}/solomon/generate-report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuth() },
        body: JSON.stringify(params),
      });
      const data = await res.json();
      if (data.success) {
        setMessages(prev => [...prev, {
          role: 'system',
          content: `Report generated: **${data.filename}**`,
          download_url: data.download_url,
          filename: data.filename,
          ts: Date.now(),
        }]);
        toast.success('Report ready for download');
      }
    } catch (err) {
      toast.error('Failed to generate report');
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, sampleRate: 16000 }
      });
      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach(t => t.stop());
        clearInterval(timerRef.current);
        setIsRecording(false);

        if (chunksRef.current.length === 0) return;

        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        setIsTranscribing(true);

        try {
          const formData = new FormData();
          formData.append('audio', blob, 'recording.webm');

          const res = await fetch(`${API_URL}/solomon/voice-transcribe`, {
            method: 'POST',
            headers: getAuth(),
            body: formData,
          });

          if (!res.ok) throw new Error('Transcription failed');
          const data = await res.json();

          if (data.transcript) {
            setInput(data.transcript);
            toast.success(`Transcribed ${Math.round(recordingTime)}s of audio`);
          }
        } catch (err) {
          toast.error('Voice transcription failed. Please try again.');
        } finally {
          setIsTranscribing(false);
          setRecordingTime(0);
        }
      };

      mediaRecorderRef.current = recorder;
      recorder.start(1000);
      setIsRecording(true);
      setRecordingTime(0);
      timerRef.current = setInterval(() => setRecordingTime(t => t + 1), 1000);
      toast.info('Recording started — speak freely, then click stop when done');
    } catch (err) {
      toast.error('Microphone access denied');
    }
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
  };

  const clearChat = async () => {
    if (sessionId) {
      try { await fetch(`${API_URL}/solomon/session/${sessionId}`, { method: 'DELETE', headers: getAuth() }); } catch {}
    }
    setMessages([]);
    setSessionId(null);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  const fmtTime = (s) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-full sm:w-[480px] bg-slate-950 border-l border-slate-800 shadow-2xl z-50 flex flex-col" data-testid="solomon-godmode-sidebar">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-slate-800 bg-gradient-to-r from-slate-950 to-slate-900">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white tracking-wide">Solomon</h3>
            <p className="text-[10px] text-blue-400 font-medium">Strategic Advisor • McKinsey • CPA</p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          {messages.length > 0 && (
            <button onClick={clearChat} className="p-2 text-slate-500 hover:text-slate-300 hover:bg-slate-800 rounded-lg transition-colors" data-testid="solomon-gm-clear">
              <Trash2 className="w-4 h-4" />
            </button>
          )}
          <button onClick={onClose} className="p-2 text-slate-500 hover:text-white hover:bg-slate-800 rounded-lg transition-colors" data-testid="solomon-gm-close">
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4" data-testid="solomon-gm-messages">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center px-4">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500/20 to-indigo-600/20 border border-blue-500/20 flex items-center justify-center mb-5">
              <Brain className="w-8 h-8 text-blue-400" />
            </div>
            <h4 className="text-lg font-bold text-white mb-1">Ask Solomon Anything</h4>
            <p className="text-xs text-slate-500 mb-6 max-w-xs leading-relaxed">
              Your AI strategic advisor with McKinsey-grade analysis, CPA expertise, and full platform visibility. Voice-enabled for extended briefings.
            </p>
            <div className="grid grid-cols-1 gap-2 w-full max-w-sm">
              {SAMPLE_PROMPTS.map((p, i) => (
                <button key={i} onClick={() => sendMessage(p.text)}
                  className="flex items-center gap-2.5 px-3 py-2.5 bg-slate-900 border border-slate-800 rounded-lg text-left hover:border-blue-500/40 hover:bg-slate-800/50 transition-all group"
                  data-testid={`solomon-gm-prompt-${i}`}
                >
                  <p.icon className="w-3.5 h-3.5 text-slate-600 group-hover:text-blue-400 flex-shrink-0 transition-colors" />
                  <span className="text-xs text-slate-400 group-hover:text-slate-200 transition-colors">{p.text}</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg, i) => (
            <div key={i} className={`flex gap-2.5 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`} data-testid={`solomon-gm-msg-${i}`}>
              {msg.role !== 'user' && (
                <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500/20 to-indigo-600/20 border border-blue-500/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                  {msg.role === 'system' ? <FileText className="w-3 h-3 text-emerald-400" /> : <Brain className="w-3 h-3 text-blue-400" />}
                </div>
              )}
              <div className={`max-w-[85%] ${msg.role === 'user' ? 'bg-blue-600 text-white rounded-2xl rounded-tr-md px-3.5 py-2.5' : 'bg-slate-900 border border-slate-800 text-slate-200 rounded-2xl rounded-tl-md px-3.5 py-2.5'}`}>
                <div className="text-[13px] leading-relaxed" dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(formatMessage(msg.content)) }} />
                {msg.download_url && (
                  <a href={`${API_URL}${msg.download_url}`} download={msg.filename}
                    className="inline-flex items-center gap-1.5 mt-2 px-3 py-1.5 bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 rounded-lg text-xs font-medium hover:bg-emerald-500/30 transition-colors"
                    data-testid={`solomon-gm-download-${i}`}
                  >
                    <Download className="w-3 h-3" /> {msg.filename}
                  </a>
                )}
                {msg.actions?.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {msg.actions.map((a, j) => (
                      <button key={j} onClick={() => window.location.href = safeRedirect(a.path)}
                        className="flex items-center gap-1 px-2.5 py-1 bg-blue-500/20 border border-blue-500/30 text-blue-400 rounded-md text-xs hover:bg-blue-500/30 transition-colors"
                      >
                        {a.label} <ChevronRight className="w-3 h-3" />
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        {loading && (
          <div className="flex gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500/20 to-indigo-600/20 border border-blue-500/10 flex items-center justify-center flex-shrink-0">
              <Brain className="w-3 h-3 text-blue-400 animate-pulse" />
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-2xl rounded-tl-md px-3.5 py-2.5 flex items-center gap-2">
              <Loader2 className="w-3.5 h-3.5 text-blue-400 animate-spin" />
              <span className="text-xs text-slate-500">Solomon is analyzing...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Recording indicator */}
      {isRecording && (
        <div className="px-4 py-2 bg-red-950/50 border-t border-red-500/20 flex items-center justify-between" data-testid="solomon-gm-recording">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
            <span className="text-xs text-red-400 font-medium">Recording — {fmtTime(recordingTime)}</span>
          </div>
          <button onClick={stopRecording} className="flex items-center gap-1.5 px-3 py-1 bg-red-500/20 border border-red-500/30 text-red-400 rounded-lg text-xs font-medium hover:bg-red-500/30 transition-colors" data-testid="solomon-gm-stop-recording">
            <StopCircle className="w-3 h-3" /> Stop & Transcribe
          </button>
        </div>
      )}

      {isTranscribing && (
        <div className="px-4 py-2 bg-blue-950/50 border-t border-blue-500/20 flex items-center gap-2" data-testid="solomon-gm-transcribing">
          <Loader2 className="w-3.5 h-3.5 text-blue-400 animate-spin" />
          <span className="text-xs text-blue-400 font-medium">Transcribing your recording with Whisper...</span>
        </div>
      )}

      {/* Input */}
      <div className="border-t border-slate-800 bg-slate-950 px-4 py-3">
        <div className="flex items-end gap-2">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={isRecording ? "Recording in progress..." : "Ask Solomon about your numbers, strategy, compliance..."}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder:text-slate-600 resize-none focus:outline-none focus:ring-1 focus:ring-blue-500/50 focus:border-blue-500/50"
              rows={input.length > 100 ? 3 : 1}
              disabled={loading || isRecording}
              data-testid="solomon-gm-input"
            />
          </div>
          <button
            onClick={isRecording ? stopRecording : startRecording}
            disabled={loading || isTranscribing}
            className={`p-2.5 rounded-xl transition-all flex-shrink-0 ${isRecording ? 'bg-red-500 text-white animate-pulse shadow-lg shadow-red-500/30' : 'bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700'}`}
            title={isRecording ? 'Stop recording' : 'Start voice recording (Whisper)'}
            data-testid="solomon-gm-mic"
          >
            {isRecording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
          </button>
          <button
            onClick={() => sendMessage(input)}
            disabled={!input.trim() || loading}
            className="p-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-500 transition-colors disabled:opacity-30 disabled:cursor-not-allowed flex-shrink-0"
            data-testid="solomon-gm-send"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        <div className="flex items-center justify-between mt-2">
          <p className="text-[10px] text-slate-600">Powered by Anthropic Claude • Voice by OpenAI Whisper</p>
          <div className="flex gap-1">
            <button onClick={() => handleReportAction({ report_type: 'investor_summary', format: 'csv', title: 'Investor Summary' })}
              className="text-[10px] text-slate-600 hover:text-blue-400 flex items-center gap-1 transition-colors" data-testid="solomon-gm-export-csv">
              <FileSpreadsheet className="w-3 h-3" /> Export CSV
            </button>
            <span className="text-[10px] text-slate-700">|</span>
            <button onClick={() => handleReportAction({ report_type: 'investor_summary', format: 'markdown', title: 'Investor Summary' })}
              className="text-[10px] text-slate-600 hover:text-blue-400 flex items-center gap-1 transition-colors" data-testid="solomon-gm-export-report">
              <FileText className="w-3 h-3" /> Generate Report
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
