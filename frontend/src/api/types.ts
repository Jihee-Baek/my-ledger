// Mirrors backend/app/schemas/*.py. Amounts are Decimal on the backend,
// which FastAPI/Pydantic serialize as JSON strings - kept as `string`
// here and only parsed to number for display/formatting, never
// recomputed (see design doc 8.9: all math stays in the backend).

export interface CategoryOut {
  id: number
  name: string
  parent_id: number | null
  children: CategoryOut[]
}

export interface TransactionOut {
  id: number
  transaction_date: string
  transaction_time: string | null
  transaction_type: 'INCOME' | 'EXPENSE' | 'TRANSFER'
  amount: string
  currency: string
  merchant_raw: string | null
  description: string | null
  memo: string | null
  category_id: number | null
  category_confirmed: boolean
  is_excluded: boolean
  card_id: number | null
  account_id: number | null
  source: string
  created_at: string
}

export interface TransactionListOut {
  items: TransactionOut[]
  total: number
  limit: number
  offset: number
}

export interface TransactionUpdate {
  category_id?: number | null
  memo?: string | null
}

export interface CardOut {
  id: number
  institution: string
  card_number_masked: string | null
  card_type: string | null
  is_active: boolean
}

export interface TransactionSummaryOut {
  currency: string
  count: number
  expense_count: number
  income_count: number
  transfer_count: number
  total_expense: string
  total_income: string
  total_transfer: string
  period_expense_total: string
  expense_share_pct: number | null
  breakdown_kind: 'parent' | 'child' | 'merchant'
  breakdown: CategoryAmount[]
}

export interface CategoryAmount {
  category: string
  amount: string
  percentage: number
}

export interface CurrencyTotal {
  currency: string
  total_expense: string
}

export interface MonthlySummaryOut {
  year: number
  month: number
  currency: string
  total_income: string
  total_expense: string
  net: string
  top_categories: CategoryAmount[]
  other_currencies: CurrencyTotal[]
}

export interface CategorySummaryItem {
  category_id: number | null
  category: string
  parent_category: string | null
  amount: string
  percentage: number
}

export interface MerchantSummaryItem {
  merchant: string
  amount: string
  count: number
}

export interface MonthComparisonItem {
  category: string
  base_amount: string
  target_amount: string
  diff: string
  diff_percentage: number | null
}

export interface RecurringExpenseItem {
  merchant: string
  months_seen: number
  occurrences: number
  average_amount: string
  last_amount: string
}

export interface BudgetStatusItem {
  category_id: number | null
  category: string
  budgeted: string
  actual: string
  remaining: string
  percentage_used: number | null
}

export interface MonthlyTrendItem {
  year: number
  month: number
  total_income: string
  total_expense: string
  net: string
}

export interface CategoryRuleOut {
  id: number
  keyword: string
  match_type: string
  category_id: number
  priority: number
  enabled: boolean
  source: 'SYSTEM' | 'USER'
  created_at: string
}

export interface CategoryRuleCreate {
  keyword: string
  category_id: number
  match_type?: string
  priority?: number
  enabled?: boolean
}

export interface CategoryRuleUpdate {
  keyword?: string
  category_id?: number
  match_type?: string
  priority?: number
  enabled?: boolean
}

export interface AnomalyOverall {
  current_total: string
  baseline_average: string
  change_percentage: number | null
}

export interface AnomalyCategory {
  category: string
  current_amount: string
  baseline_average: string
  change_percentage: number | null
  is_new: boolean
}

export interface SpendingAnomalies {
  year: number
  month: number
  lookback_months: number
  currency: string
  overall: AnomalyOverall
  categories: AnomalyCategory[]
}

export interface ImportResultOut {
  source: string
  file_name: string
  batch_id: number | null
  total: number
  imported: number
  duplicates: number
  classified: number
  unclassified: number
}
