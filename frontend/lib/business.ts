const ACTIVE_BUSINESS_KEY = "active_business_id";

export function saveActiveBusinessId(businessId: string) {
  localStorage.setItem(ACTIVE_BUSINESS_KEY, businessId);
}

export function getActiveBusinessId(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACTIVE_BUSINESS_KEY);
}

export function clearActiveBusinessId() {
  localStorage.removeItem(ACTIVE_BUSINESS_KEY);
}
