// Expense Categories
export interface ExpenseCategory {
  id: string;
  business_id: string;
  name: string;
  color: string;
  icon: string | null;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

// Expenses
export type TransactionDirection = 'INCOME' | 'EXPENSE';
export type ExpenseStatus = 'PENDING' | 'PAID' | 'CANCELLED';
export type RecurrenceType = 'NONE' | 'DAILY' | 'WEEKLY' | 'MONTHLY' | 'YEARLY';

export interface Expense {
  id: string;
  business_id: string;
  branch_id: string | null;
  category_id: string | null;
  category_name?: string;
  direction: TransactionDirection;
  title: string;
  description: string | null;
  amount: number;
  currency: string;
  transaction_date: string;
  status: ExpenseStatus;
  payment_method: string | null;
  invoice_id: string | null;
  receipt_url: string | null;
  recurrence: RecurrenceType;
  is_auto_generated: boolean;
  tags: string | null;
  created_at: string;
  updated_at: string;
}

export interface FinancialSummary {
  total_income: number;
  total_expense: number;
  net_profit: number;
  period_start: string;
  period_end: string;
}

export interface CategoryBreakdown {
  category_name: string;
  category_color: string;
  total_amount: number;
  percentage: number;
}

export interface MonthlyReport {
  year: number;
  month: number;
  income: number;
  expense: number;
  net: number;
  category_breakdown: CategoryBreakdown[];
  daily_totals: { date: string; income: number; expense: number }[];
}

// Cash Register
export type CashRegisterStatus = 'OPEN' | 'CLOSED';
export type CashTransactionType = 'OPENING' | 'SALE' | 'EXPENSE' | 'DEPOSIT' | 'WITHDRAWAL' | 'CLOSING';

export interface CashRegister {
  id: string;
  business_id: string;
  branch_id: string | null;
  register_date: string;
  opening_balance: number;
  closing_balance: number | null;
  expected_balance: number | null;
  difference: number | null;
  status: CashRegisterStatus;
  opened_at: string;
  closed_at: string | null;
  notes: string | null;
  created_at: string;
}

export interface CashTransaction {
  id: string;
  register_id: string;
  transaction_type: CashTransactionType;
  amount: number;
  description: string | null;
  reference_type: string | null;
  reference_id: string | null;
  created_at: string;
}

export interface RegisterSummary {
  opening_balance: number;
  total_sales: number;
  total_expenses: number;
  total_deposits: number;
  total_withdrawals: number;
  expected_closing: number;
  actual_closing: number | null;
  difference: number | null;
}
