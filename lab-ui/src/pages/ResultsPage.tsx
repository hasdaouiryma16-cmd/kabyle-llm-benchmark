import { useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Alert, Badge, Button, Card, Empty, inlineInputClass, PageHeader, Spinner, useToast } from "../components/ui";
import { api, qs, useApi } from "../lib/api";
import { seriesColor, useDarkMode } from "../lib/palette";
import { categoryLabel, type ModelInfo, type ModelResult, type ResponseRow, type Results } from "../lib/types";

const VARIANT_LABEL: Record<string, string> = { fewshot: "few-shot", rag: "RAG", finetuned: "fine-tuné" };
const fmt = (v: number | null | undefined, unit = "") => (v === null || v === undefined ? "—" : `${v}${unit}`);

function ChartFrame({ title, children, caption }: { title: string; children: React.ReactNode; caption?: string }) {
  return (
    <Card>
      <h3 className="mb-3 font-medium">{title}</h3>
      {children}
      {caption && <p className="mt-2 text-xs text-stone-500">{caption}</p>}
    </Card>
  );
}

const axisProps = {
  stroke: "var(--chart-axis)",
  tick: { fill: "var(--chart-axis)", fontSize: 12 },
  tickLine: false,
};

export function ResultsPage() {
  const testSets = useApi<{ test_set_hash: string; version: string | null; runs: number }[]>("/api/results/test-sets");
  const models = useApi<ModelInfo[]>("/api/models");
  const [hash, setHash] = useState("");
  const [split, setSplit] = useState("");
  const results = useApi<Results>(`/api/results${qs({ test_set_hash: hash, split })}`);
  const dark = useDarkMode();
  const notify = useToast();

  // Couleur stable par modèle : son rang dans la configuration, jamais son classement
  const colorOf = useMemo(() => {
    const order = (models.data ?? []).map((m) => m.key);
    return (key: string) => seriesColor(order.indexOf(key), dark);
  }, [models.data, dark]);

  async function exportPublic() {
    try {
      const r = await api.post<{ models: number; examples: number }>("/api/results/export-public");
      notify(`Exporté : ${r.models} modèle(s), ${r.examples} exemple(s) → data/results/public/results.json`);
    } catch (e) {
      notify((e as Error).message, "error");
    }
  }

  const data = results.data;
  const ranked = data?.models.filter((m) => m.overall.n_graded > 0) ?? [];
  return (
    <div>
      <PageHeader
        title="Résultats"
        subtitle="Note humaine (0–3, ramenée en %) avec intervalle de confiance à 95 %, chrF++ et taux de réponses dans la bonne langue."
        actions={
          <>
            <select className={inlineInputClass} value={hash} onChange={(e) => setHash(e.target.value)}>
              <option value="">Dernier jeu de test</option>
              {testSets.data?.map((t) => (
                <option key={t.test_set_hash} value={t.test_set_hash}>
                  {t.version ?? "non versionné"} · {t.test_set_hash.slice(0, 8)} ({t.runs} run{t.runs > 1 ? "s" : ""})
                </option>
              ))}
            </select>
            <select className={inlineInputClass} value={split} onChange={(e) => setSplit(e.target.value)}>
              <option value="">Public + privé</option>
              <option value="public">Public</option>
              <option value="private">Privé</option>
            </select>
            <Button variant="primary" onClick={exportPublic}>
              Exporter vers le site public
            </Button>
          </>
        }
      />

      {results.loading && !data ? (
        <Spinner />
      ) : results.error ? (
        <Alert>{results.error}</Alert>
      ) : !data?.models.length ? (
        <Empty>Aucun résultat : lancez une exécution puis notez les réponses.</Empty>
      ) : (
        <div className="space-y-6">
          <Leaderboard models={data.models} colorOf={colorOf} />
          {ranked.length > 0 && <CategoryChart results={data} models={ranked} colorOf={colorOf} />}
          {data.gains.length > 0 && <Gains results={data} colorOf={colorOf} />}
          {ranked.some((m) => Object.keys(m.error_tags).length) && <ErrorTags results={data} />}
          <Explorer hash={data.test_set_hash} models={data.models} />
        </div>
      )}
    </div>
  );
}

