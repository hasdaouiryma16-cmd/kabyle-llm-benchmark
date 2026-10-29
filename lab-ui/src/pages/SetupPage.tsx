import { Alert, Badge, Button, Card, PageHeader, Spinner } from "../components/ui";
import { useApi } from "../lib/api";
import type { SetupCheck, SetupStatus } from "../lib/types";

// Chaque état a une icône et un libellé : jamais la couleur seule
const STATES: Record<SetupCheck["state"], { icon: string; label: string; tone: "green" | "red" | "amber" | "neutral" }> = {
  ok: { icon: "✓", label: "Prêt", tone: "green" },
  todo: { icon: "✗", label: "À faire", tone: "red" },
  warn: { icon: "!", label: "À vérifier", tone: "amber" },
  optional: { icon: "○", label: "Facultatif", tone: "neutral" },
};

export function SetupPage() {
  const { data, error, loading, reload } = useApi<SetupStatus>("/api/setup");
  return (
    <div>
      <PageHeader
        title="Préparation"
        subtitle="Ce qui est prêt et ce qui reste à faire avant de lancer un benchmark. Rien n'est modifié ici."
        actions={
          <Button onClick={reload} disabled={loading}>
            Revérifier
          </Button>
        }
      />
      {error ? (
        <Alert>{error}</Alert>
      ) : !data ? (
        <Spinner />
      ) : (
        <div className="space-y-6">
          {!data.can_run_api_benchmark && (
            <Alert tone="amber">Aucune clé d'API n'est configurée : seuls les modèles locaux (Ollama) peuvent être lancés.</Alert>
          )}
          {data.groups.map((group) => (
            <Card key={group.id} className="p-0">
              <h2 className="border-b border-stone-200 px-4 py-3 text-sm font-semibold dark:border-neutral-800">{group.title}</h2>
              <ul className="divide-y divide-stone-100 dark:divide-neutral-800">
                {group.checks.map((check) => {
                  const s = STATES[check.state];
                  return (
                    <li key={check.id} className="flex flex-col gap-1 px-4 py-3 sm:flex-row sm:items-start sm:gap-4">
                      <div className="w-28 shrink-0">
                        <Badge tone={s.tone}>
                          <span aria-hidden="true" className="mr-1">
                            {s.icon}
                          </span>
                          {s.label}
                        </Badge>
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="text-sm font-medium">{check.label}</div>
                        <div className="text-sm text-stone-600 dark:text-stone-400">{check.detail}</div>
                        {check.hint && <div className="mt-1 text-sm text-teal-800 dark:text-teal-300">→ {check.hint}</div>}
                        {check.command && (
                          <pre className="mt-1 whitespace-pre-wrap break-words rounded bg-stone-100 px-2 py-1 font-mono text-xs text-stone-700 dark:bg-neutral-800 dark:text-stone-300">
                            {check.command}
                          </pre>
                        )}
                      </div>
                    </li>
                  );
                })}
              </ul>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
