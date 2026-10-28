// Copie les résultats exportés par le labo (data/results/public/) dans le site.
// Sans résultats, le site affiche « résultats à venir » : aucun chiffre n'est inventé.
import { copyFileSync, existsSync, mkdirSync, readdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const source = join(root, "..", "data", "results", "public");
const dataDir = join(root, "src", "data");
const publicDir = join(root, "public");
mkdirSync(dataDir, { recursive: true });

const results = join(source, "results.json");
if (existsSync(results)) {
  copyFileSync(results, join(dataDir, "results.json"));
  console.log("results.json copié");
} else {
  writeFileSync(join(dataDir, "results.json"), JSON.stringify({ empty: true }) + "\n");
  console.log("Pas encore de résultats : le site affichera « résultats à venir »");
}

// Visuels générés par scripts/visuals (image de partage, graphiques LinkedIn)
const visuals = join(source, "visuals");
if (existsSync(visuals)) {
  mkdirSync(join(publicDir, "visuals"), { recursive: true });
  for (const file of readdirSync(visuals).filter((f) => f.endsWith(".png"))) {
    copyFileSync(join(visuals, file), join(publicDir, "visuals", file));
  }
  if (existsSync(join(visuals, "og.png"))) copyFileSync(join(visuals, "og.png"), join(publicDir, "og.png"));
}
