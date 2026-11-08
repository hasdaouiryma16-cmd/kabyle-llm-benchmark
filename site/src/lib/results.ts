import raw from "../data/results.json";

export interface Summary {
  n: number;
  n_graded: number;
  human_mean: number | null;
  human_pct: number | null;
  human_pct_ci95: [number, number] | null;
  score_distribution?: Record<string, number>;
  chrf: number | null;
  lang_ok_rate: number | null;
  n_lang_checked: number;
}

export interface ModelResult {
  key: string;
  label: string;
  provider: string | null;
  model: string | null;
  variant: string;
  base: string | null;
  overall: Summary;
  by_category: Record<string, Summary>;
  error_tags: Record<string, number>;
}

export interface Gain {
  n_paired: number;
  before_pct?: number;
  after_pct?: number;
  gain_points?: number;
  gain_relative_pct?: number | null;
  gain_points_ci95?: [number, number] | null;
  chrf_before?: number;
  chrf_after?: number;
}

export interface PublicItem {
  id: string;
  category: string;
  script: string;
  prompt: string;
  source_text: string | null;
  context: string | null;
  references: string[];
  answers: { model_key: string; output: string | null; score: number | null; chrf: number | null }[];
}

export interface Results {
  generated_at: string;
  test_set: {
    version: string | null;
    content_hash: string;
    items: number | null;
    public_items: number | null;
    private_items: number | null;
    canary: string | null;
  };
  categories: { id: string; label_fr: string; label_en: string }[];
  error_tags: { id: string; label_fr: string; label_en: string }[];
  models: ModelResult[];
  gains: {
    variant: string;
    variant_label: string;
    variant_type: string;
    base: string;
    overall: Gain;
    by_category: Record<string, Gain>;
  }[];
  metric_agreement?: { n: number; spearman_human_chrf: number | null };
  examples: unknown[];
  items?: PublicItem[];
}

const data = raw as unknown as Results | { empty: true };

/** null tant que le labo n'a pas exporté de résultats réels. */
export const results: Results | null = "empty" in data ? null : data;

export const graded = (r: Results) => r.models.filter((m) => m.overall.n_graded > 0);

/** Méthodes d'aide, dans l'ordre de présentation ; la couleur suit la méthode, jamais le rang. */
export const METHODS = ["base", "fewshot", "rag", "finetuned"] as const;
export type Method = (typeof METHODS)[number];

export interface Family {
  key: string; // clé du modèle de base
  label: string;
  provider: string | null;
  local: boolean; // poids ouverts, exécuté sur notre machine (Ollama)
  byMethod: Partial<Record<Method, ModelResult>>;
}

/** Regroupe chaque variante avec son modèle de base (une « famille » par modèle). */
export function families(r: Results): Family[] {
  const ranked = graded(r);
  const out = new Map<string, Family>();
  for (const m of ranked) {
    const baseKey = m.base ?? m.key;
    const base = ranked.find((x) => x.key === baseKey) ?? m;
    const fam = out.get(baseKey) ?? {
      key: baseKey,
      label: base.label,
      provider: base.provider,
      local: base.provider === "ollama",
      byMethod: {},
    };
    fam.byMethod[(m.variant as Method) ?? "base"] = m;
    out.set(baseKey, fam);
  }
  const best = (f: Family) => Math.max(...Object.values(f.byMethod).map((m) => m?.overall.human_pct ?? 0));
  return [...out.values()].sort((a, b) => (b.byMethod.base?.overall.human_pct ?? 0) - (a.byMethod.base?.overall.human_pct ?? 0) || best(b) - best(a));
}

export const ranked = (r: Results) =>
  [...graded(r)].sort((a, b) => (b.overall.human_pct ?? 0) - (a.overall.human_pct ?? 0));

export const totalGraded = (r: Results) => graded(r).reduce((s, m) => s + m.overall.n_graded, 0);

export const categoryCount = (r: Results, cat: string) => r.items?.filter((i) => i.category === cat).length ?? 0;
