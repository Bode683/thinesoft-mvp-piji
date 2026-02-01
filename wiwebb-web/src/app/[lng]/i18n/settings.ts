export const fallbackLng = 'en' as const
export const languages = [fallbackLng, 'fr'] as const
export const defaultNS = 'common' as const
export const cookieName = 'i18next' as const
export const headerName = 'x-i18next-current-language' as const

export type Language = (typeof languages)[number]