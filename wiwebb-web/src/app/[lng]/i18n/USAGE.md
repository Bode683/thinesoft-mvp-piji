# i18n Usage Guide

This guide explains how to use the internationalization (i18n) utilities in this application.

## Basic Translation

### In Client Components

```tsx
'use client'

import { useT } from '@/app/lib/i18n'

export default function MyComponent() {
  const { t } = useT()

  return <h1>{t('welcome')}</h1>
}
```

### In Server Components

```tsx
import { getT } from '@/app/lib/i18n'

export default async function MyServerComponent({
  params: { lng }
}: {
  params: { lng: string }
}) {
  const { t } = await getT(lng)

  return <h1>{t('welcome')}</h1>
}
```

## Date Formatting

```tsx
import { useParams } from 'next/navigation'
import { formatDate, formatDateTime, formatRelativeTime } from '@/app/lib/i18n'

export default function DateExample() {
  const params = useParams()
  const lng = params?.lng as string

  const date = new Date('2024-03-15')

  return (
    <div>
      {/* Format date: "March 15, 2024" (en) or "15 mars 2024" (fr) */}
      <p>{formatDate(date, lng)}</p>

      {/* Format with custom options */}
      <p>{formatDate(date, lng, { dateStyle: 'short' })}</p>

      {/* Format date and time */}
      <p>{formatDateTime(date, lng)}</p>

      {/* Relative time: "3 days ago", "in 2 hours" */}
      <p>{formatRelativeTime(date, lng)}</p>
    </div>
  )
}
```

## Number Formatting

```tsx
import { useParams } from 'next/navigation'
import { formatNumber, formatCurrency, formatPercent } from '@/app/lib/i18n'

export default function NumberExample() {
  const params = useParams()
  const lng = params?.lng as string

  return (
    <div>
      {/* Format number: "1,234.56" (en) or "1 234,56" (fr) */}
      <p>{formatNumber(1234.56, lng)}</p>

      {/* Format currency: "$1,234.56" (en) or "1 234,56 $US" (fr) */}
      <p>{formatCurrency(1234.56, lng, 'USD')}</p>

      {/* Format percentage: "50%" */}
      <p>{formatPercent(0.5, lng)}</p>
    </div>
  )
}
```

## Plural Forms

```tsx
import { useParams } from 'next/navigation'
import { getPluralForm } from '@/app/lib/i18n'

export default function PluralExample() {
  const params = useParams()
  const lng = params?.lng as string

  const count = 5
  const pluralForm = getPluralForm(count, lng) // 'one', 'other', etc.

  const messages = {
    one: 'You have 1 item',
    other: `You have ${count} items`,
  }

  return <p>{messages[pluralForm] || messages.other}</p>
}
```

## List Formatting

```tsx
import { useParams } from 'next/navigation'
import { formatList } from '@/app/lib/i18n'

export default function ListExample() {
  const params = useParams()
  const lng = params?.lng as string

  const items = ['Apple', 'Orange', 'Banana']

  return (
    <div>
      {/* "Apple, Orange, and Banana" (en) or "Apple, Orange et Banana" (fr) */}
      <p>{formatList(items, lng)}</p>

      {/* Disjunction: "Apple, Orange, or Banana" */}
      <p>{formatList(items, lng, { type: 'disjunction' })}</p>
    </div>
  )
}
```

## Error Boundary

Wrap your components with `TranslationErrorBoundary` to prevent crashes from translation errors:

```tsx
import { TranslationErrorBoundary } from '@/app/lib/i18n'

export default function MyLayout({ children }: { children: React.ReactNode }) {
  return (
    <TranslationErrorBoundary
      fallback={<div>Failed to load translations. Please refresh.</div>}
      onError={(error, errorInfo) => {
        // Log to your error tracking service
        console.error('Translation error:', error, errorInfo)
      }}
    >
      {children}
    </TranslationErrorBoundary>
  )
}
```

## Language Detection Order

The application detects language in this order:

1. **URL path** - `/en/page` or `/fr/page`
2. **Cookie** - `i18next` cookie (validated)
3. **Accept-Language header** - From browser
4. **Default** - Falls back to English

## Security Features

- Language codes are validated against supported languages
- Invalid language codes are rejected
- Cookies are set with security flags in production:
  - `sameSite: 'lax'`
  - `secure: true` (production only)
  - `maxAge: 1 year`

## Error Handling

- Missing translation keys log warnings in development
- Failed translation loads return empty objects (no crashes)
- `returnEmptyString: false` ensures keys are shown instead of blank strings
- Error boundaries catch rendering errors

## Adding New Languages

1. Add language to `settings.ts`:
```ts
export const languages = [fallbackLng, 'fr', 'es'] as const
```

2. Create translation folder:
```
src/app/lib/i18n/locales/es/common.json
```

3. Add translations to the JSON file

4. Restart the development server

## Best Practices

1. **Always use translation keys** - Avoid hardcoded strings
2. **Use formatting utilities** - Don't format dates/numbers manually
3. **Wrap with error boundaries** - Prevent translation errors from crashing the app
4. **Test in all languages** - Ensure translations are complete
5. **Use namespaces** - Organize translations by feature (coming soon)
6. **Validate user input** - Don't trust language codes from external sources
