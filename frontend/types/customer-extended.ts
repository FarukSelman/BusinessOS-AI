// Customer Tags
export interface CustomerTag {
  id: string;
  business_id: string;
  name: string;
  color: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface TagAssignment {
  tag_id: string;
}

// Loyalty / Parapuan
export type TransactionType = 'EARN' | 'SPEND' | 'EXPIRE' | 'ADJUSTMENT' | 'BONUS';
export type WalletStatus = 'ACTIVE' | 'FROZEN';

export interface LoyaltyRule {
  id: string;
  business_id: string;
  points_per_currency: number;
  min_spend_for_earn: number;
  points_value_in_currency: number;
  min_points_for_spend: number;
  expiry_days: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LoyaltyWallet {
  id: string;
  business_id: string;
  customer_id: string;
  balance: number;
  lifetime_earned: number;
  lifetime_spent: number;
  status: WalletStatus;
  created_at: string;
  updated_at: string;
}

export interface LoyaltyTransaction {
  id: string;
  wallet_id: string;
  business_id: string;
  transaction_type: TransactionType;
  points: number;
  description: string | null;
  reference_type: string | null;
  reference_id: string | null;
  created_at: string;
}

// Surveys
export type SurveyStatus = 'ACTIVE' | 'INACTIVE' | 'DRAFT';
export type QuestionType = 'RATING' | 'TEXT' | 'MULTIPLE_CHOICE' | 'YES_NO';

export interface SurveyQuestion {
  id: string;
  type: QuestionType;
  text: string;
  options: string[] | null;
  required: boolean;
}

export interface Survey {
  id: string;
  business_id: string;
  title: string;
  description: string | null;
  questions: SurveyQuestion[];
  status: SurveyStatus;
  is_auto_send: boolean;
  created_at: string;
  updated_at: string;
}

export interface SurveyResponseItem {
  id: string;
  survey_id: string;
  business_id: string;
  customer_id: string | null;
  appointment_id: string | null;
  answers: { question_id: string; answer: string | number | boolean }[];
  overall_rating: number | null;
  comment: string | null;
  respondent_name: string | null;
  respondent_email: string | null;
  created_at: string;
}

// Reviews
export type ReviewStatus = 'PENDING' | 'PUBLISHED' | 'REJECTED';

export interface CustomerReview {
  id: string;
  business_id: string;
  customer_id: string | null;
  appointment_id: string | null;
  service_id: string | null;
  rating: number;
  comment: string | null;
  reviewer_name: string;
  status: ReviewStatus;
  reply: string | null;
  replied_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReviewStats {
  average_rating: number;
  total_count: number;
  rating_distribution: { [key: number]: number };
}
