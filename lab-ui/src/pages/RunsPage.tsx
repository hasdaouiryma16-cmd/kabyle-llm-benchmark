import { useEffect, useMemo, useState } from "react";
import { Alert, Badge, Button, Card, Empty, Field, inputClass, Modal, PageHeader, ProgressBar, Spinner, useToast } from "../components/ui";
import { api, useApi } from "../lib/api";
import { CATEGORIES, type Category, type Estimate, type ModelInfo, type Progress, type Run, type RunResponse } from "../lib/types";

const STATUS: Record<string, { label: string; tone: "neutral" | "teal" | "amber" | "red" | "green" }> = {
  pending: { label: "en attente", tone: "neutral" },
  running: { label: "en cours", tone: "teal" },
  completed: { label: "terminé", tone: "green" },
  cancelled: { label: "annulé", tone: "neutral" },
  interrupted: { label: "interrompu", tone: "amber" },
  stopped_cost: { label: "plafond de coût", tone: "red" },
};

const VARIANT_LABEL: Record<string, string> = { fewshot: "few-shot", rag: "RAG", finetuned: "fine-tuné" };

/** Suit la progression d'un run en direct (Server-Sent Events). */
function useLiveProgress(runId: number, enabled: boolean, onDone: () => void) {
  const [progress, setProgress] = useState<Progress | null>(null);
  useEffect(() => {
    if (!enabled) return;
    const source = new EventSource(`/api/runs/${runId}/events`);
    source.onmessage = (e) => {
      const p = JSON.parse(e.data) as Progress;
      setProgress(p);
      if (!p.active && p.status !== "running") {
        source.close();
        onDone();
      }
    };
    source.onerror = () => source.close();
    return () => source.close();
  }, [runId, enabled, onDone]);
  return progress;
}

export function RunsPage() {
  const runs = useApi<Run[]>("/api/runs");
  const models = useApi<ModelInfo[]>("/api/models");
  const [showNew, setShowNew] = useState(false);
  const [detail, setDetail] = useState<Run | null>(null);

  return (
    <div>
      <PageHeader
        title="Exécutions"
        subtitle="Mêmes consignes et paramètres enregistrés pour chaque modèle. Une exécution interrompue reprend là où elle s'est arrêtée."
        actions={
          <Button variant="primary" onClick={() => setShowNew(true)}>
            + Nouvelle exécution
          </Button>
        }
      />
      {runs.loading && !runs.data ? (
        <Spinner />
      ) : !runs.data?.length ? (
        <Empty>Aucune exécution. Commencez par un mode test sur 2 questions par catégorie pour vérifier les coûts.</Empty>
      ) : (
        <div className="space-y-3">
          {runs.data.map((run) => (
            <RunRow key={run.id} run={run} onChanged={runs.reload} onOpen={() => setDetail(run)} />
          ))}
        </div>
      )}
      {showNew && models.data && (
        <NewRun
          models={models.data}
          onClose={() => setShowNew(false)}
          onStarted={() => {
            setShowNew(false);
            runs.reload();
          }}
        />
      )}
      {detail && <RunDetail run={detail} onClose={() => setDetail(null)} />}
    </div>
  );
}

