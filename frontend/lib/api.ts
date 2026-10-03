import { getAccessToken, getRefreshToken, saveTokens, clearTokens } from "./auth";
import { clearActiveBusinessId } from "./business";
import type {
  RegisterPayload,
  RegisterResponse,
  TokenResponse,
  MeResponse,
  Business,
  BusinessCreatePayload,
  ReminderLog,
  TestReminderResult,
  ChatResponse,
  ChatSession,
  ChatMessage,
  CustomerStatus,
  Customer,
  CustomerCreatePayload,
  CustomerUpdatePayload,
  ServiceStatus,
  BusinessService,
  ServiceCreatePayload,
  ServiceUpdatePayload,
  AppointmentStatus,
  Appointment,
  AppointmentCreatePayload,
  AppointmentUpdatePayload,
  AvailableSlotsResponse,
  DocumentStatus,
  BusinessDocument,
  DocumentStatusInfo,
  MembershipRole,
  Membership,
  InvitationStatus,
  Invitation,
  InvitationCreatePayload,
  AdminBusiness,
  AppNotification,
  Invoice,
  InvoiceCreatePayload,
  InvoiceUpdatePayload,
  InvoiceStatus,
  PaymentMethod,
  RevenueStats,
  BusinessHours,
  BusinessHoursItem,
  OpenWindow
} from "@/types";

export interface UpdateProfilePayload {
  first_name: string;
  last_name: string;
}

export interface ChangePasswordPayload {
  current_password: string;
  new_password: string;
}

export * from "@/types";

// .env.local dosyasında NEXT_PUBLIC_API_URL tanımla (örn: http://localhost:8000)
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

// ---------- Auth ----------

export async function register(payload: RegisterPayload): Promise<RegisterResponse> {
  const res = await fetch(`${API_URL}/api/v1/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const body = await safeJson(res);
    throw new ApiError(res.status, body?.detail ?? "Kayıt işlemi başarısız oldu.");
  }

  return res.json();
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  // Backend OAuth2PasswordRequestForm bekliyor -> JSON değil, form-urlencoded gönderiyoruz.
  const form = new URLSearchParams();
  form.set("grant_type", "password");
  form.set("username", email); // FastAPI'nin standart alanı "username", biz email'i buraya koyuyoruz
  form.set("password", password);

  const res = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form.toString(),
  });

  if (!res.ok) {
    const body = await safeJson(res);
    throw new ApiError(res.status, body?.detail ?? "E-posta veya şifre hatalı.");
  }

  const data: TokenResponse = await res.json();
  saveTokens(data.access_token, data.refresh_token);
  return data;
}

export function logout() {
  clearTokens();
  clearActiveBusinessId();
}

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return null;

  const res = await fetch(`${API_URL}/api/v1/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!res.ok) {
    clearTokens();
    return null;
  }

  const data: TokenResponse = await res.json();
  saveTokens(data.access_token, data.refresh_token);
  return data.access_token;
}

export async function getMe(): Promise<MeResponse> {
  return apiFetch<MeResponse>("/api/v1/auth/me");
}

