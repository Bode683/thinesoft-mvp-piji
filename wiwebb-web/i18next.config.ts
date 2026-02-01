import { defineConfig } from 'i18next-cli';

export default defineConfig({
  locales: [
    "en",
    "fr"
  ],
  extract: {
    input: "src/**/*.{js,jsx,ts,tsx}",
    output: "src/app/lib/i18n/locales/{{language}}/{{namespace}}.json"
  }
});