function RunRow({ run, onChanged, onOpen }: { run: Run; onChanged: () => void; onOpen: () => void }) {
  const live = useLiveProgress(run.id, run.progress.active, onChanged);
  const p = live ?? run.progress;
  const status = STATUS[p.status] ?? { label: p.status, tone: "neutral" as const };
  const notify = useToast();

  async function action(path: string, message: string) {
    try {
      await api.post(path);
      notify(message);
      onChanged();
    } catch (e) {
      notify((e as Error).message, "error");
    }
  }

  return (
    <Card className="flex flex-wrap items-center gap-4">
      <div className="min-w-48 flex-1">
        <div className="flex items-center gap-2">
          <button className="font-medium hover:underline" onClick={onOpen}>
            {run.name}
          </button>
          <Badge tone={status.tone}>{status.label}</Badge>
          {run.sample_per_category && <Badge tone="amber">test · {run.sample_per_category}/catégorie</Badge>}
        </div>
        <div className="mt-0.5 text-xs text-stone-500">
          #{run.id} · {new Date(run.created_at).toLocaleString("fr-FR")} · {run.model_keys.length} modèle(s) · jeu{" "}
          {run.test_set_version ?? "non versionné"} ({run.test_set_hash.slice(0, 8)})
        </div>
      </div>
      <div className="w-64">
        <ProgressBar ok={p.ok} error={p.error} total={p.total} />
        <div className="mt-1 flex justify-between text-xs tabular-nums text-stone-500">
          <span>
            {p.ok} ok · {p.error} erreur(s) · {p.pending} en attente
          </span>
          <span>{p.cost_usd.toFixed(4)} $</span>
        </div>
      </div>
      <div className="flex gap-2">
        {p.active ? (
          <Button size="sm" onClick={() => action(`/api/runs/${run.id}/cancel`, "Annulation demandée")}>
            Annuler
          </Button>
        ) : (
          (p.pending > 0 || p.error > 0) && (
            <Button size="sm" onClick={() => action(`/api/runs/${run.id}/resume`, "Reprise lancée")}>
              Reprendre
            </Button>
          )
        )}
      </div>
    </Card>
  );
}