function Leaderboard({ models, colorOf }: { models: ModelResult[]; colorOf: (k: string) => string }) {
  return (
    <Card className="overflow-x-auto p-0">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-stone-200 text-xs uppercase tracking-wide text-stone-500 dark:border-neutral-800">
          <tr>
            <th className="px-4 py-3">#</th>
            <th className="px-4 py-3">Modèle</th>
            <th className="px-4 py-3 text-right">Note humaine</th>
            <th className="px-4 py-3 text-right">IC 95 %</th>
            <th className="px-4 py-3 text-right">Moyenne /3</th>
            <th className="px-4 py-3 text-right">Notées</th>
            <th className="px-4 py-3 text-right">chrF++</th>
            <th className="px-4 py-3 text-right">Bonne langue</th>
          </tr>
        </thead>
        <tbody className="tabular-nums">
          {models.map((m, i) => (
            <tr key={m.key} className="border-b border-stone-100 last:border-0 dark:border-neutral-800">
              <td className="px-4 py-3 text-stone-500">{m.overall.human_pct === null ? "—" : i + 1}</td>
              <td className="px-4 py-3">
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ background: colorOf(m.key) }} />
                  <span className="font-medium">{m.label}</span>
                  {m.variant !== "base" && <Badge tone="violet">{VARIANT_LABEL[m.variant] ?? m.variant}</Badge>}
                </div>
              </td>
              <td className="px-4 py-3 text-right font-semibold">{fmt(m.overall.human_pct, " %")}</td>
              <td className="px-4 py-3 text-right text-stone-500">
                {m.overall.human_pct_ci95 ? `${m.overall.human_pct_ci95[0]}–${m.overall.human_pct_ci95[1]}` : "—"}
              </td>
              <td className="px-4 py-3 text-right">{fmt(m.overall.human_mean)}</td>
              <td className="px-4 py-3 text-right text-stone-500">
                {m.overall.n_graded}/{m.overall.n}
              </td>
              <td className="px-4 py-3 text-right">{fmt(m.overall.chrf)}</td>
              <td className="px-4 py-3 text-right">
                {fmt(m.overall.lang_ok_rate, " %")}
                <span className="ml-1 text-xs text-stone-400">({m.overall.n_lang_checked})</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}

function CategoryChart({ results, models, colorOf }: { results: Results; models: ModelResult[]; colorOf: (k: string) => string }) {
  const shown = models.slice(0, 8); // au-delà, la palette ne garantit plus la distinction des couleurs
  const rows = results.categories
    .map((c) => ({
      category: categoryLabel(c.id),
      ...Object.fromEntries(shown.map((m) => [m.key, m.by_category[c.id]?.human_pct ?? null])),
    }))
    .filter((row) => shown.some((m) => row[m.key as keyof typeof row] !== null));
  return (
    <ChartFrame
      title="Note humaine par catégorie (%)"
      caption={models.length > 8 ? `8 premiers modèles affichés sur ${models.length}.` : undefined}
    >
      <ResponsiveContainer width="100%" height={340}>
        <BarChart data={rows} barGap={2} barCategoryGap="22%">
          <CartesianGrid vertical={false} stroke="var(--chart-grid)" />
          <XAxis dataKey="category" {...axisProps} />
          <YAxis domain={[0, 100]} unit=" %" {...axisProps} axisLine={false} width={52} />
          <Tooltip
            cursor={{ fill: "var(--chart-grid)", opacity: 0.4 }}
            contentStyle={{ background: "var(--chart-surface)", border: "1px solid var(--chart-grid)", color: "var(--chart-ink)", borderRadius: 8 }}
            formatter={(v, key) => [
              v === null || v === undefined ? "—" : `${v} %`,
              models.find((m) => m.key === key)?.label ?? String(key),
            ]}
          />
          <Legend formatter={(key: string) => models.find((m) => m.key === key)?.label ?? key} wrapperStyle={{ fontSize: 12 }} />
          {shown.map((m) => (
            <Bar key={m.key} dataKey={m.key} fill={colorOf(m.key)} radius={[4, 4, 0, 0]} maxBarSize={28} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}

function Gains({ results, colorOf }: { results: Results; colorOf: (k: string) => string }) {
  const labelOf = (key: string) => results.models.find((m) => m.key === key)?.label ?? key;
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {results.gains.map((g) => {
        const rows = Object.entries(g.by_category)
          .filter(([, v]) => v.before_pct !== undefined)
          .map(([cat, v]) => ({ category: categoryLabel(cat), avant: v.before_pct, après: v.after_pct, n: v.n_paired }));
        const o = g.overall;
        return (
          <ChartFrame
            key={g.variant}
            title={`${g.variant_label} vs ${labelOf(g.base)}`}
            caption={`Comparaison appariée sur ${o.n_paired} test(s) notés pour les deux modèles.`}
          >
            {o.gain_points !== undefined ? (
              <p className="mb-3 text-sm">
                <span className={`text-2xl font-semibold ${o.gain_points >= 0 ? "text-green-700 dark:text-green-500" : "text-red-700 dark:text-red-400"}`}>
                  {o.gain_points >= 0 ? "▲ +" : "▼ "}
                  {o.gain_points} pts
                </span>{" "}
                <span className="text-stone-500">
                  ({o.before_pct} % → {o.after_pct} %
                  {o.gain_relative_pct !== null && o.gain_relative_pct !== undefined && `, ${o.gain_relative_pct > 0 ? "+" : ""}${o.gain_relative_pct} % relatif`}
                  {o.gain_points_ci95 && `, IC 95 % ${o.gain_points_ci95[0]} à ${o.gain_points_ci95[1]}`})
                </span>
              </p>
            ) : (
              <p className="mb-3 text-sm text-stone-500">Pas encore de test noté pour les deux modèles.</p>
            )}
            {rows.length > 0 && (
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={rows} barGap={2}>
                  <CartesianGrid vertical={false} stroke="var(--chart-grid)" />
                  <XAxis dataKey="category" {...axisProps} interval={0} fontSize={11} />
                  <YAxis domain={[0, 100]} unit=" %" {...axisProps} axisLine={false} width={52} />
                  <Tooltip contentStyle={{ background: "var(--chart-surface)", border: "1px solid var(--chart-grid)", color: "var(--chart-ink)", borderRadius: 8 }} />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Bar dataKey="avant" name={labelOf(g.base)} fill={colorOf(g.base)} radius={[4, 4, 0, 0]} maxBarSize={28} />
                  <Bar dataKey="après" name={g.variant_label} fill={colorOf(g.variant)} radius={[4, 4, 0, 0]} maxBarSize={28} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </ChartFrame>
        );
      })}
    </div>
  );
}

function ErrorTags({ results }: { results: Results }) {
  const graded = results.models.filter((m) => Object.keys(m.error_tags).length);
  const [key, setKey] = useState(graded[0]?.key ?? "");
  const model = graded.find((m) => m.key === key) ?? graded[0];
  const rows = Object.entries(model.error_tags).map(([tag, n]) => ({ tag: results.error_tags[tag] ?? tag, n }));
  return (
    <ChartFrame title="Analyse des erreurs" caption="Nombre de réponses portant chaque étiquette (une réponse peut en avoir plusieurs).">
      <select className={`${inlineInputClass} mb-3`} value={model.key} onChange={(e) => setKey(e.target.value)}>
        {graded.map((m) => (
          <option key={m.key} value={m.key}>
            {m.label}
          </option>
        ))}
      </select>
      <ResponsiveContainer width="100%" height={Math.max(160, rows.length * 34)}>
        <BarChart data={rows} layout="vertical" margin={{ left: 24 }}>
          <CartesianGrid horizontal={false} stroke="var(--chart-grid)" />
          <XAxis type="number" allowDecimals={false} {...axisProps} />
          <YAxis type="category" dataKey="tag" width={230} {...axisProps} axisLine={false} />
          <Tooltip contentStyle={{ background: "var(--chart-surface)", border: "1px solid var(--chart-grid)", color: "var(--chart-ink)", borderRadius: 8 }} />
          <Bar dataKey="n" name="Réponses" fill="#2a78d6" radius={[0, 4, 4, 0]} maxBarSize={20} />
        </BarChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}

function Explorer({ hash, models }: { hash: string | null; models: ModelResult[] }) {
  const [model, setModel] = useState("");
  const [favoritesOnly, setFavoritesOnly] = useState(false);
  const rows = useApi<ResponseRow[]>(
    `/api/results/responses${qs({ test_set_hash: hash, model_key: model, favorites_only: favoritesOnly || null, graded_only: true })}`,
  );
  const notify = useToast();

  async function favorite(row: ResponseRow, kind: "success" | "error" | null) {
    if (kind === null) await api.del(`/api/favorites/${row.response_id}`);
    else {
      const note = prompt("Note pour cet exemple (facultatif)", row.favorite?.note ?? "") ?? "";
      await api.put(`/api/favorites/${row.response_id}`, { kind, note });
    }
    notify(kind ? "Ajouté aux exemples marquants" : "Retiré des exemples");
    rows.reload();
  }

  return (
    <Card>
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <h3 className="mr-auto font-medium">Réponses notées · exemples marquants</h3>
        <select className={inlineInputClass} value={model} onChange={(e) => setModel(e.target.value)}>
          <option value="">Tous les modèles</option>
          {models.map((m) => (
            <option key={m.key} value={m.key}>
              {m.label}
            </option>
          ))}
        </select>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={favoritesOnly} onChange={(e) => setFavoritesOnly(e.target.checked)} />
          Favoris uniquement
        </label>
      </div>
      {!rows.data?.length ? (
        <p className="text-sm text-stone-500">Aucune réponse notée pour cette sélection.</p>
      ) : (
        <div className="max-h-[36rem] space-y-2 overflow-y-auto">
          {rows.data.map((r) => (
            <div key={r.response_id} className="rounded-lg border border-stone-200 p-3 text-sm dark:border-neutral-800">
              <div className="mb-1 flex flex-wrap items-center gap-2">
                <span className="font-medium">{r.model_label}</span>
                <Badge>{categoryLabel(r.item.category)}</Badge>
                <Badge tone={r.score === 3 ? "green" : r.score === 0 ? "red" : "amber"}>note {r.score}/3</Badge>
                {r.item.split === "private" && <Badge tone="violet">privé (jamais publié)</Badge>}
                {r.error_tags.map((t) => (
                  <Badge key={t} tone="red">
                    {t}
                  </Badge>
                ))}
                <div className="ml-auto flex gap-1">
                  <Button size="sm" variant={r.favorite?.kind === "success" ? "primary" : "ghost"} onClick={() => favorite(r, r.favorite?.kind === "success" ? null : "success")} disabled={r.item.split === "private"}>
                    ★ Réussite
                  </Button>
                  <Button size="sm" variant={r.favorite?.kind === "error" ? "danger" : "ghost"} onClick={() => favorite(r, r.favorite?.kind === "error" ? null : "error")} disabled={r.item.split === "private"}>
                    ⚠ Erreur révélatrice
                  </Button>
                </div>
              </div>
              <div className="kab text-stone-600 dark:text-stone-400">{r.item.prompt}</div>
              <div className="kab mt-1">
                <span className="text-xs uppercase text-stone-500">Réponse : </span>
                {r.output}
              </div>
              {r.item.references.length > 0 && (
                <div className="kab text-stone-500">
                  <span className="text-xs uppercase">Référence : </span>
                  {r.item.references.join(" · ")}
                </div>
              )}
              {r.favorite?.note && <div className="mt-1 text-xs italic text-stone-500">Note : {r.favorite.note}</div>}
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
