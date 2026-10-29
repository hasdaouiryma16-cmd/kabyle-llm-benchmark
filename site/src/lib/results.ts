import raw from "../data/results.json";

export interface Summary {
  n: number;
  n_graded: number;
  human_mean: number | null;
  human_pct: number | null;
  human_pct_ci95: [number, number] | null;
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
  examples: {
    kind: "success" | "error";
    note: string;
    model: string;
    model_key: string;
    item: { id: string; category: string; script: string; prompt: string; source_text: string | null; context: string | null; references: string[] };
    output: string | null;
    score: number | null;
    error_tags: string[];
    chrf: number | null;
  }[];
}

const data = raw as unknown as Results | { empty: true };

/** null tant que le labo n'a pas exporté de résultats réels. */
export const results: Results | null = "empty" in data ? null : data;

export const graded = (r: Results) => r.models.filter((m) => m.overall.n_graded > 0);
