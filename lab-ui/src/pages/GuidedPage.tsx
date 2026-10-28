import { useEffect, useMemo, useState } from "react";
import { CharBar } from "../components/CharBar";
import { readinessProblems, EMPTY_ITEM } from "../components/ItemEditor";
import { Alert, Badge, Button, Card, Empty, Field, inputClass, PageHeader, Spinner, useToast } from "../components/ui";
import { api, ApiError, useApi } from "../lib/api";
import { categoryLabel, type GuidedEntry, type ItemFields } from "../lib/types";

const SKIPPED_KEY = "guided-skipped";

function loadSkipped(): string[] {
  try {
    return JSON.parse(localStorage.getItem(SKIPPED_KEY) ?? "[]");
  } catch {
    return [];
  }
}

const FIELD_LABELS = {
  source_text: "Texte source (en kabyle)",
  context: "Texte de compréhension (en kabyle)",
  prompt: "Consigne à envoyer au modèle",
  references: "Réponse(s) de référence",
};

export function GuidedPage() {
  const guided = useApi<GuidedEntry[]>("/api/guided");
  const [skipped, setSkipped] = useState<string[]>(loadSkipped);
  const [index, setIndex] = useState(0);
  const [values, setValues] = useState({ source_text: "", context: "", prompt: "", references: [""] });
  const [isPrivate, setIsPrivate] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const notify = useToast();

  const queue = useMemo(
    () => (guided.data ?? []).filter((e) => !e.used_by && !skipped.includes(e.id)),
    [guided.data, skipped],
  );
  const entry = queue[Math.min(index, queue.length - 1)];
  const done = (guided.data ?? []).filter((e) => e.used_by).length;

  useEffect(() => {
    try {
      localStorage.setItem(SKIPPED_KEY, JSON.stringify(skipped));
    } catch {
      /* stockage indisponible : sans conséquence */
    }
  }, [skipped]);

  const reset = () => {
    setValues({ source_text: "", context: "", prompt: "", references: [""] });
    setIsPrivate(false);
    setError(null);
  };

  function buildItem(status: "ready" | "draft"): ItemFields {
    const fill = new Set(entry.fill);
    const source_text = fill.has("source_text") ? values.source_text.trim() : entry.source_text;
    let prompt = fill.has("prompt") ? values.prompt.trim() : (entry.prompt ?? "");
    if (entry.prompt_template) prompt = entry.prompt_template.replace("{source_text}", source_text ?? "");
    return {
      ...EMPTY_ITEM,
      category: entry.category,
      expected_lang: entry.category === "translation_kab_fr" ? "fr" : "kab",
      ...entry.item,
      subcategory: entry.theme,
      prompt,
      source_text: source_text || null,
      context: fill.has("context") ? values.context.trim() || null : null,
      references: values.references.map((r) => r.trim()).filter(Boolean),
      split: isPrivate ? "private" : "public",
      status,
      source: `guided:${entry.id}`,
    };
  }

  async function save(status: "ready" | "draft") {
    setError(null);
    try {
      const created = await api.post<{ id: string }>("/api/tests", buildItem(status));
      notify(`${created.id} enregistré${status === "draft" ? " en brouillon" : ""}`);
      reset();
      guided.reload();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
    }
  }

  function skip() {
    if (!entry) return;
    setSkipped((s) => [...s, entry.id]);
    reset();
  }

  // Ctrl+Entrée : enregistrer
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Enter" && (e.ctrlKey || e.metaKey) && entry) {
        e.preventDefault();
        void save("ready");
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  if (guided.loading && !guided.data) return <Spinner />;
  if (guided.error) return <Alert>{guided.error}</Alert>;

  const total = guided.data?.length ?? 0;
  const preview = entry ? buildItem("ready") : null;
  const problems = preview ? readinessProblems(preview) : [];
  const kabyle = { spellCheck: false, lang: "kab", className: `${inputClass} kab` };

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader
        title="Mode guidé"
        subtitle={`${done} / ${total} consignes traitées · ${skipped.length} passée(s)`}
        actions={
          skipped.length > 0 && (
            <Button size="sm" variant="ghost" onClick={() => setSkipped([])}>
              Revoir les consignes passées
            </Button>
          )
        }
      />
      <div className="mb-4 h-1.5 overflow-hidden rounded-full bg-stone-200 dark:bg-neutral-800">
        <div className="h-full bg-teal-600 transition-all" style={{ width: `${total ? (done / total) * 100 : 0}%` }} />
      </div>

      {!entry ? (
        <Empty>Toutes les consignes ont été traitées. Bravo ! Ajoutez-en dans data/prompts/guided_fr.yaml.</Empty>
      ) : (
        <Card className="space-y-5">
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone="teal">{categoryLabel(entry.category)}</Badge>
            {entry.theme && <Badge>{entry.theme}</Badge>}
            <span className="ml-auto font-mono text-xs text-stone-400">{entry.id}</span>
          </div>
          <p className="text-lg leading-snug">{entry.guide}</p>

          {entry.prompt && !entry.fill.includes("prompt") && (
            <div className="rounded-lg bg-stone-100 p-3 text-sm dark:bg-neutral-800">
              <div className="mb-1 text-xs font-medium uppercase tracking-wide text-stone-500">Consigne envoyée au modèle</div>
              {entry.prompt}
            </div>
          )}

          <CharBar />

          {entry.fill.includes("source_text") && (
            <Field label={FIELD_LABELS.source_text}>
              <textarea rows={2} {...kabyle} value={values.source_text} onChange={(e) => setValues({ ...values, source_text: e.target.value })} autoFocus />
            </Field>
          )}
          {entry.fill.includes("context") && (
            <Field label={FIELD_LABELS.context}>
              <textarea rows={5} {...kabyle} value={values.context} onChange={(e) => setValues({ ...values, context: e.target.value })} autoFocus />
            </Field>
          )}
          {entry.fill.includes("prompt") && (
            <Field label={FIELD_LABELS.prompt}>
              <textarea rows={2} {...kabyle} value={values.prompt} onChange={(e) => setValues({ ...values, prompt: e.target.value })} autoFocus={!entry.fill.includes("context")} />
            </Field>
          )}
          {entry.fill.includes("references") && (
            <Field label={FIELD_LABELS.references} hint="Ajoutez des variantes si plusieurs réponses sont correctes.">
              <div className="space-y-2">
                {values.references.map((ref, i) => (
                  <input
                    key={i}
                    {...kabyle}
                    autoFocus={i === 0 && entry.fill.length === 1}
                    value={ref}
                    placeholder={i === 0 ? "Référence" : "Variante acceptable"}
                    onChange={(e) =>
                      setValues({ ...values, references: values.references.map((r, j) => (j === i ? e.target.value : r)) })
                    }
                  />
                ))}
                <Button size="sm" onClick={() => setValues({ ...values, references: [...values.references, ""] })}>
                  + Variante
                </Button>
              </div>
            </Field>
          )}

          {preview && entry.prompt_template && (
            <div className="text-xs text-stone-500">
              Consigne générée : <span className="kab text-stone-700 dark:text-stone-300">{preview.prompt}</span>
            </div>
          )}

          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={isPrivate} onChange={(e) => setIsPrivate(e.target.checked)} />
            Partie privée (non publiée, ~20 % des tests)
          </label>

          {error && <Alert>{error}</Alert>}

          <div className="flex flex-wrap items-center justify-between gap-2 border-t border-stone-200 pt-4 dark:border-neutral-800">
            <div className="flex gap-2">
              <Button variant="ghost" onClick={skip}>
                Passer
              </Button>
              <Button variant="ghost" onClick={() => setIndex((i) => (i + 1) % Math.max(queue.length, 1))}>
                Plus tard
              </Button>
            </div>
            <div className="flex items-center gap-2">
              <Button onClick={() => save("draft")}>Brouillon</Button>
              <Button variant="primary" onClick={() => save("ready")} disabled={problems.length > 0}>
                Enregistrer <kbd>Ctrl</kbd>+<kbd>Entrée</kbd>
              </Button>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
