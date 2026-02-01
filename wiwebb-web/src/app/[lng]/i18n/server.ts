import i18next from './i18next.server'
import { headerName, defaultNS } from './settings'
import { headers } from 'next/headers'
import type { TFunction } from 'i18next'

type Namespace = string | string[]

interface GetTOptions {
  keyPrefix?: string
}

export async function getT(ns: Namespace = defaultNS, options?: GetTOptions) {
  const headerList = await headers()
  const lng = headerList.get(headerName) || undefined

  if (lng && i18next.resolvedLanguage !== lng) {
    await i18next.changeLanguage(lng)
  }

  if (ns && !i18next.hasLoadedNamespace(ns)) {
    await i18next.loadNamespaces(ns)
  }

  const resolvedLng = lng ?? i18next.resolvedLanguage ?? 'en'
  const namespace = Array.isArray(ns) ? ns[0] : ns

  return {
    t: i18next.getFixedT(resolvedLng, namespace, options?.keyPrefix) as TFunction,
    i18n: i18next
  }
}