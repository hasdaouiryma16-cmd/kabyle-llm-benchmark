import { useCallback, useEffect, useState } from "react";
import { Alert, Badge, Button, Card, Empty, inputClass, inlineInputClass, PageHeader, Spinner, useToast, cx } from "../components/ui";
import { api, qs, useApi } from "../lib/api";
import { CATEGORIES, categoryLabel, type BlindItem, type Run } from "../lib/types";

const SCALE = [
  { score: 0, label: "Faux", hint: "hors sujet, incompréhensible ou mauvaise langue" },
  { score: 1, label: "Partiel", hint: "quelques éléments justes, erreurs importantes" },
  { score: 2, label: "Correct", hint: "sens juste, erreurs mineures (orthographe, tournure)" },
  { score: 3, label: "Parfait", hint: "correct et naturel" },
];

// Touches des étiquettes d'erreur, dans l'ordre renvoyé par l'API
const TAG_KEYS = "azertyuiopq";

export function GradePage() {
  const runs = useApi<Run[]>("/api/runs");
  const tags = useApi<{ id: string; label: string }[]>("/api/grading/tags");
  const [runId, setRunId] = useState("");
  const [category, setCategory] = useState("");
  const stats = useApi<{ total: number; graded: number; remaining: number }>(`/api/grading/stats${qs({ run_id: runId })}`);
  const [current, setCurrent] = useState<BlindItem | null | undefined>(undefined);
  const [history, setHistory] = useState<string[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [comment, setComment] = useState("");
  const [revealed, setRevealed] = useState<{ label: string; chrf: number | null } | null>(null);
  const notify = useToast();

  const show = useCallback((item: BlindItem | null) => {
    setCurrent(item);
    setSelectedTags(item?.grade?.error_tags ?? []);
    setComment(item?.grade?.comment ?? "");
    setRevealed(null);
  }, []);

  const loadNext = useCallback(async () => {
    show(await api.get<BlindItem | null>(`/api/grading/next${qs({ run_id: runId, category })}`));
  }, [runId, category, show]);

  useEffect(() => {
    void loadNext();
  }, [loadNext]);

  const submit = useCallback(
    async (score: number) => {
      if (!current) return;
      try {
        await api.put(`/api/grading/${current.response_id}`, { score, error_tags: selectedTags, comment });
        setHistory((h) => [...h, current.response_id]);
        stats.reload();
        await loadNext();
      } catch (e) {
        notify((e as Error).message, "error");
      }
    },
    [current, selectedTags, comment, loadNext, notify, stats],
  );

  async function back() {
    const previous = history.at(-1);
    if (!previous) return;
    setHistory((h) => h.slice(0, -1));
    show(await api.get<BlindItem>(`/api/grading/${previous}`));
  }

  async function reveal() {
    const last = history.at(-1);
    if (!last) return;
    setRevealed(await api.get(`/api/grading/${last}/reveal`));
  }

  // Raccourcis : 0–3 = noter et passer à la suivante, lettres = étiquettes, ← = précédente
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.tagName === "SELECT") return;
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      if (["0", "1", "2", "3"].includes(e.key)) {
        e.preventDefault();
        void submit(Number(e.key));
      } else if (e.key === "ArrowLeft") {
        void back();
      } else {
        const index = TAG_KEYS.indexOf(e.key.toLowerCase());
        const tag = tags.data?.[index];
        if (tag) setSelectedTags((s) => (s.includes(tag.id) ? s.filter((t) => t !== tag.id) : [...s, tag.id]));
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  const s = stats.data;
  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader
        title="Notation à l'aveugle"
        subtitle="Les réponses sont tirées au hasard ; le modèle n'est jamais affiché avant la note."
        actions={
          <>
            <select className={inlineInputClass} value={runId} onChange={(e) => setRunId(e.target.value)}>
              <option value="">Toutes les exécutions</option>
              {runs.data?.map((r) => (
                <option key={r.id} value={r.id}>
                  #{r.id} {r.name}
                </option>
              ))}
            </select>
            <select className={inlineInputClass} value={category} onChange={(e) => setCategory(e.target.value)}>
              <option value="">Toutes les catégories</option>
              {CATEGORIES.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.label}
                </option>
              ))}
            </select>
          </>
        }
      />

      {s && (
        <div className="mb-4 flex items-center gap-3 text-sm text-stone-600 dark:text-stone-400">
          <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-stone-200 dark:bg-neutral-800">
            <div className="h-full bg-teal-600" style={{ width: `${s.total ? (s.graded / s.total) * 100 : 0}%` }} />
          </div>
          <span className="tabular-nums">
            {s.graded} / {s.total} notées
          </span>
        </div>
      )}

      {revealed && (
        <div className="mb-4">
          <Alert tone="teal">
            Réponse précédente : <strong>{revealed.label}</strong>
            {revealed.chrf !== null && ` · chrF++ ${revealed.chrf}`}
          </Alert>
        </div>
      )}

      {current === undefined ? (
        <Spinner />
      ) : current === null ? (
        <Empty>Plus aucune réponse à noter pour cette sélection. 🎉</Empty>
      ) : (
        <div className="space-y-4">
          <Card className="space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone="teal">{categoryLabel(current.item.category)}</Badge>
              <Badge>réponse attendue en {current.item.expected_lang === "fr" ? "français" : "kabyle"}</Badge>
              {current.item.script === "tifinagh" && <Badge tone="violet">tifinagh</Badge>}
              {current.grade && <Badge tone="amber">déjà notée : {current.grade.score}</Badge>}
              <span className="ml-auto font-mono text-xs text-stone-400">{current.item.id}</span>
            </div>
            {current.item.context && (
              <div className="kab whitespace-pre-wrap rounded-lg bg-stone-100 p-3 dark:bg-neutral-800">{current.item.context}</div>
            )}
            <div>
              <div className="text-xs font-medium uppercase tracking-wide text-stone-500">Consigne</div>
              <div className="kab whitespace-pre-wrap">{current.item.prompt}</div>
            </div>
            {current.item.references.length > 0 && (
              <div>
                <div className="text-xs font-medium uppercase tracking-wide text-stone-500">Référence(s)</div>
                <ul className="kab list-disc pl-5">
                  {current.item.references.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
            )}
          </Card>

          <Card className="border-teal-600/40 dark:border-teal-500/40">
            <div className="text-xs font-medium uppercase tracking-wide text-stone-500">Réponse du modèle</div>
            <div className="kab mt-1 whitespace-pre-wrap text-lg leading-relaxed">
              {current.output?.trim() || <span className="italic text-stone-400">(réponse vide)</span>}
            </div>
          </Card>

          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            {SCALE.map((s) => (
              <button
                key={s.score}
                onClick={() => submit(s.score)}
                className={cx(
                  "rounded-xl border p-3 text-left transition-colors hover:border-teal-600 hover:bg-teal-50 dark:hover:bg-teal-950/40",
                  current.grade?.score === s.score ? "border-teal-600" : "border-stone-200 dark:border-neutral-800",
                )}
              >
                <div className="flex items-center justify-between">
                  <span className="text-2xl font-semibold">{s.score}</span>
                  <kbd>{s.score}</kbd>
                </div>
                <div className="font-medium">{s.label}</div>
                <div className="text-xs text-stone-500">{s.hint}</div>
              </button>
            ))}
          </div>

          <div className="flex flex-wrap gap-1.5">
            {tags.data?.map((t, i) => (
              <button
                key={t.id}
                onClick={() => setSelectedTags((s) => (s.includes(t.id) ? s.filter((x) => x !== t.id) : [...s, t.id]))}
                className={cx(
                  "rounded-full border px-2.5 py-1 text-xs",
                  selectedTags.includes(t.id)
                    ? "border-red-600 bg-red-50 text-red-800 dark:bg-red-950 dark:text-red-300"
                    : "border-stone-300 text-stone-600 dark:border-neutral-700 dark:text-stone-300",
                )}
              >
                <kbd className="mr-1">{TAG_KEYS[i]?.toUpperCase()}</kbd>
                {t.label}
              </button>
            ))}
          </div>
          <input className={inputClass} placeholder="Commentaire (facultatif)" value={comment} onChange={(e) => setComment(e.target.value)} />

          <div className="flex flex-wrap items-center gap-2 text-xs text-stone-500">
            <Button size="sm" variant="ghost" onClick={back} disabled={!history.length}>
              ← Précédente
            </Button>
            <Button size="sm" variant="ghost" onClick={reveal} disabled={!history.length}>
              Révéler le modèle de la réponse précédente
            </Button>
            <span className="ml-auto">
              <kbd>0</kbd>–<kbd>3</kbd> noter · lettres : étiquettes · <kbd>←</kbd> précédente
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