function NewRun({ models, onClose, onStarted }: { models: ModelInfo[]; onClose: () => void; onStarted: () => void }) {
  const [name, setName] = useState(`Run du ${new Date().toLocaleDateString("fr-FR")}`);
  const [selected, setSelected] = useState<string[]>([]);
  const [categories, setCategories] = useState<Category[]>(CATEGORIES.map((c) => c.id));
  const [testMode, setTestMode] = useState(true);
  const [sample, setSample] = useState(2);
  const [chosenSplit, setSplit] = useState("");
  // Une offre gratuite sélectionnée impose la partie publique (l'API refuse le reste)
  const publicOnly = models.some((m) => m.public_only && selected.includes(m.key));
  const split = publicOnly ? "public" : chosenSplit;
  const [estimate, setEstimate] = useState<Estimate | null>(null);
  const [error, setError] = useState<string | null>(null);
  const notify = useToast();

  const payload = useMemo(
    () => ({
      name,
      model_keys: selected,
      categories,
      split: split || null,
      sample_per_category: testMode ? sample : null,
    }),
    [name, selected, categories, split, testMode, sample],
  );

  useEffect(() => {
    if (!selected.length || !categories.length) return setEstimate(null);
    const timer = setTimeout(() => {
      api
        .post<Estimate>("/api/runs/estimate", payload)
        .then((e) => (setEstimate(e), setError(null)))
        .catch((e: Error) => setError(e.message));
    }, 250);
    return () => clearTimeout(timer);
  }, [payload, selected.length, categories.length]);

  const byProvider = models.reduce<Record<string, ModelInfo[]>>((acc, m) => {
    (acc[m.provider] ??= []).push(m);
    return acc;
  }, {});

  async function launch() {
    try {
      await api.post("/api/runs", payload);
      notify("Exécution lancée");
      onStarted();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  const toggle = <T,>(list: T[], value: T) => (list.includes(value) ? list.filter((v) => v !== value) : [...list, value]);

  return (
    <Modal open title="Nouvelle exécution" onClose={onClose} wide>
      <div className="space-y-5">
        <Field label="Nom">
          <input className={inputClass} value={name} onChange={(e) => setName(e.target.value)} />
        </Field>

        <div>
          <div className="mb-2 text-xs font-medium uppercase tracking-wide text-stone-500">Modèles</div>
          <div className="grid gap-3 sm:grid-cols-2">
            {Object.entries(byProvider).map(([provider, list]) => (
              <div key={provider} className="rounded-lg border border-stone-200 p-3 dark:border-neutral-800">
                <div className="mb-1.5 text-sm font-medium capitalize">{provider}</div>
                {list.map((m) => (
                  <label key={m.key} className={`flex items-center gap-2 py-0.5 text-sm ${m.available ? "" : "opacity-50"}`}>
                    <input
                      type="checkbox"
                      disabled={!m.available}
                      checked={selected.includes(m.key)}
                      onChange={() => setSelected((s) => toggle(s, m.key))}
                    />
                    {m.label}
                    {m.variant !== "base" && <Badge tone="violet">{VARIANT_LABEL[m.variant]}</Badge>}
                    {m.public_only && <Badge tone="amber">gratuit · tests publics</Badge>}
                    {!m.available && <span className="text-xs text-stone-500">(indisponible)</span>}
                  </label>
                ))}
              </div>
            ))}
          </div>
          <p className="mt-2 text-xs text-stone-500">
            Un modèle est indisponible si sa clé API manque dans <code>.env</code> ou si Ollama ne répond pas.
            Les offres gratuites peuvent réutiliser les requêtes : elles ne reçoivent que les tests publics.
          </p>
        </div>

        <div>
          <div className="mb-2 text-xs font-medium uppercase tracking-wide text-stone-500">Catégories</div>
          <div className="flex flex-wrap gap-x-4 gap-y-1">
            {CATEGORIES.map((c) => (
              <label key={c.id} className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={categories.includes(c.id)} onChange={() => setCategories((s) => toggle(s, c.id))} />
                {c.label}
              </label>
            ))}
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-3">
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={testMode} onChange={(e) => setTestMode(e.target.checked)} />
            Mode test (limite les coûts)
          </label>
          <Field label="Questions par catégorie">
            <input type="number" min={1} className={inputClass} value={sample} disabled={!testMode} onChange={(e) => setSample(Number(e.target.value))} />
          </Field>
          <Field label="Partie du jeu">
            <select className={inputClass} value={split} disabled={publicOnly} onChange={(e) => setSplit(e.target.value)}>
              <option value="">Publique + privée</option>
              <option value="public">Publique</option>
              <option value="private">Privée</option>
            </select>
          </Field>
        </div>

        {estimate && (
          <Alert tone="teal">
            <strong>{estimate.calls}</strong> appel(s) · {estimate.items} test(s) ·{" "}
            {estimate.cost_usd_known_models !== null
              ? `coût estimé ≈ ${estimate.cost_usd_known_models.toFixed(3)} $`
              : "coût non estimable (prix inconnus)"}
            <div className="mt-0.5 text-xs opacity-80">{estimate.note}</div>
          </Alert>
        )}
        {error && <Alert>{error}</Alert>}

        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose}>
            Annuler
          </Button>
          <Button variant="primary" onClick={launch} disabled={!selected.length || !categories.length || !estimate?.calls}>
            Lancer
          </Button>
        </div>
      </div>
    </Modal>
  );
}

function RunDetail({ run, onClose }: { run: Run; onClose: () => void }) {
  const responses = useApi<RunResponse[]>(`/api/runs/${run.id}/responses`);
  return (
    <Modal open title={`${run.name} · réponses`} onClose={onClose} wide>
      {!responses.data ? (
        <Spinner />
      ) : (
        <div className="max-h-[70vh] overflow-auto">
          <table className="w-full text-left text-sm">
            <thead className="sticky top-0 bg-white text-xs uppercase text-stone-500 dark:bg-neutral-900">
              <tr>
                <th className="py-2 pr-3">Test</th>
                <th className="py-2 pr-3">Modèle</th>
                <th className="py-2 pr-3">Réponse</th>
                <th className="py-2 pr-3 text-right">chrF++</th>
              </tr>
            </thead>
            <tbody>
              {responses.data.map((r) => (
                <tr key={r.id} className="border-t border-stone-100 align-top dark:border-neutral-800">
                  <td className="py-2 pr-3 font-mono text-xs">{r.item_id}</td>
                  <td className="py-2 pr-3 whitespace-nowrap">{r.model_key}</td>
                  <td className="kab py-2 pr-3">
                    {r.status === "error" ? <span className="text-red-600">{r.error}</span> : r.status === "pending" ? <span className="text-stone-400">en attente</span> : r.output}
                  </td>
                  <td className="py-2 pr-3 text-right tabular-nums">{r.chrf ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Modal>
  );
}
