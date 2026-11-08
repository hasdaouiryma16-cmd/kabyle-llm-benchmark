import react from "@astrojs/react";
import { defineConfig } from "astro/config";

// Hébergé sur Vercel, à la racine du domaine (comme le portfolio).
// SITE_URL et BASE_PATH permettent un autre hébergement (ex. GitHub Pages sous /kabyle-llm-benchmark/).
export default defineConfig({
  site: process.env.SITE_URL ?? "https://kabyle-llm-benchmark.vercel.app",
  base: process.env.BASE_PATH ?? "/",
  trailingSlash: "always",
  integrations: [react()],
  i18n: {
    defaultLocale: "fr",
    locales: ["fr", "en"],
    routing: { prefixDefaultLocale: false },
  },
});
