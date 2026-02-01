// Export all i18n utilities
export { useT } from './client'
export { getT } from './server'
export { languages, fallbackLng, defaultNS, type Language } from './settings'
export {
  formatDate,
  formatDateTime,
  formatRelativeTime,
  formatNumber,
  formatCurrency,
  formatPercent,
  getPluralForm,
  formatList,
} from './formatting'
export { TranslationErrorBoundary } from './TranslationErrorBoundary'
