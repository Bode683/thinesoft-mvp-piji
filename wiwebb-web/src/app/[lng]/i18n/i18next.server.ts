import i18next from 'i18next'
import resourcesToBackend from 'i18next-resources-to-backend'
import { fallbackLng, languages, defaultNS } from './settings'

// Server-side i18next instance (no React dependencies)
const serverI18next = i18next.createInstance()

serverI18next
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
    lng: fallbackLng,
    fallbackNS: defaultNS,
    defaultNS,
    ns: [defaultNS], // Explicitly specify namespace to load
    preload: languages as unknown as string[],
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
    console.error('Failed to initialize i18next server:', error)
  })

export default serverI18next
