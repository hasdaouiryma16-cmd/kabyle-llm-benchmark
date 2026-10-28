import react from "@astrojs/react";
import { defineConfig } from "astro/config";

// Publié sur GitHub Pages : https://hasdaouiryma16-cmd.github.io/kabyle-llm-benchmark/
export default defineConfig({
  site: "https://hasdaouiryma16-cmd.github.io",
  base: "/kabyle-llm-benchmark",
  integrations: [react()],
  i18n: {
    defaultLocale: "fr",
    locales: ["fr", "en"],
    routing: { prefixDefaultLocale: false },
  },
});
