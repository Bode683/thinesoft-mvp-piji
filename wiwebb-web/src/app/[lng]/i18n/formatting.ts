import { type Language } from './settings'

/**
 * Formats a date according to the user's locale
 * @param date - Date to format
 * @param locale - Language/locale code
 * @param options - Intl.DateTimeFormat options
 * @returns Formatted date string
 */
export function formatDate(
  date: Date | string | number,
  locale: Language,
  options?: Intl.DateTimeFormatOptions
): string {
  try {
    const dateObj = typeof date === 'string' || typeof date === 'number' ? new Date(date) : date

    if (isNaN(dateObj.getTime())) {
      console.error('Invalid date provided to formatDate:', date)
      return String(date)
    }

    const defaultOptions: Intl.DateTimeFormatOptions = {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      ...options,
    }

    return new Intl.DateTimeFormat(locale, defaultOptions).format(dateObj)
  } catch (error) {
    console.error('Error formatting date:', error)
    return String(date)
  }
}

/**
 * Formats a date with time according to the user's locale
 * @param date - Date to format
 * @param locale - Language/locale code
 * @param options - Intl.DateTimeFormat options
 * @returns Formatted date-time string
 */
export function formatDateTime(
  date: Date | string | number,
  locale: Language,
  options?: Intl.DateTimeFormatOptions
): string {
  const defaultOptions: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    ...options,
  }

  return formatDate(date, locale, defaultOptions)
}

/**
 * Formats a relative time (e.g., "3 days ago", "in 2 hours")
 * @param date - Date to compare
 * @param locale - Language/locale code
 * @param baseDate - Date to compare against (defaults to now)
 * @returns Formatted relative time string
 */
export function formatRelativeTime(
  date: Date | string | number,
  locale: Language,
  baseDate: Date = new Date()
): string {
  try {
    const dateObj = typeof date === 'string' || typeof date === 'number' ? new Date(date) : date

    if (isNaN(dateObj.getTime())) {
      console.error('Invalid date provided to formatRelativeTime:', date)
      return String(date)
    }

    const rtf = new Intl.RelativeTimeFormat(locale, { numeric: 'auto' })
    const diffInSeconds = (dateObj.getTime() - baseDate.getTime()) / 1000

    // Determine the best unit
    const units: Array<{ unit: Intl.RelativeTimeFormatUnit; seconds: number }> = [
      { unit: 'year', seconds: 31536000 },
      { unit: 'month', seconds: 2592000 },
      { unit: 'week', seconds: 604800 },
      { unit: 'day', seconds: 86400 },
      { unit: 'hour', seconds: 3600 },
      { unit: 'minute', seconds: 60 },
      { unit: 'second', seconds: 1 },
    ]

    for (const { unit, seconds } of units) {
      const value = diffInSeconds / seconds
      if (Math.abs(value) >= 1) {
        return rtf.format(Math.round(value), unit)
      }
    }

    return rtf.format(0, 'second')
  } catch (error) {
    console.error('Error formatting relative time:', error)
    return String(date)
  }
}

/**
 * Formats a number according to the user's locale
 * @param value - Number to format
 * @param locale - Language/locale code
 * @param options - Intl.NumberFormat options
 * @returns Formatted number string
 */
export function formatNumber(
  value: number,
  locale: Language,
  options?: Intl.NumberFormatOptions
): string {
  try {
    if (typeof value !== 'number' || isNaN(value)) {
      console.error('Invalid number provided to formatNumber:', value)
      return String(value)
    }

    return new Intl.NumberFormat(locale, options).format(value)
  } catch (error) {
    console.error('Error formatting number:', error)
    return String(value)
  }
}

/**
 * Formats a currency amount according to the user's locale
 * @param value - Amount to format
 * @param locale - Language/locale code
 * @param currency - Currency code (e.g., 'USD', 'EUR', 'GBP')
 * @param options - Additional Intl.NumberFormat options
 * @returns Formatted currency string
 */
export function formatCurrency(
  value: number,
  locale: Language,
  currency: string = 'USD',
  options?: Intl.NumberFormatOptions
): string {
  try {
    if (typeof value !== 'number' || isNaN(value)) {
      console.error('Invalid number provided to formatCurrency:', value)
      return String(value)
    }

    const defaultOptions: Intl.NumberFormatOptions = {
      style: 'currency',
      currency,
      ...options,
    }

    return new Intl.NumberFormat(locale, defaultOptions).format(value)
  } catch (error) {
    console.error('Error formatting currency:', error)
    return String(value)
  }
}

/**
 * Formats a percentage according to the user's locale
 * @param value - Value to format (0.5 = 50%)
 * @param locale - Language/locale code
 * @param options - Intl.NumberFormat options
 * @returns Formatted percentage string
 */
export function formatPercent(
  value: number,
  locale: Language,
  options?: Intl.NumberFormatOptions
): string {
  try {
    if (typeof value !== 'number' || isNaN(value)) {
      console.error('Invalid number provided to formatPercent:', value)
      return String(value)
    }

    const defaultOptions: Intl.NumberFormatOptions = {
      style: 'percent',
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
      ...options,
    }

    return new Intl.NumberFormat(locale, defaultOptions).format(value)
  } catch (error) {
    console.error('Error formatting percent:', error)
    return String(value)
  }
}

/**
 * Gets the plural form for a count (e.g., "item" vs "items")
 * Uses Intl.PluralRules for locale-aware pluralization
 * @param count - Number to check
 * @param locale - Language/locale code
 * @returns Plural category: 'zero', 'one', 'two', 'few', 'many', or 'other'
 */
export function getPluralForm(count: number, locale: Language): Intl.LDMLPluralRule {
  try {
    if (typeof count !== 'number' || isNaN(count)) {
      console.error('Invalid count provided to getPluralForm:', count)
      return 'other'
    }

    const pr = new Intl.PluralRules(locale)
    return pr.select(count)
  } catch (error) {
    console.error('Error getting plural form:', error)
    return 'other'
  }
}

/**
 * Formats a list of items according to the user's locale
 * @param items - Array of items to format
 * @param locale - Language/locale code
 * @param options - Intl.ListFormat options
 * @returns Formatted list string
 */
export function formatList(
  items: string[],
  locale: Language,
  options?: Intl.ListFormatOptions
): string {
  try {
    if (!Array.isArray(items) || items.length === 0) {
      return ''
    }

    const defaultOptions: Intl.ListFormatOptions = {
      style: 'long',
      type: 'conjunction',
      ...options,
    }

    return new Intl.ListFormat(locale, defaultOptions).format(items)
  } catch (error) {
    console.error('Error formatting list:', error)
    return items.join(', ')
  }
}
