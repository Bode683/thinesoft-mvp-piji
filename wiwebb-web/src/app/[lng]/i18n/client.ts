'use client'

import i18next from './i18next.client'
import { useParams } from 'next/navigation'
import { useEffect } from 'react'
import { useTranslation, type UseTranslationOptions } from 'react-i18next'

const runsOnServerSide = typeof window === 'undefined'

type Namespace = string | string[]

export function useT(ns?: Namespace, options?: UseTranslationOptions<undefined>) {
  const params = useParams()
  const lng = params?.lng
  const translation = useTranslation(ns, options)

  if (typeof lng !== 'string') {
    throw new Error('useT is only available inside /src/app/[lng] routes')
  }

  // Change language when route changes
  useEffect(() => {
    if (!lng || i18next.resolvedLanguage === lng) return
    i18next.changeLanguage(lng).catch((error) => {
      console.error(`Failed to change language to ${lng}:`, error)
    })
  }, [lng])

  // Handle server-side language change (no hooks needed here)
  if (runsOnServerSide && i18next.resolvedLanguage !== lng) {
    i18next.changeLanguage(lng).catch((error) => {
      console.error(`Failed to change language to ${lng} on server:`, error)
    })
  }

  return translation
}