export async function updateProfile(payload: UpdateProfilePayload): Promise<MeResponse> {
  return apiFetch<MeResponse>("/api/v1/auth/me", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function changePassword(payload: ChangePasswordPayload): Promise<{ message: string }> {
  return apiFetch<{ message: string }>("/api/v1/auth/change-password", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}


async function safeJson(res: Response) {
  try {
    return await res.json();
  } catch {
    return null;
  }
}

// ---------- Genel amaçlı, token'lı istek fonksiyonu ----------
// Tüm modüller (chat, randevu, satış, finans, pazarlama) bunu kullanacak.

interface RequestOptions extends RequestInit {
  skipAuth?: boolean;
}

export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { skipAuth, headers, ...rest } = options;
  const isFormData = rest.body instanceof FormData;

  const doFetch = async (token: string | null) => {
    return fetch(`${API_URL}${path}`, {
      ...rest,
      headers: {
        // FormData gönderirken Content-Type'ı biz değil, tarayıcı ayarlamalı (multipart boundary için)
        ...(isFormData ? {} : { "Content-Type": "application/json" }),
        ...(token && !skipAuth ? { Authorization: `Bearer ${token}` } : {}),
        ...headers,
      },
    });
  };

  let token = getAccessToken();
  let res = await doFetch(token);

  // Token süresi dolmuşsa bir kez refresh deneyip isteği tekrar at
  if (res.status === 401 && !skipAuth) {
    token = await refreshAccessToken();
    if (token) {
      res = await doFetch(token);
    }
  }

  if (!res.ok) {
    const body = await safeJson(res);
    throw new ApiError(res.status, body?.detail ?? `İstek başarısız oldu (${res.status})`);
  }

  // 204 No Content gibi durumlar için
  if (res.status === 204) return undefined as T;

  return res.json();
}

// ---------- Businesses ----------
// Sistemdeki her kaynak bir business_id'ye bağlı (multi-tenant),
// bu yüzden kullanıcı önce bir işletme seçmeli/oluşturmalı.

export async function getBusinesses(): Promise<Business[]> {
  return apiFetch<Business[]>("/api/v1/businesses");
}

export async function createBusiness(payload: BusinessCreatePayload): Promise<Business> {
  return apiFetch<Business>("/api/v1/businesses", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getBusiness(businessId: string): Promise<Business> {
  return apiFetch<Business>(`/api/v1/businesses/${businessId}`);
}

// ---------- Chat (Müşteri destek ajanı) ----------
// Konuşma geçmişi backend'de business_id + user_id bazında otomatik tutuluyor,
// frontend'in conversation_id yönetmesine gerek yok.

export async function sendChatMessage(
  businessId: string,
  question: string,
  sessionId?: string
): Promise<ChatResponse> {
  return apiFetch<ChatResponse>(`/api/v1/businesses/${businessId}/chat`, {
    method: "POST",
    body: JSON.stringify({ question, session_id: sessionId ?? null }),
  });
}

export async function approveAgentAction(businessId: string, actionId: string) {
  return apiFetch(`/api/v1/businesses/${businessId}/agent-actions/${actionId}/approve`, {
    method: "POST",
  });
}

export async function rejectAgentAction(businessId: string, actionId: string, reason: string) {
  return apiFetch(`/api/v1/businesses/${businessId}/agent-actions/${actionId}/reject`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
}

// ---------- Customers ----------

export async function listCustomers(businessId: string, page = 1, size = 20): Promise<Customer[]> {
  return apiFetch<Customer[]>(
    `/api/v1/businesses/${businessId}/customers?page=${page}&size=${size}`
  );
}

export async function createCustomer(
  businessId: string,
  payload: CustomerCreatePayload
): Promise<Customer> {
  return apiFetch<Customer>(`/api/v1/businesses/${businessId}/customers`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateCustomer(
  businessId: string,
  customerId: string,
  payload: CustomerUpdatePayload
): Promise<Customer> {
  return apiFetch<Customer>(`/api/v1/businesses/${businessId}/customers/${customerId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteCustomer(businessId: string, customerId: string): Promise<void> {
  return apiFetch<void>(`/api/v1/businesses/${businessId}/customers/${customerId}`, {
    method: "DELETE",
  });
}

// ---------- Services (Satış ve öneri ajanının önerdiği ürün/hizmet kataloğu) ----------

export async function listServices(businessId: string): Promise<BusinessService[]> {
  return apiFetch<BusinessService[]>(`/api/v1/businesses/${businessId}/services`);
}

export async function createService(
  businessId: string,
  payload: ServiceCreatePayload
): Promise<BusinessService> {
  return apiFetch<BusinessService>(`/api/v1/businesses/${businessId}/services`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateService(
  businessId: string,
  serviceId: string,
  payload: ServiceUpdatePayload
): Promise<BusinessService> {
  return apiFetch<BusinessService>(`/api/v1/businesses/${businessId}/services/${serviceId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteService(businessId: string, serviceId: string): Promise<void> {
  return apiFetch<void>(`/api/v1/businesses/${businessId}/services/${serviceId}`, {
    method: "DELETE",
  });
}

// ---------- Appointments ----------

export async function listAppointmentsByDate(
  businessId: string,
  targetDate: string
): Promise<Appointment[]> {
  return apiFetch<Appointment[]>(
    `/api/v1/businesses/${businessId}/appointments?date=${targetDate}`
  );
}

export async function listAppointments(
  businessId: string,
  page = 1,
  size = 100
): Promise<Appointment[]> {
  return apiFetch<Appointment[]>(
    `/api/v1/businesses/${businessId}/appointments?page=${page}&size=${size}`
  );
}

export async function createAppointment(
  businessId: string,
  payload: AppointmentCreatePayload
): Promise<Appointment> {
  return apiFetch<Appointment>(`/api/v1/businesses/${businessId}/appointments`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateAppointment(
  businessId: string,
  appointmentId: string,
  payload: AppointmentUpdatePayload
): Promise<Appointment> {
  return apiFetch<Appointment>(`/api/v1/businesses/${businessId}/appointments/${appointmentId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function cancelAppointment(businessId: string, appointmentId: string): Promise<Appointment> {
  return apiFetch<Appointment>(
    `/api/v1/businesses/${businessId}/appointments/${appointmentId}/cancel`,
    { method: "POST" }
  );
}

export async function completeAppointment(businessId: string, appointmentId: string): Promise<Appointment> {
  return apiFetch<Appointment>(
    `/api/v1/businesses/${businessId}/appointments/${appointmentId}/complete`,
    { method: "POST" }
  );
}

export async function getAvailableSlots(
  businessId: string,
  date: string,
  durationMinutes = 60
): Promise<AvailableSlotsResponse> {
  return apiFetch<AvailableSlotsResponse>(
    `/api/v1/businesses/${businessId}/appointments/available-slots?date=${date}&duration_minutes=${durationMinutes}`
  );
}

// ---------- Documents (RAG bilgi tabanı) ----------

export async function listDocuments(businessId: string): Promise<BusinessDocument[]> {
  return apiFetch<BusinessDocument[]>(`/api/v1/businesses/${businessId}/documents`);
}

export async function uploadDocument(businessId: string, file: File): Promise<BusinessDocument> {
  const formData = new FormData();
  formData.append("file", file);
  return apiFetch<BusinessDocument>(`/api/v1/businesses/${businessId}/documents`, {
    method: "POST",
    body: formData,
  });
}

export async function getDocumentStatus(
  businessId: string,
  documentId: string
): Promise<DocumentStatusInfo> {
  return apiFetch<DocumentStatusInfo>(
    `/api/v1/businesses/${businessId}/documents/${documentId}/status`
  );
}

export async function deleteDocument(businessId: string, documentId: string): Promise<void> {
  return apiFetch<void>(`/api/v1/businesses/${businessId}/documents/${documentId}`, {
    method: "DELETE",
  });
}

// ---------- Memberships (Ekip yönetimi) ----------

export async function listMemberships(businessId: string): Promise<Membership[]> {
  return apiFetch<Membership[]>(`/api/v1/businesses/${businessId}/memberships`);
}

export async function updateMembershipRole(
  businessId: string,
  membershipId: string,
  role: MembershipRole
): Promise<Membership> {
  return apiFetch<Membership>(`/api/v1/businesses/${businessId}/memberships/${membershipId}`, {
    method: "PATCH",
    body: JSON.stringify({ role }),
  });
}

export async function removeMembership(businessId: string, membershipId: string): Promise<void> {
  return apiFetch<void>(`/api/v1/businesses/${businessId}/memberships/${membershipId}`, {
    method: "DELETE",
  });
}

// ---------- Invitations (yalnızca işletme sahibi görebilir/gönderebilir) ----------

export async function listInvitations(businessId: string): Promise<Invitation[]> {
  return apiFetch<Invitation[]>(`/api/v1/businesses/${businessId}/invitations`);
}

export async function createInvitation(
  businessId: string,
  payload: InvitationCreatePayload
): Promise<Invitation> {
  return apiFetch<Invitation>(`/api/v1/businesses/${businessId}/invitations`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function acceptInvitation(token: string): Promise<Invitation> {
  return apiFetch<Invitation>(`/api/v1/invitations/accept/${token}`, {
    method: "POST",
  });
}

export async function uploadTextAsDocument(
  businessId: string,
  filename: string,
  text: string
): Promise<BusinessDocument> {
  const blob = new Blob([text], { type: "text/plain" });
  const file = new File([blob], filename, { type: "text/plain" });
  return uploadDocument(businessId, file);
}

// ---------- Platform Admin (superadmin) ----------

export async function adminListBusinesses(page = 1, size = 50): Promise<AdminBusiness[]> {
  return apiFetch<AdminBusiness[]>(`/api/v1/admin/businesses?page=${page}&size=${size}`);
}

export async function adminUpdateBusinessStatus(
  businessId: string,
  status: AdminBusiness["status"]
): Promise<AdminBusiness> {
  return apiFetch<AdminBusiness>(`/api/v1/admin/businesses/${businessId}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

export async function adminUpdateBusinessPlan(
  businessId: string,
  plan: AdminBusiness["plan"]
): Promise<AdminBusiness> {
  return apiFetch<AdminBusiness>(`/api/v1/admin/businesses/${businessId}/plan`, {
    method: "PATCH",
    body: JSON.stringify({ plan }),
  });
}

export async function adminDeleteBusiness(businessId: string): Promise<void> {
  return apiFetch<void>(`/api/v1/admin/businesses/${businessId}`, {
    method: "DELETE",
  });
}

// ---------- Notifications ----------

export async function listNotifications(
  businessId: string,
  unreadOnly = false
): Promise<AppNotification[]> {
  const query = unreadOnly ? '?unread_only=true' : '';
  return apiFetch<AppNotification[]>(
    `/api/v1/businesses/${businessId}/notifications${query}`
  );
}

export async function getUnreadCount(businessId: string): Promise<{ count: number }> {
  return apiFetch<{ count: number }>(
    `/api/v1/businesses/${businessId}/notifications/unread-count`
  );
}

export async function markNotificationRead(
  businessId: string,
  notificationId: string
): Promise<void> {
  return apiFetch<void>(
    `/api/v1/businesses/${businessId}/notifications/${notificationId}/read`,
    { method: 'POST' }
  );
}

export async function markAllNotificationsRead(businessId: string): Promise<void> {
  return apiFetch<void>(
    `/api/v1/businesses/${businessId}/notifications/read-all`,
    { method: 'POST' }
  );
}

// ---------- Chat Sessions ----------

export async function listChatSessions(businessId: string): Promise<ChatSession[]> {
  return apiFetch<ChatSession[]>(`/api/v1/businesses/${businessId}/chat/sessions`);
}

export async function getChatSessionMessages(
  businessId: string,
  sessionId: string
): Promise<ChatMessage[]> {
  return apiFetch<ChatMessage[]>(
    `/api/v1/businesses/${businessId}/chat/sessions/${sessionId}/messages`
  );
}

export async function deleteChatSession(
  businessId: string,
  sessionId: string
): Promise<void> {
  return apiFetch<void>(
    `/api/v1/businesses/${businessId}/chat/sessions/${sessionId}`,
    { method: 'DELETE' }
  );
}

// ---------- Invoices ----------

export async function listInvoices(
  businessId: string,
  statusFilter?: InvoiceStatus
): Promise<Invoice[]> {
  const query = statusFilter ? `?status=${statusFilter}` : '';
  return apiFetch<Invoice[]>(
    `/api/v1/businesses/${businessId}/invoices${query}`
  );
}

export async function getInvoice(
  businessId: string,
  invoiceId: string
): Promise<Invoice> {
  return apiFetch<Invoice>(
    `/api/v1/businesses/${businessId}/invoices/${invoiceId}`
  );
}

export async function createInvoice(
  businessId: string,
  payload: InvoiceCreatePayload
): Promise<Invoice> {
  return apiFetch<Invoice>(
    `/api/v1/businesses/${businessId}/invoices`,
    {
      method: 'POST',
      body: JSON.stringify(payload),
    }
  );
}

export async function updateInvoice(
  businessId: string,
  invoiceId: string,
  payload: InvoiceUpdatePayload
): Promise<Invoice> {
  return apiFetch<Invoice>(
    `/api/v1/businesses/${businessId}/invoices/${invoiceId}`,
    {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }
  );
}

export async function markInvoicePaid(
  businessId: string,
  invoiceId: string,
  paymentMethod: PaymentMethod
): Promise<Invoice> {
  return apiFetch<Invoice>(
    `/api/v1/businesses/${businessId}/invoices/${invoiceId}/pay?payment_method=${paymentMethod}`,
    { method: 'POST' }
  );
}

export async function cancelInvoice(
  businessId: string,
  invoiceId: string
): Promise<Invoice> {
  return apiFetch<Invoice>(
    `/api/v1/businesses/${businessId}/invoices/${invoiceId}/cancel`,
    { method: 'POST' }
  );
}

export async function getRevenueStats(
  businessId: string
): Promise<RevenueStats> {
  return apiFetch<RevenueStats>(
    `/api/v1/businesses/${businessId}/invoices/stats`
  );
}

// ---------- Document Chunks (RAG'in dokümanı nasıl parçaladığı) ----------

export interface DocumentChunk {
  id: string;
  document_id: string;
  chunk_index: number;
  content: string;
  token_count: number | null;
  embedding_status: string;
  created_at: string;
  updated_at: string;
}

export async function getDocumentChunks(
  businessId: string,
  documentId: string
): Promise<DocumentChunk[]> {
  return apiFetch<DocumentChunk[]>(
    `/api/v1/businesses/${businessId}/documents/${documentId}/chunks`
  );
}

// ==================== Schedule Blocks ====================
export async function listScheduleBlocks(businessId: string) {
  return apiFetch<any[]>(`/api/v1/businesses/${businessId}/schedule-blocks`);
}

export async function createScheduleBlock(businessId: string, data: any) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/schedule-blocks`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateScheduleBlock(businessId: string, blockId: string, data: any) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/schedule-blocks/${blockId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteScheduleBlock(businessId: string, blockId: string) {
  return apiFetch<void>(`/api/v1/businesses/${businessId}/schedule-blocks/${blockId}`, {
    method: "DELETE",
  });
}

export async function getBlockedTimesForDate(businessId: string, date: string, branchId?: string | null) {
  const branch = branchId ? `&branch_id=${branchId}` : "";
  return apiFetch<any[]>(`/api/v1/businesses/${businessId}/schedule-blocks/for-date?date=${date}${branch}`);
}

// ==================== Business Hours ====================
// branchId verilmezse işletme geneli saatler, verilirse o şubenin kendi saatleri.
function businessHoursPath(businessId: string, branchId?: string | null) {
  const query = branchId ? `?branch_id=${branchId}` : "";
  return `/api/v1/businesses/${businessId}/business-hours${query}`;
}

export async function getBusinessHours(businessId: string, branchId?: string | null) {
  return apiFetch<BusinessHours[]>(businessHoursPath(businessId, branchId));
}

export async function setBusinessHours(
  businessId: string,
  items: BusinessHoursItem[],
  branchId?: string | null,
) {
  return apiFetch<BusinessHours[]>(businessHoursPath(businessId, branchId), {
    method: "PUT",
    body: JSON.stringify({ items }),
  });
}

// Şubenin kendi saatlerini siler; şube tekrar işletme geneli saatleri kullanır.
export async function resetBranchHours(businessId: string, branchId: string) {
  return apiFetch<void>(businessHoursPath(businessId, branchId), { method: "DELETE" });
}

export async function getOpenWindow(businessId: string, date: string, branchId?: string | null) {
  const branch = branchId ? `&branch_id=${branchId}` : "";
  return apiFetch<OpenWindow>(
    `/api/v1/businesses/${businessId}/business-hours/open-window?date=${date}${branch}`,
  );
}

// ==================== Reminders ====================
export async function listReminderConfigs(businessId: string) {
  return apiFetch<any[]>(`/api/v1/businesses/${businessId}/reminders/configs`);
}

export async function createReminderConfig(businessId: string, data: any) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/reminders/configs`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateReminderConfig(businessId: string, configId: string, data: any) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/reminders/configs/${configId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteReminderConfig(businessId: string, configId: string) {
  return apiFetch<void>(`/api/v1/businesses/${businessId}/reminders/configs/${configId}`, {
    method: "DELETE",
  });
}

export async function listReminderLogs(
  businessId: string,
  params: { page?: number; size?: number; appointmentId?: string } = {},
) {
  const q = new URLSearchParams();
  q.set("page", String(params.page ?? 1));
  q.set("size", String(params.size ?? 20));
  if (params.appointmentId) q.set("appointment_id", params.appointmentId);
  return apiFetch<ReminderLog[]>(`/api/v1/businesses/${businessId}/reminders/logs?${q.toString()}`);
}

export async function sendTestReminder(businessId: string, configId: string) {
  return apiFetch<TestReminderResult>(
    `/api/v1/businesses/${businessId}/reminders/send-test/${configId}`,
    { method: "POST" },
  );
}

// ==================== Customer Tags ====================
export async function listCustomerTags(businessId: string) {
  return apiFetch<any[]>(`/api/v1/businesses/${businessId}/customer-tags`);
}

export async function createCustomerTag(businessId: string, data: { name: string; color?: string; description?: string }) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/customer-tags`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateCustomerTag(businessId: string, tagId: string, data: any) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/customer-tags/${tagId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteCustomerTag(businessId: string, tagId: string) {
  return apiFetch<void>(`/api/v1/businesses/${businessId}/customer-tags/${tagId}`, {
    method: "DELETE",
  });
}

export async function assignTagToCustomer(businessId: string, customerId: string, tagId: string) {
  return apiFetch<void>(`/api/v1/businesses/${businessId}/customer-tags/customers/${customerId}/assign`, {
    method: "POST",
    body: JSON.stringify({ tag_id: tagId }),
  });
}

export async function removeTagFromCustomer(businessId: string, customerId: string, tagId: string) {
  return apiFetch<void>(`/api/v1/businesses/${businessId}/customer-tags/customers/${customerId}/${tagId}`, {
    method: "DELETE",
  });
}

export async function getCustomerTags(businessId: string, customerId: string) {
  return apiFetch<any[]>(`/api/v1/businesses/${businessId}/customer-tags/customers/${customerId}/tags`);
}

// ==================== Loyalty ====================
export async function getLoyaltyRules(businessId: string) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/loyalty/rules`);
}

export async function updateLoyaltyRules(businessId: string, data: any) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/loyalty/rules`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function listLoyaltyWallets(businessId: string) {
  return apiFetch<any[]>(`/api/v1/businesses/${businessId}/loyalty/wallets`);
}

export async function getCustomerWallet(businessId: string, customerId: string) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/loyalty/wallets/${customerId}`);
}

export async function earnPoints(businessId: string, data: { customer_id: string; points: number; description: string }) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/loyalty/earn`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function spendPoints(businessId: string, data: { customer_id: string; points: number; description: string }) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/loyalty/spend`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function adjustPoints(businessId: string, data: { customer_id: string; points: number; description: string }) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/loyalty/adjust`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function listLoyaltyTransactions(businessId: string, customerId?: string) {
  const query = customerId ? `?customer_id=${customerId}` : "";
  return apiFetch<any[]>(`/api/v1/businesses/${businessId}/loyalty/transactions${query}`);
}

// ==================== Surveys ====================
export async function listSurveys(businessId: string) {
  return apiFetch<any[]>(`/api/v1/businesses/${businessId}/surveys`);
}

// ==================== Reports ====================
export async function getDashboardStats(businessId: string) {
  return apiFetch<import("@/types/reports").DashboardStats>(`/api/v1/businesses/${businessId}/reports/dashboard-stats`);
}

export async function getRevenueReport(businessId: string, startDate: string, endDate: string, groupBy: string = "day") {
  return apiFetch<import("@/types/reports").RevenueDataPoint[]>(`/api/v1/businesses/${businessId}/reports/revenue?start_date=${startDate}&end_date=${endDate}&group_by=${groupBy}`);
}

export async function getAppointmentReport(businessId: string, startDate: string, endDate: string) {
  return apiFetch<import("@/types/reports").AppointmentReport>(`/api/v1/businesses/${businessId}/reports/appointments?start_date=${startDate}&end_date=${endDate}`);
}

export async function getCustomerReport(businessId: string, startDate: string, endDate: string) {
  return apiFetch<import("@/types/reports").CustomerReport>(`/api/v1/businesses/${businessId}/reports/customers?start_date=${startDate}&end_date=${endDate}`);
}

export async function getServiceReport(businessId: string, startDate: string, endDate: string) {
  return apiFetch<import("@/types/reports").ServiceStats[]>(`/api/v1/businesses/${businessId}/reports/services?start_date=${startDate}&end_date=${endDate}`);
}

export async function getStaffPerformanceReport(businessId: string, startDate: string, endDate: string) {
  return apiFetch<import("@/types/reports").StaffPerformance[]>(`/api/v1/businesses/${businessId}/reports/staff-performance?start_date=${startDate}&end_date=${endDate}`);
}

// ==================== Products ====================
export async function listProducts(businessId: string, params?: { category?: string; status?: string; search?: string; low_stock_only?: boolean; page?: number; size?: number }) {
  const queryParams = new URLSearchParams();
  if (params?.category) queryParams.append("category", params.category);
  if (params?.status) queryParams.append("status", params.status);
  if (params?.search) queryParams.append("search", params.search);
  if (params?.low_stock_only) queryParams.append("low_stock_only", "true");
  if (params?.page) queryParams.append("page", params.page.toString());
  if (params?.size) queryParams.append("size", params.size.toString());
  
  const queryStr = queryParams.toString();
  return apiFetch<any[]>(`/api/v1/businesses/${businessId}/products${queryStr ? `?${queryStr}` : ""}`);
}

export async function createProduct(businessId: string, data: any) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/products`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateProduct(businessId: string, productId: string, data: any) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/products/${productId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteProduct(businessId: string, productId: string) {
  return apiFetch<void>(`/api/v1/businesses/${businessId}/products/${productId}`, {
    method: "DELETE",
  });
}

export async function getProductStockSummary(businessId: string) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/products/stock-summary`);
}

export async function getLowStockProducts(businessId: string) {
  return apiFetch<any[]>(`/api/v1/businesses/${businessId}/products/low-stock`);
}

export async function addProductStock(businessId: string, productId: string, data: { quantity: number; movement_type: string; unit_price?: number; notes?: string }) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/products/${productId}/stock`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getProductMovements(businessId: string, productId: string, page?: number) {
  const query = page ? `?page=${page}` : "";
  return apiFetch<any[]>(`/api/v1/businesses/${businessId}/products/${productId}/movements${query}`);
}

// ==================== Product Sales ====================
export async function createProductSale(businessId: string, data: any) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/product-sales`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function listProductSales(businessId: string, params?: { page?: number; date_from?: string; date_to?: string }) {
  const queryParams = new URLSearchParams();
  if (params?.page) queryParams.append("page", params.page.toString());
  if (params?.date_from) queryParams.append("date_from", params.date_from);
  if (params?.date_to) queryParams.append("date_to", params.date_to);
  
  const queryStr = queryParams.toString();
  return apiFetch<any[]>(`/api/v1/businesses/${businessId}/product-sales${queryStr ? `?${queryStr}` : ""}`);
}

export async function getProductSale(businessId: string, saleId: string) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/product-sales/${saleId}`);
}

export async function createSurvey(businessId: string, data: any) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/surveys`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateSurvey(businessId: string, surveyId: string, data: any) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/surveys/${surveyId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteSurvey(businessId: string, surveyId: string) {
  return apiFetch<void>(`/api/v1/businesses/${businessId}/surveys/${surveyId}`, {
    method: "DELETE",
  });
}

export async function getSurveyResponses(businessId: string, surveyId: string) {
  return apiFetch<any[]>(`/api/v1/businesses/${businessId}/surveys/${surveyId}/responses`);
}

export async function getSurveyStats(businessId: string, surveyId: string) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/surveys/${surveyId}/stats`);
}

// ==================== Reviews ====================
export async function listReviews(businessId: string, status?: string) {
  const query = status ? `?status=${status}` : "";
  return apiFetch<any[]>(`/api/v1/businesses/${businessId}/reviews${query}`);
}

export async function getReviewStats(businessId: string) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/reviews/stats`);
}

export async function approveReview(businessId: string, reviewId: string) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/reviews/${reviewId}/approve`, {
    method: "PATCH",
  });
}

export async function rejectReview(businessId: string, reviewId: string) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/reviews/${reviewId}/reject`, {
    method: "PATCH",
  });
}

export async function replyToReview(businessId: string, reviewId: string, reply: string) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/reviews/${reviewId}/reply`, {
    method: "PATCH",
    body: JSON.stringify({ reply }),
  });
}

// ==================== Customer History ====================
export async function getCustomerHistory(businessId: string, customerId: string) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/customers/${customerId}/history`);
}

// ==================== Branches ====================
export async function listBranches(businessId: string) {
  return apiFetch<any[]>(`/api/v1/businesses/${businessId}/branches`);
}
export async function createBranch(businessId: string, data: any) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/branches`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}
export async function updateBranch(businessId: string, branchId: string, data: any) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/branches/${branchId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}
export async function deleteBranch(businessId: string, branchId: string) {
  return apiFetch<void>(`/api/v1/businesses/${businessId}/branches/${branchId}`, {
    method: "DELETE",
  });
}
export async function setMainBranch(businessId: string, branchId: string) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/branches/${branchId}/set-main`, {
    method: "POST",
  });
}

// ==================== Staff ====================
export async function listStaff(businessId: string, branchId?: string) {
  const query = branchId ? `?branch_id=${branchId}` : "";
  return apiFetch<any[]>(`/api/v1/businesses/${businessId}/staff${query}`);
}
export async function createStaff(businessId: string, data: any) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/staff`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}
export async function updateStaff(businessId: string, staffId: string, data: any) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/staff/${staffId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}
export async function deleteStaff(businessId: string, staffId: string) {
  return apiFetch<void>(`/api/v1/businesses/${businessId}/staff/${staffId}`, {
    method: "DELETE",
  });
}
export async function assignStaffServices(businessId: string, staffId: string, serviceIds: string[]) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/staff/${staffId}/services`, {
    method: "PUT",
    body: JSON.stringify({ service_ids: serviceIds }),
  });
}
export async function getStaffServices(businessId: string, staffId: string) {
  return apiFetch<any[]>(`/api/v1/businesses/${businessId}/staff/${staffId}/services`);
}
export async function setStaffSchedule(businessId: string, staffId: string, items: any[]) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/staff/${staffId}/schedule`, {
    method: "PUT",
    body: JSON.stringify({ items }),
  });
}
export async function getStaffSchedule(businessId: string, staffId: string) {
  return apiFetch<any[]>(`/api/v1/businesses/${businessId}/staff/${staffId}/schedule`);
}
export async function getAvailableStaff(businessId: string, date: string, startTime: string, serviceId: string, branchId?: string) {
  const params = new URLSearchParams();
  if (date) params.append("date", date);
  if (startTime) params.append("start_time", startTime);
  if (serviceId) params.append("service_id", serviceId);
  if (branchId) params.append("branch_id", branchId);
  
  return apiFetch<any[]>(`/api/v1/businesses/${businessId}/staff/available?${params.toString()}`);
}

