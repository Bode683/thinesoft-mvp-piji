import { ThemeToggle } from "@/components/theme-toggle";
import { getT } from "@/app/[lng]/i18n";

export default async function Home() {
  const { t } = await getT('common');

  return (
    <div className="min-h-screen bg-background text-foreground">
      <ThemeToggle />

      <main className="container mx-auto px-4 py-16">
        {/* Header */}
        <div className="mb-12 text-center">
          <h1 className="mb-4 text-4xl font-bold tracking-tight">
            {t('theme.title')}
          </h1>
          <p className="text-lg text-muted-foreground">
            {t('theme.description')}
          </p>
        </div>

        {/* Featured Cards with Light/Dark Support */}
        <section className="mb-12">
          <h2 className="mb-6 text-2xl font-semibold">{t('sections.featuredCards')}</h2>
          <div className="grid gap-6 md:grid-cols-2">
            <div className="group overflow-hidden rounded-xl border bg-card text-card-foreground shadow-lg transition-all hover:shadow-xl">
              <div className="bg-primary p-6 text-primary-foreground">
                <h3 className="text-xl font-bold">{t('cards.premium.title')}</h3>
              </div>
              <div className="p-6">
                <p className="mb-4 text-muted-foreground">
                  {t('cards.premium.description')}
                </p>
                <div className="flex gap-3">
                  <button className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90">
                    {t('cards.premium.primaryAction')}
                  </button>
                  <button className="rounded-md border border-input bg-background px-4 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground">
                    {t('cards.premium.secondary')}
                  </button>
                </div>
              </div>
            </div>

            <div className="overflow-hidden rounded-xl border bg-gradient-to-br from-card to-muted text-card-foreground shadow-lg transition-all hover:shadow-xl">
              <div className="p-6">
                <div className="mb-4 inline-block rounded-lg bg-accent p-3 text-accent-foreground">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
                  </svg>
                </div>
                <h3 className="mb-2 text-xl font-bold">{t('cards.gradient.title')}</h3>
                <p className="mb-4 text-sm text-muted-foreground">
                  {t('cards.gradient.description')}
                </p>
                <button className="w-full rounded-md border border-primary bg-primary/10 px-4 py-2 text-sm font-medium text-primary transition-colors hover:bg-primary hover:text-primary-foreground">
                  {t('cards.gradient.action')}
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* Color Palette */}
        <section className="mb-12">
          <h2 className="mb-6 text-2xl font-semibold">Color Palette</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <div className="rounded-lg bg-primary p-6 text-primary-foreground">
              <h3 className="font-semibold">Primary</h3>
              <p className="text-sm opacity-90">Main brand color</p>
            </div>
            <div className="rounded-lg bg-secondary p-6 text-secondary-foreground">
              <h3 className="font-semibold">Secondary</h3>
              <p className="text-sm opacity-90">Secondary color</p>
            </div>
            <div className="rounded-lg bg-accent p-6 text-accent-foreground">
              <h3 className="font-semibold">Accent</h3>
              <p className="text-sm opacity-90">Accent highlights</p>
            </div>
            <div className="rounded-lg bg-muted p-6 text-muted-foreground">
              <h3 className="font-semibold">Muted</h3>
              <p className="text-sm opacity-90">Subtle backgrounds</p>
            </div>
            <div className="rounded-lg bg-destructive p-6 text-destructive-foreground">
              <h3 className="font-semibold">Destructive</h3>
              <p className="text-sm opacity-90">Error/danger states</p>
            </div>
            <div className="rounded-lg border bg-card p-6 text-card-foreground">
              <h3 className="font-semibold">Card</h3>
              <p className="text-sm text-muted-foreground">Card container</p>
            </div>
          </div>
        </section>

        {/* Typography */}
        <section className="mb-12">
          <h2 className="mb-6 text-2xl font-semibold">Typography</h2>
          <div className="space-y-4">
            <h1 className="text-4xl font-bold">Heading 1</h1>
            <h2 className="text-3xl font-bold">Heading 2</h2>
            <h3 className="text-2xl font-semibold">Heading 3</h3>
            <p className="text-base">
              Regular paragraph text with normal weight and spacing.
            </p>
            <p className="text-sm text-muted-foreground">
              Muted text for secondary information and descriptions.
            </p>
          </div>
        </section>

        {/* Buttons & Borders */}
        <section className="mb-12">
          <h2 className="mb-6 text-2xl font-semibold">Interactive Buttons</h2>
          <div className="space-y-6">
            <div>
              <h3 className="mb-3 text-sm font-medium text-muted-foreground">Solid Buttons</h3>
              <div className="flex flex-wrap gap-3">
                <button className="rounded-lg bg-primary px-6 py-3 font-medium text-primary-foreground shadow-sm transition-all hover:opacity-90 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2">
                  Primary
                </button>
                <button className="rounded-lg bg-secondary px-6 py-3 font-medium text-secondary-foreground shadow-sm transition-all hover:opacity-90 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2">
                  Secondary
                </button>
                <button className="rounded-lg bg-destructive px-6 py-3 font-medium text-destructive-foreground shadow-sm transition-all hover:opacity-90 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2">
                  Destructive
                </button>
              </div>
            </div>

            <div>
              <h3 className="mb-3 text-sm font-medium text-muted-foreground">Outline Buttons</h3>
              <div className="flex flex-wrap gap-3">
                <button className="rounded-lg border border-input bg-background px-6 py-3 font-medium transition-all hover:bg-accent hover:text-accent-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2">
                  Outline
                </button>
                <button className="rounded-lg border border-primary bg-background px-6 py-3 font-medium text-primary transition-all hover:bg-primary hover:text-primary-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2">
                  Primary Outline
                </button>
                <button className="rounded-lg border border-destructive bg-background px-6 py-3 font-medium text-destructive transition-all hover:bg-destructive hover:text-destructive-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2">
                  Danger Outline
                </button>
              </div>
            </div>

            <div>
              <h3 className="mb-3 text-sm font-medium text-muted-foreground">Ghost Buttons</h3>
              <div className="flex flex-wrap gap-3">
                <button className="rounded-lg px-6 py-3 font-medium transition-colors hover:bg-accent hover:text-accent-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2">
                  Ghost
                </button>
                <button className="rounded-lg px-6 py-3 font-medium text-primary transition-colors hover:bg-primary/10 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2">
                  Ghost Primary
                </button>
                <button className="rounded-lg px-6 py-3 font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2">
                  Ghost Muted
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* Cards with Shadows */}
        <section className="mb-12">
          <h2 className="mb-6 text-2xl font-semibold">Cards & Shadows</h2>
          <div className="grid gap-6 sm:grid-cols-2">
            <div className="rounded-xl border bg-card p-6 text-card-foreground shadow-sm">
              <h3 className="mb-2 text-lg font-semibold">Shadow SM</h3>
              <p className="text-sm text-muted-foreground">
                Subtle shadow for elevated content
              </p>
            </div>
            <div className="rounded-xl border bg-card p-6 text-card-foreground shadow-md">
              <h3 className="mb-2 text-lg font-semibold">Shadow MD</h3>
              <p className="text-sm text-muted-foreground">
                Medium shadow for more prominence
              </p>
            </div>
            <div className="rounded-xl border bg-card p-6 text-card-foreground shadow-lg">
              <h3 className="mb-2 text-lg font-semibold">Shadow LG</h3>
              <p className="text-sm text-muted-foreground">
                Large shadow for important cards
              </p>
            </div>
            <div className="rounded-xl border bg-card p-6 text-card-foreground shadow-xl">
              <h3 className="mb-2 text-lg font-semibold">Shadow XL</h3>
              <p className="text-sm text-muted-foreground">
                Extra large shadow for modals
              </p>
            </div>
          </div>
        </section>

        {/* Border Radius */}
        <section>
          <h2 className="mb-6 text-2xl font-semibold">Border Radius</h2>
          <div className="flex flex-wrap gap-4">
            <div className="flex h-20 w-20 items-center justify-center rounded-sm border bg-muted">
              <span className="text-xs">SM</span>
            </div>
            <div className="flex h-20 w-20 items-center justify-center rounded-md border bg-muted">
              <span className="text-xs">MD</span>
            </div>
            <div className="flex h-20 w-20 items-center justify-center rounded-lg border bg-muted">
              <span className="text-xs">LG</span>
            </div>
            <div className="flex h-20 w-20 items-center justify-center rounded-xl border bg-muted">
              <span className="text-xs">XL</span>
            </div>
            <div className="flex h-20 w-20 items-center justify-center rounded-2xl border bg-muted">
              <span className="text-xs">2XL</span>
            </div>
          </div>
        </section>

        {/* Theme toggle info */}
        <div className="mt-16 rounded-lg border bg-card p-8 text-center shadow-sm">
          <div className="mb-3 flex justify-center">
            <div className="rounded-full bg-primary p-3 text-primary-foreground">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <circle cx="12" cy="12" r="4" />
                <path d="M12 2v2" />
                <path d="M12 20v2" />
                <path d="m4.93 4.93 1.41 1.41" />
                <path d="m17.66 17.66 1.41 1.41" />
                <path d="M2 12h2" />
                <path d="M20 12h2" />
                <path d="m6.34 17.66-1.41 1.41" />
                <path d="m19.07 4.93-1.41 1.41" />
              </svg>
            </div>
          </div>
          <h3 className="mb-2 text-lg font-semibold">Theme Toggle Active</h3>
          <p className="text-sm text-muted-foreground">
            {t('theme.toggle')} {t('theme.saved')}
          </p>
        </div>
      </main>
    </div>
  );
}
