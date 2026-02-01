'use client'

import i18next from 'i18next'
import resourcesToBackend from 'i18next-resources-to-backend'
import { initReactI18next } from 'react-i18next'
import { fallbackLng, languages, defaultNS } from './settings'

const runsOnServerSide = typeof window === 'undefined'

// Client-side i18next instance (with React)
const clientI18next = i18next.createInstance()

clientI18next
  .use(initReactI18next)
  .use(
    resourcesToBackend((language: string, namespace: string) =>
      import(`./locales/${language}/${namespace}.json`).catch((error) => {
        console.error(`Failed to load translation: ${language}/${namespace}`, error)
        // Return empty object to prevent crashes
        return { default: {} }
      })
    )
  )
  .init({
    supportedLngs: languages as unknown as string[],
    fallbackLng,
    lng: undefined, // let detect the language on client side
    fallbackNS: defaultNS,
    defaultNS,
    ns: [defaultNS], // Explicitly specify namespace to load
    detection: {
      order: ['path', 'cookie', 'htmlTag', 'navigator'],
    },
    preload: runsOnServerSide ? (languages as unknown as string[]) : [],
    // Error handling configuration
    saveMissing: process.env.NODE_ENV === 'development',
    missingKeyHandler: (lngs, ns, key) => {
      if (process.env.NODE_ENV === 'development') {
        console.warn(`Missing translation key: ${key} in namespace: ${ns} for languages: ${lngs.join(', ')}`)
      }
    },
    // Return key as fallback instead of empty string
    returnEmptyString: false,
    returnNull: false,
  })
  .catch((error) => {
    console.error('Failed to initialize i18next client:', error)
  })

export default clientI18next
