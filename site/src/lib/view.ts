import type { Lang } from "./i18n";
import type { Method } from "./results";

/** Couleur (variable CSS) et forme de chaque méthode : la forme double la couleur pour les daltoniens. */
export const METHOD_STYLE: Record<Method, { color: string; shape: string }> = {
  base: { color: "var(--m-base)", shape: "ring" },
  fewshot: { color: "var(--m-fewshot)", shape: "circle" },
  rag: { color: "var(--m-rag)", shape: "square" },
  finetuned: { color: "var(--m-finetuned)", shape: "diamond" },
};

export const fmt = (v: number | null | undefined, lang: Lang, digits = 1) =>
  v === null || v === undefined
    ? "—"
    : v.toLocaleString(lang === "fr" ? "fr-FR" : "en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits });

export const pct = (v: number | null | undefined, lang: Lang, digits = 1) =>
  v === null || v === undefined ? "—" : lang === "fr" ? `${fmt(v, lang, digits)} %` : `${fmt(v, lang, digits)}%`;

export const signed = (v: number | null | undefined, lang: Lang) =>
  v === null || v === undefined ? "—" : `${v >= 0 ? "+" : "−"}${fmt(Math.abs(v), lang)}`;

/** Liste lisible : « A, B et C » / « A, B and C ». */
export const joinList = (xs: string[], lang: Lang) =>
  xs.length <= 1 ? (xs[0] ?? "") : `${xs.slice(0, -1).join(", ")} ${lang === "fr" ? "et" : "and"} ${xs[xs.length - 1]}`;

/** Le texte passe en blanc au-delà de ce seuil d'intensité (contraste sur la teinte). */
export const isHigh = (v: number | null | undefined) => (v ?? 0) >= 58;
