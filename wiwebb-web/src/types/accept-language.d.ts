declare module 'accept-language' {
  interface AcceptLanguage {
    languages(langs: readonly string[] | string[]): void;
    get(header?: string | null): string | undefined;
  }

  const acceptLanguage: AcceptLanguage;
  export default acceptLanguage;
}
