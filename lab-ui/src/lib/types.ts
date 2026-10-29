export type Category =
  | "translation_fr_kab"
  | "translation_kab_fr"
  | "comprehension"
  | "culture"
  | "writing"
  | "conversation";

export const CATEGORIES: { id: Category; label: string }[] = [
  { id: "translation_fr_kab", label: "Traduction fr → kab" },
  { id: "translation_kab_fr", label: "Traduction kab → fr" },
  { id: "comprehension", label: "Compréhension" },
  { id: "culture", label: "Culture" },
  { id: "writing", label: "Écriture" },
  { id: "conversation", label: "Conversation" },
];

export const categoryLabel = (id: string) => CATEGORIES.find((c) => c.id === id)?.label ?? id;

export type Grading = "auto" | "human" | "auto+human";
export type Split = "public" | "private";
export type Status = "draft" | "ready";
export type Script = "latin" | "tifinagh";

export interface ItemFields {
  category: Category;
  subcategory: string | null;
  script: Script;
  prompt: string;
  source_text: string | null;
  context: string | null;
  references: string[];
  grading: Grading;
  expected_lang: string;
  difficulty: number;
  split: Split;
  status: Status;
  source: string;
  author: string | null;
  notes: string;
}

export interface Item extends ItemFields {
  id: string;
  created_at: string;
  updated_at: string;
}

export interface TestsetStatus {
  items: number;
  ready: number;
  by_category: Record<string, { total: number; ready: number }>;
  by_split: Record<string, number>;
  by_status: Record<string, number>;
  content_hash: string;
  manifest: { version: string; canary: string; generated_at: string } | null;
  repo_in_sync: boolean;
}

export interface ImportReport {
  created: number;
  updated: number;
  errors: { row: number; id: string | null; errors: string[] }[];
}

export interface GuidedEntry {
  id: string;
  theme: string | null;
  category: Category;
  guide: string;
  fill: ("references" | "source_text" | "context" | "prompt")[];
  prompt_template: string | null;
  prompt: string | null;
  source_text: string | null;
  item: Partial<ItemFields>;
  used_by: string | null;
}

export interface ModelInfo {
  key: string;
  label: string;
  provider: string;
  model: string;
  params: Record<string, unknown>;
  pricing: { input: number; output: number } | null;
  base: string | null;
  variant: "base" | "fewshot" | "rag" | "finetuned";
  available: boolean;
}

export interface Progress {
  run_id: number;
  status: string;
  active: boolean;
  total: number;
  pending: number;
  ok: number;
  error: number;
  cost_usd: number;
  by_model: Record<string, Record<string, number>>;
}

export interface Run {
  id: number;
  name: string;
  status: string;
  created_at: string;
  test_set_hash: string;
  test_set_version: string | null;
  model_keys: string[];
  categories: string[];
  sample_per_category: number | null;
  cost_usd: number;
  progress: Progress;
}

export interface Estimate {
  items: number;
  calls: number;
  by_category: Record<string, number>;
  models: { key: string; calls: number; cost_usd: number | null }[];
  cost_usd_known_models: number | null;
  note: string;
}

export interface RunResponse {
  id: string;
  item_id: string;
  model_key: string;
  status: string;
  output: string | null;
  error: string | null;
  chrf: number | null;
  lang_ok: boolean | null;
  latency_ms: number | null;
  cost_usd: number | null;
}

export interface BlindItem {
  response_id: string;
  item: Pick<
    ItemFields,
    "category" | "script" | "prompt" | "source_text" | "context" | "references" | "expected_lang" | "grading"
  > & { id: string };
  output: string | null;
  grade: { score: number; error_tags: string[]; comment: string } | null;
}

export interface Summary {
  n: number;
  n_graded: number;
  human_mean: number | null;
  human_pct: number | null;
  human_pct_ci95: [number, number] | null;
  score_distribution: Record<string, number>;
  chrf: number | null;
  n_chrf: number;
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
  n_paired_chrf: number;
  before_pct?: number;
  after_pct?: number;
  gain_points?: number;
  gain_relative_pct?: number | null;
  gain_points_ci95?: [number, number] | null;
  chrf_before?: number;
  chrf_after?: number;
  chrf_gain?: number;
}

export interface Results {
  test_set_hash: string | null;
  split: string;
  categories: { id: string; label: string }[];
  error_tags: Record<string, string>;
  models: ModelResult[];
  gains: {
    variant: string;
    variant_label: string;
    variant_type: string;
    base: string;
    overall: Gain;
    by_category: Record<string, Gain>;
  }[];
  metric_agreement?: MetricAgreement;
}

export interface MetricAgreement {
  n: number;
  spearman_human_chrf: number | null;
}

export interface ResponseRow {
  response_id: string;
  model_key: string;
  model_label: string;
  item: Item;
  output: string | null;
  chrf: number | null;
  lang_ok: boolean | null;
  detected_lang: string | null;
  script: string | null;
  score: number | null;
  error_tags: string[];
  comment: string;
  favorite: { kind: "success" | "error"; note: string } | null;
}

export interface SetupCheck {
  id: string;
  label: string;
  state: "ok" | "todo" | "warn" | "optional";
  detail: string;
  hint: string;
  command: string;
}

export interface SetupStatus {
  groups: { id: string; title: string; checks: SetupCheck[] }[];
  can_run_api_benchmark: boolean;
}
