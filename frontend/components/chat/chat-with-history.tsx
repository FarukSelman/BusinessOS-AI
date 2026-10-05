"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Bot, User as UserIcon, Wrench, MessageSquarePlus, MessageSquare, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { 
  sendChatMessage, 
  listChatSessions, 
  getChatSessionMessages, 
  deleteChatSession,
  ApiError,
  ChatSession,
  ChatMessage,
  PendingAgentAction,
  approveAgentAction,
  rejectAgentAction,
  notifyAgentActionsChanged,
} from "@/lib/api";
import { PendingActionCard, type ActionOutcome } from "@/components/chat/pending-action-card";
import { getActiveBusinessId } from "@/lib/business";
import { cn } from "@/lib/utils";
import { format } from "date-fns";
import { tr } from "date-fns/locale";

interface Message {
  role: "user" | "assistant";
  content: string;
  agentName?: string | null;
  toolsUsed?: string[] | null;
  pendingActions?: PendingAgentAction[] | null;
}

interface ChatWithHistoryProps {
  title: string;
  description: string;
  agentColor: string;
  examplePrompts?: string[];
}

export function ChatWithHistory({ title, description, agentColor, examplePrompts }: ChatWithHistoryProps) {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionOutcomes, setActionOutcomes] = useState<Record<string, ActionOutcome>>({});
  const bottomRef = useRef<HTMLDivElement>(null);

  const businessId = getActiveBusinessId();

  useEffect(() => {
    if (businessId) {
      loadSessions();
    }
  }, [businessId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function loadSessions() {
    if (!businessId) return;
    try {
      const data = await listChatSessions(businessId);
      setSessions(data);
    } catch (err) {
      console.error("Sohbet geçmişi yüklenemedi:", err);
    }
  }

  async function loadSessionMessages(sessionId: string) {
    if (!businessId) return;
    try {
      setLoading(true);
      const data = await getChatSessionMessages(businessId, sessionId);
      const formatted = data.map((m) => ({
        role: m.role.toLowerCase() as "user" | "assistant",
        content: m.content
      }));
      setMessages(formatted);
      setActiveSessionId(sessionId);
      setError(null);
    } catch (err) {
      console.error("Mesajlar yüklenemedi:", err);
    } finally {
      setLoading(false);
    }
  }

  function startNewChat() {
    setActiveSessionId(null);
    setMessages([]);
    setError(null);
  }

  async function handleDeleteSession(e: React.MouseEvent, sessionId: string) {
    e.stopPropagation();
    if (!businessId) return;
    if (!confirm("Sohbeti silmek istediğine emin misin?")) return;
    
    try {
      await deleteChatSession(businessId, sessionId);
      if (activeSessionId === sessionId) {
        startNewChat();
      }
      loadSessions();
    } catch (err) {
      console.error("Sohbet silinemedi:", err);
    }
  }

  async function sendQuestion(question: string) {
    if (!question.trim()) return;

    if (!businessId) {
      setError("Önce bir işletme seçmelisin.");
      return;
    }

    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setInput("");
    setError(null);
    setLoading(true);

    try {
      const response = await sendChatMessage(businessId, question, activeSessionId || undefined);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: response.answer,
          agentName: response.agent_name,
          toolsUsed: response.tools_used,
          pendingActions: response.pending_actions,
        },
      ]);
      if (response.pending_actions?.length) notifyAgentActionsChanged();

      if (!activeSessionId && response.conversation_id) {
        setActiveSessionId(response.conversation_id);
        loadSessions(); // reload list
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Mesaj gönderilemedi, tekrar dene.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    sendQuestion(input);
  }

  async function approveAction(actionId: string) {
    if (!businessId) return;
    try {
      setLoading(true);
      await approveAgentAction(businessId, actionId);
      setActionOutcomes((previous) => ({ ...previous, [actionId]: "approved" }));
      notifyAgentActionsChanged();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "İşlem onaylanamadı.");
    } finally {
      setLoading(false);
    }
  }

  async function rejectAction(actionId: string, reason: string) {
    if (!businessId) return;
    try {
      setLoading(true);
      await rejectAgentAction(businessId, actionId, reason);
      setActionOutcomes((previous) => ({ ...previous, [actionId]: "rejected" }));
      notifyAgentActionsChanged();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "İşlem reddedilemedi.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-4">
      {/* Sidebar */}
      <div className="flex w-64 shrink-0 flex-col overflow-hidden rounded-lg border border-border bg-surface-elevated/50 backdrop-blur-sm">
        <div className="p-3 border-b border-border">
          <Button onClick={startNewChat} className="w-full gap-2 justify-start" variant="outline">
            <MessageSquarePlus className="h-4 w-4" />
            Yeni Sohbet
          </Button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {sessions.length === 0 && (
            <p className="text-center text-xs text-ink-muted p-4">Geçmiş sohbet bulunamadı.</p>
          )}
          {sessions.map((s) => (
            <div
              key={s.id}
              onClick={() => loadSessionMessages(s.id)}
              className={cn(
                "group flex items-center justify-between rounded-md px-3 py-2 text-sm cursor-pointer transition-colors",
                activeSessionId === s.id ? "bg-accent/10 text-accent" : "hover:bg-surface-elevated text-ink-muted hover:text-ink"
              )}
            >
              <div className="flex items-center gap-2 truncate">
                <MessageSquare className="h-4 w-4 shrink-0" />
                <span className="truncate">{s.title || "Yeni Sohbet"}</span>
              </div>
              <button
                onClick={(e) => handleDeleteSession(e, s.id)}
                className="opacity-0 group-hover:opacity-100 hover:text-danger p-1"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <div className="border-l-2 pl-3 mb-4 shrink-0" style={{ borderColor: agentColor }}>
          <h1 className="font-display text-2xl font-semibold tracking-tight text-ink">
            {title}
          </h1>
          <p className="text-sm text-ink-muted">
            {description}
          </p>
        </div>

        <div className="flex flex-1 flex-col overflow-hidden rounded-lg border border-border bg-surface-elevated/50 backdrop-blur-sm">
          <div className="flex-1 space-y-4 overflow-y-auto p-4">
            {messages.length === 0 && (
              examplePrompts && examplePrompts.length > 0 ? (
                <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
                  <p className="text-sm text-ink-muted">Bir örnekle başla:</p>
                  <div className="flex flex-wrap justify-center gap-2 max-w-md">
                    {examplePrompts.map((p) => (
                      <button
                        key={p}
                        onClick={() => sendQuestion(p)}
                        className="rounded-full border border-border bg-surface px-3 py-1.5 text-xs font-medium text-ink hover:border-accent hover:text-accent transition-colors"
                      >
                        {p}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <p className="text-center text-sm text-ink-muted">
                  Henüz mesaj yok. Bir soru sorarak başla.
                </p>
              )
            )}

            {messages.map((m, i) => (
              <div
                key={i}
                className={cn("flex gap-3", m.role === "user" ? "flex-row-reverse" : "flex-row")}
              >
                <div
                  className={cn(
                    "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
                    m.role === "user" ? "bg-accent text-accent-ink" : "text-white"
                  )}
                  style={m.role === "assistant" ? { backgroundColor: agentColor } : undefined}
                >
                  {m.role === "user" ? <UserIcon className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                </div>
                <div
                  className={cn(
                    "max-w-[75%] rounded-2xl px-4 py-2 text-sm",
                    m.role === "user" ? "bg-accent text-accent-ink" : "bg-surface text-ink"
                  )}
                >
                  {m.agentName && (
                    <p
                      className="mb-1 text-xs font-semibold uppercase tracking-wide"
                      style={{ color: agentColor }}
                    >
                      {m.agentName}
                    </p>
                  )}
                  <p className="whitespace-pre-wrap">{m.content}</p>
                  {m.toolsUsed && m.toolsUsed.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1.5 border-t border-border pt-2">
                      {m.toolsUsed.map((tool, idx) => (
                        <span
                          key={`${tool}-${idx}`}
                          className="flex items-center gap-1 rounded-full bg-surface-elevated px-2 py-0.5 text-[10px] font-medium text-ink-muted"
                        >
                          <Wrench className="h-2.5 w-2.5" />
                          {tool}
                        </span>
                      ))}
                    </div>
                  )}
                  {m.pendingActions?.map((action) => (
                    <PendingActionCard
                      key={action.action_id}
                      action={action}
                      disabled={loading}
                      outcome={actionOutcomes[action.action_id]}
                      onApprove={approveAction}
                      onReject={rejectAction}
                    />
                  ))}
                </div>
              </div>
            ))}

            {loading && <p className="text-sm text-ink-muted">Yanıt yazılıyor...</p>}
            <div ref={bottomRef} />
          </div>

          <form onSubmit={handleSend} className="flex gap-2 border-t border-border p-3">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Bir soru yaz..."
              disabled={loading}
              className="bg-surface border-border"
            />
            <Button type="submit" disabled={loading || !input.trim()} size="icon" className="shrink-0">
              <Send className="h-4 w-4" />
            </Button>
          </form>

          {error && <p className="px-4 pb-3 text-sm text-red-600">{error}</p>}
        </div>
      </div>
    </div>
  );
}
