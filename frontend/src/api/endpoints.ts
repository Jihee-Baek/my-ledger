import { api } from './client'
import type {
  BudgetStatusItem,
  CardOut,
  CategoryOut,
  CategoryRuleCreate,
  CategoryRuleOut,
  CategoryRuleUpdate,
  CategorySummaryItem,
  ImportResultOut,
  MerchantSummaryItem,
  MonthComparisonItem,
  MonthlySummaryOut,
  MonthlyTrendItem,
  RecurringExpenseItem,
  SpendingAnomalies,
  TransactionListOut,
  TransactionUpdate,
} from './types'

export const endpoints = {
  monthlySummary: (year: number, month: number, currency = 'KRW') =>
    api.get<MonthlySummaryOut>('/summary/monthly', { year, month, currency }),

  categorySummary: (year: number, month: number, currency = 'KRW') =>
    api.get<CategorySummaryItem[]>('/summary/category', { year, month, currency }),

  merchantSummary: (year: number, month: number, limit = 10, currency = 'KRW') =>
    api.get<MerchantSummaryItem[]>('/summary/merchant', { year, month, limit, currency }),

  trend: (months = 6, endYear?: number, endMonth?: number, currency = 'KRW') =>
    api.get<MonthlyTrendItem[]>('/summary/trend', {
      months,
      end_year: endYear,
      end_month: endMonth,
      currency,
    }),

  compareMonth: (baseYear: number, baseMonth: number, targetYear: number, targetMonth: number, currency = 'KRW') =>
    api.get<MonthComparisonItem[]>('/comparison/month', {
      base_year: baseYear,
      base_month: baseMonth,
      target_year: targetYear,
      target_month: targetMonth,
      currency,
    }),

  recurringExpenses: (months = 3, minMonthsSeen = 2, currency = 'KRW') =>
    api.get<RecurringExpenseItem[]>('/recurring-expenses', {
      months,
      min_months_seen: minMonthsSeen,
      currency,
    }),

  anomalies: (year: number, month: number, lookbackMonths = 3, minChangePct = 30, currency = 'KRW') =>
    api.get<SpendingAnomalies>('/anomalies', {
      year,
      month,
      lookback_months: lookbackMonths,
      min_change_pct: minChangePct,
      currency,
    }),

  budgetStatus: (year: number, month: number, currency = 'KRW') =>
    api.get<BudgetStatusItem[]>('/budget', { year, month, currency }),

  setBudget: (year: number, month: number, amount: number, categoryId: number | null) =>
    api.post<BudgetStatusItem>('/budget', { year, month, amount, category_id: categoryId }),

  transactions: (params: {
    start_date?: string
    end_date?: string
    min_amount?: number
    max_amount?: number
    category_id?: number
    uncategorized?: boolean
    card_id?: number
    merchant?: string
    q?: string
    transaction_type?: string
    currency?: string
    include_excluded?: boolean
    sort_by?: 'date' | 'amount'
    sort_dir?: 'asc' | 'desc'
    limit?: number
    offset?: number
  }) => api.get<TransactionListOut>('/transactions', params),

  updateTransaction: (id: number, body: TransactionUpdate) => api.patch(`/transactions/${id}`, body),

  categories: () => api.get<CategoryOut[]>('/categories'),

  cards: () => api.get<CardOut[]>('/cards'),

  categoryRules: () => api.get<CategoryRuleOut[]>('/category-rules'),
  createCategoryRule: (body: CategoryRuleCreate) => api.post<CategoryRuleOut>('/category-rules', body),
  updateCategoryRule: (id: number, body: CategoryRuleUpdate) => api.patch<CategoryRuleOut>(`/category-rules/${id}`, body),
  deleteCategoryRule: (id: number) => api.delete<void>(`/category-rules/${id}`),

  importFile: (file: File, preview: boolean) => api.upload<ImportResultOut>('/import', file, { preview }),
}
