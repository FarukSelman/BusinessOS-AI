export interface ChatResponse {
  conversation_id: string;
  answer: string;
  agent_name: string | null;
  tools_used: string[] | null;
  pending_actions: PendingAgentAction[] | null;
}

export interface PendingAgentAction {
  action_id: string;
  action_type: string;
  payload: Record<string, unknown>;
}

export interface ChatSession {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: string;
  role: 'USER' | 'ASSISTANT' | 'SYSTEM';
  content: string;
  created_at: string;
}