// ==================== Expense Categories ====================
export async function listExpenseCategories(businessId: string) {
  return apiFetch<any[]>(`/api/v1/businesses/${businessId}/expense-categories`);
}
export async function createExpenseCategory(businessId: string, data: any) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/expense-categories`, {
    method: "POST",
    body: JSON.stringify(data)
  });
}
export async function updateExpenseCategory(businessId: string, catId: string, data: any) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/expense-categories/${catId}`, {
    method: "PATCH",
    body: JSON.stringify(data)
  });
}
export async function deleteExpenseCategory(businessId: string, catId: string) {
  return apiFetch<void>(`/api/v1/businesses/${businessId}/expense-categories/${catId}`, {
    method: "DELETE"
  });
}

// ==================== Expenses ====================
export async function listExpenses(businessId: string, params?: { direction?: string; category_id?: string; date_from?: string; date_to?: string; status?: string; search?: string; page?: number; size?: number }) {
  const cleaned = Object.fromEntries(Object.entries(params || {}).filter(([, v]) => v !== undefined && v !== null));
  const query = Object.keys(cleaned).length ? `?${new URLSearchParams(cleaned as any).toString()}` : "";
  return apiFetch<any[]>(`/api/v1/businesses/${businessId}/expenses${query}`);
}
export async function createExpense(businessId: string, data: any) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/expenses`, {
    method: "POST",
    body: JSON.stringify(data)
  });
}
export async function updateExpense(businessId: string, expenseId: string, data: any) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/expenses/${expenseId}`, {
    method: "PATCH",
    body: JSON.stringify(data)
  });
}
export async function deleteExpense(businessId: string, expenseId: string) {
  return apiFetch<void>(`/api/v1/businesses/${businessId}/expenses/${expenseId}`, {
    method: "DELETE"
  });
}
export async function getFinancialSummary(businessId: string, startDate: string, endDate: string) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/expenses/summary?start_date=${startDate}&end_date=${endDate}`);
}
export async function getMonthlyReport(businessId: string, year: number, month: number) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/expenses/monthly-report?year=${year}&month=${month}`);
}
export async function getCategoryBreakdown(businessId: string, startDate: string, endDate: string) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/expenses/category-breakdown?start_date=${startDate}&end_date=${endDate}`);
}

// ==================== Cash Register ====================
export async function openCashRegister(businessId: string, data: { opening_balance: number; branch_id?: string; notes?: string }) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/cash-register/open`, {
    method: "POST",
    body: JSON.stringify(data)
  });
}
export async function closeCashRegister(businessId: string, registerId: string, data: { closing_balance: number; notes?: string }) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/cash-register/${registerId}/close`, {
    method: "POST",
    body: JSON.stringify(data)
  });
}
export async function addCashTransaction(businessId: string, registerId: string, data: any) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/cash-register/${registerId}/transactions`, {
    method: "POST",
    body: JSON.stringify(data)
  });
}
export async function getTodayRegister(businessId: string) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/cash-register/today`);
}
export async function listCashRegisters(businessId: string, params?: { page?: number }) {
  const query = params?.page ? `?page=${params.page}` : "";
  return apiFetch<any[]>(`/api/v1/businesses/${businessId}/cash-register${query}`);
}
export async function getCashRegister(businessId: string, registerId: string) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/cash-register/${registerId}`);
}
export async function getRegisterSummary(businessId: string, registerId: string) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/cash-register/${registerId}/summary`);
}

// ==================== Service Packages ====================
export async function listPackages(businessId: string) {
  return apiFetch<any[]>(`/api/v1/businesses/${businessId}/packages`);
}
export async function createPackage(businessId: string, data: any) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/packages`, { method: 'POST', body: JSON.stringify(data) });
}
export async function updatePackage(businessId: string, packageId: string, data: any) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/packages/${packageId}`, { method: 'PATCH', body: JSON.stringify(data) });
}
export async function deletePackage(businessId: string, packageId: string) {
  return apiFetch<void>(`/api/v1/businesses/${businessId}/packages/${packageId}`, { method: 'DELETE' });
}

// ==================== Customer Packages ====================
export async function sellPackage(businessId: string, data: any) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/customer-packages`, { method: 'POST', body: JSON.stringify(data) });
}
export async function listCustomerPackages(businessId: string, params?: { customer_id?: string; status?: string }) {
  const query = new URLSearchParams(
    Object.fromEntries(Object.entries(params || {}).filter(([, v]) => v !== undefined && v !== null))
  ).toString();
  return apiFetch<any[]>(`/api/v1/businesses/${businessId}/customer-packages${query ? '?' + query : ''}`);
}
export async function getCustomerPackageDetail(businessId: string, cpId: string) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/customer-packages/${cpId}`);
}
export async function completeSession(businessId: string, cpId: string, sessionId: string, data?: any) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/customer-packages/${cpId}/sessions/${sessionId}/complete`, { method: 'POST', body: data ? JSON.stringify(data) : undefined });
}
export async function cancelSession(businessId: string, cpId: string, sessionId: string) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/customer-packages/${cpId}/sessions/${sessionId}/cancel`, { method: 'POST' });
}

// ==================== Installments ====================
export async function listInstallments(businessId: string, params?: { status?: string }) {
  const query = new URLSearchParams(
    Object.fromEntries(Object.entries(params || {}).filter(([, v]) => v !== undefined && v !== null))
  ).toString();
  return apiFetch<any[]>(`/api/v1/businesses/${businessId}/installments${query ? '?' + query : ''}`);
}
export async function listOverdueInstallments(businessId: string) {
  return apiFetch<any[]>(`/api/v1/businesses/${businessId}/installments/overdue`);
}
export async function payInstallment(businessId: string, installmentId: string, data?: { payment_method?: string }) {
  return apiFetch<any>(`/api/v1/businesses/${businessId}/installments/${installmentId}/pay`, { method: 'POST', body: data ? JSON.stringify(data) : undefined });
}
