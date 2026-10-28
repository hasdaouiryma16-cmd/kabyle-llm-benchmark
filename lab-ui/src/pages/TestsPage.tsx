import { useRef, useState } from "react";
import { ItemEditor } from "../components/ItemEditor";
import { Alert, Badge, Button, Card, Empty, inlineInputClass, PageHeader, Spinner, useToast } from "../components/ui";
import { api, ApiError, qs, useApi } from "../lib/api";
import { CATEGORIES, categoryLabel, type ImportReport, type Item, type TestsetStatus } from "../lib/types";

export function TestsPage() {
  const [filters, setFilters] = useState({ category: "", status: "", split: "", q: "" });
  const items = useApi<Item[]>(`/api/tests${qs(filters)}`);
  const status = useApi<TestsetStatus>("/api/testset/status");
  const [editing, setEditing] = useState<{ item: Item | null; key: number } | null>(null);
  const [report, setReport] = useState<ImportReport | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const notify = useToast();

  const refresh = () => {
    items.reload();
    status.reload();
  };

  async function importFile(file: File) {
    const form = new FormData();
    form.append("file", file);
    try {
      const r = await api.post<ImportReport>("/api/testset/import", form);
      setReport(null);
      notify(`Import : ${r.created} créé(s), ${r.updated} mis à jour`);
      refresh();
    } catch (e) {
      if (e instanceof ApiError && e.detail && typeof e.detail === "object" && "errors" in e.detail)
        setReport(e.detail as ImportReport);
      else notify(String((e as Error).message), "error");
    }
  }

  async function saveToRepo() {
    const version = prompt(
      "Version du jeu de test (ex. 1.1.0). Laisser vide pour conserver la version actuelle.",
      status.data?.manifest?.version ?? "1.0.0",
    );
    if (version === null) return;
    try {
      await api.post("/api/testset/save-to-repo", version.trim() ? { version: version.trim() } : undefined);
      notify("Jeu de test enregistré dans data/test/ (pensez à commiter)");
      status.reload();
    } catch (e) {
      notify((e as Error).message, "error");
    }
  }

  async function loadFromRepo() {
    if (!confirm("Recharger depuis le dépôt ? Les tests du dépôt remplacent ceux de même identifiant.")) return;
    try {
      const r = await api.post<ImportReport>("/api/testset/load-from-repo");
      notify(`Rechargé : ${r.created} créé(s), ${r.updated} mis à jour`);
      refresh();
    } catch (e) {
      notify((e as Error).message, "error");
    }
  }

  const s = status.data;
  return (
    <div>
      <PageHeader
        title="Jeu de tests"
        subtitle="Les références en kabyle sont saisies uniquement par l'autrice. Le fichier JSONL du dépôt est la source de vérité."
        actions={
          <>
            <Button onClick={() => fileRef.current?.click()}>Importer</Button>
            <input
              ref={fileRef}
              type="file"
              accept=".json,.jsonl,.csv"
              hidden
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) importFile(f);
                e.target.value = "";
              }}
            />
            <ExportMenu />
            <Button variant="primary" onClick={() => setEditing({ item: null, key: Date.now() })}>
              + Nouveau test
            </Button>
          </>
        }
      />

      {s && (
        <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Stat label="Tests" value={s.items} detail={`${s.ready} prêts · ${s.by_status.draft ?? 0} brouillons`} />
          <Stat
            label="Partie privée"
            value={`${s.items ? Math.round(((s.by_split.private ?? 0) / s.items) * 100) : 0} %`}
            detail={`${s.by_split.private ?? 0} tests · objectif ≈ 20 %`}
          />
          <Stat label="Version" value={s.manifest?.version ?? "—"} detail={`empreinte ${s.content_hash.slice(0, 10)}…`} />
          <Card className="flex flex-col justify-between gap-2">
            <div className="flex items-center gap-2 text-sm">
              {s.repo_in_sync ? (
                <Badge tone="green">Synchronisé avec le dépôt</Badge>
              ) : s.items === 0 && !s.manifest ? (
                <Badge>Rien à enregistrer pour l'instant</Badge>
              ) : (
                <Badge tone="amber">Modifications non enregistrées</Badge>
              )}
            </div>
            <div className="flex gap-2">
              <Button size="sm" variant="primary" onClick={saveToRepo}>
                Enregistrer dans le dépôt
              </Button>
              <Button size="sm" onClick={loadFromRepo}>
                Recharger
              </Button>
            </div>
          </Card>
        </div>
      )}

      {report && (
        <div className="mb-4">
          <Alert>
            <p className="font-medium">Import refusé : {report.errors.length} ligne(s) invalide(s). Rien n'a été écrit.</p>
            <ul className="mt-1 max-h-48 list-disc overflow-y-auto pl-5">
              {report.errors.map((e) => (
                <li key={e.row}>
                  Ligne {e.row}
                  {e.id ? ` (${e.id})` : ""} : {e.errors.join(" ; ")}
                </li>
              ))}
            </ul>
          </Alert>
        </div>
      )}

      <div className="mb-3 flex flex-wrap gap-2">
        <input
          className={`${inlineInputClass} min-w-64`}
          placeholder="Rechercher…"
          value={filters.q}
          onChange={(e) => setFilters({ ...filters, q: e.target.value })}
        />
        <select className={inlineInputClass} value={filters.category} onChange={(e) => setFilters({ ...filters, category: e.target.value })}>
          <option value="">Toutes les catégories</option>
          {CATEGORIES.map((c) => (
            <option key={c.id} value={c.id}>
              {c.label}
            </option>
          ))}
        </select>
        <select className={inlineInputClass} value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
          <option value="">Tous les statuts</option>
          <option value="ready">Prêts</option>
          <option value="draft">Brouillons</option>
        </select>
        <select className={inlineInputClass} value={filters.split} onChange={(e) => setFilters({ ...filters, split: e.target.value })}>
          <option value="">Public + privé</option>
          <option value="public">Public</option>
          <option value="private">Privé</option>
        </select>
      </div>

      {items.loading && !items.data ? (
        <Spinner />
      ) : items.error ? (
        <Alert>{items.error}</Alert>
      ) : !items.data?.length ? (
        <Empty>Aucun test pour l'instant. Utilisez le mode guidé ou « Nouveau test ».</Empty>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-stone-200 bg-white dark:border-neutral-800 dark:bg-neutral-900">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-stone-200 text-xs uppercase tracking-wide text-stone-500 dark:border-neutral-800">
              <tr>
                <th className="px-4 py-2.5">Id</th>
                <th className="px-4 py-2.5">Catégorie</th>
                <th className="px-4 py-2.5">Consigne</th>
                <th className="px-4 py-2.5 text-right">Réf.</th>
                <th className="px-4 py-2.5">Statut</th>
              </tr>
            </thead>
            <tbody>
              {items.data.map((item) => (
                <tr
                  key={item.id}
                  onClick={() => setEditing({ item, key: Date.now() })}
                  className="cursor-pointer border-b border-stone-100 last:border-0 hover:bg-stone-50 dark:border-neutral-800 dark:hover:bg-neutral-800/50"
                >
                  <td className="whitespace-nowrap px-4 py-2.5 font-mono text-xs">{item.id}</td>
                  <td className="whitespace-nowrap px-4 py-2.5">{categoryLabel(item.category)}</td>
                  <td className="kab max-w-xl truncate px-4 py-2.5">{item.prompt}</td>
                  <td className="px-4 py-2.5 text-right tabular-nums">{item.references.length}</td>
                  <td className="space-x-1 whitespace-nowrap px-4 py-2.5">
                    <Badge tone={item.status === "ready" ? "teal" : "neutral"}>{item.status === "ready" ? "prêt" : "brouillon"}</Badge>
                    {item.split === "private" && <Badge tone="violet">privé</Badge>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {editing && (
        <ItemEditor
          key={editing.key}
          item={editing.item}
          open
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            refresh();
          }}
        />
      )}
    </div>
  );
}

function ExportMenu() {
  return (
    <div className="flex overflow-hidden rounded-md border border-stone-300 text-sm dark:border-neutral-700">
      <span className="bg-stone-100 px-3 py-2 text-stone-600 dark:bg-neutral-800 dark:text-stone-300">Exporter</span>
      {(["jsonl", "json", "csv"] as const).map((f) => (
        <a
          key={f}
          href={`/api/testset/export?format=${f}`}
          className="border-l border-stone-300 bg-white px-3 py-2 font-medium uppercase hover:bg-stone-100 dark:border-neutral-700 dark:bg-neutral-900 dark:hover:bg-neutral-800"
        >
          {f}
        </a>
      ))}
    </div>
  );
}

export function Stat({ label, value, detail }: { label: string; value: string | number; detail?: string }) {
  return (
    <Card>
      <div className="text-xs font-medium uppercase tracking-wide text-stone-500 dark:text-stone-400">{label}</div>
      <div className="mt-1 text-2xl font-semibold">{value}</div>
      {detail && <div className="mt-0.5 text-xs text-stone-500 dark:text-stone-400">{detail}</div>}
    </Card>
  );
}
