import { useState } from "react";
import { api, ApiError } from "../lib/api";
import { CATEGORIES, type Item, type ItemFields } from "../lib/types";
import { CharBar } from "./CharBar";
import { Alert, Button, Field, inputClass, Modal, useToast } from "./ui";

export const EMPTY_ITEM: ItemFields = {
  category: "translation_fr_kab",
  subcategory: null,
  script: "latin",
  prompt: "",
  source_text: null,
  context: null,
  references: [""],
  grading: "auto+human",
  expected_lang: "kab",
  difficulty: 1,
  split: "public",
  status: "draft",
  source: "author",
  author: null,
  notes: "",
};

/** Mêmes règles que le backend (app/models.py, readiness_problems). */
export function readinessProblems(item: ItemFields): string[] {
  const problems: string[] = [];
  const refs = item.references.filter((r) => r.trim());
  if (item.grading !== "human" && refs.length === 0) problems.push("au moins une référence");
  if (item.category.startsWith("translation") && !item.source_text?.trim()) problems.push("le texte source");
  if (item.category === "comprehension" && !item.context?.trim()) problems.push("le texte de compréhension");
  return problems;
}

const toFields = (item: Item | null): ItemFields => {
  if (!item) return { ...EMPTY_ITEM, references: [""] };
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { id, created_at, updated_at, ...fields } = item;
  return { ...fields, references: fields.references.length ? fields.references : [""] };
};

export function ItemEditor({
  item,
  open,
  onClose,
  onSaved,
}: {
  item: Item | null;
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [form, setForm] = useState<ItemFields>(() => toFields(item));
  const [customId, setCustomId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const notify = useToast();
  const set = <K extends keyof ItemFields>(key: K, value: ItemFields[K]) => setForm((f) => ({ ...f, [key]: value }));
  const problems = readinessProblems(form);
  const kabyleInput = { spellCheck: false, lang: "kab", className: `${inputClass} kab` };

  async function save() {
    setSaving(true);
    setError(null);
    const payload = { ...form, references: form.references.filter((r) => r.trim()) };
    try {
      if (item) await api.put(`/api/tests/${item.id}`, payload);
      else await api.post("/api/tests", { ...payload, id: customId.trim() || undefined });
      notify(item ? "Test mis à jour" : "Test créé");
      onSaved();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  }

  async function remove() {
    if (!item || !confirm(`Supprimer définitivement le test ${item.id} ?`)) return;
    await api.del(`/api/tests/${item.id}`);
    notify("Test supprimé");
    onSaved();
  }

  return (
    <Modal open={open} title={item ? `Modifier ${item.id}` : "Nouveau test"} onClose={onClose} wide>
      <div className="space-y-4">
        <CharBar />
        <div className="grid gap-3 sm:grid-cols-4">
          <Field label="Catégorie">
            <select
              className={inputClass}
              value={form.category}
              onChange={(e) => {
                const category = e.target.value as ItemFields["category"];
                setForm((f) => ({
                  ...f,
                  category,
                  expected_lang: category === "translation_kab_fr" ? "fr" : f.expected_lang === "fr" ? "kab" : f.expected_lang,
                }));
              }}
            >
              {CATEGORIES.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.label}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Thème">
            <input className={inputClass} value={form.subcategory ?? ""} onChange={(e) => set("subcategory", e.target.value || null)} />
          </Field>
          <Field label="Écriture attendue">
            <select className={inputClass} value={form.script} onChange={(e) => set("script", e.target.value as ItemFields["script"])}>
              <option value="latin">Latin</option>
              <option value="tifinagh">Tifinagh</option>
            </select>
          </Field>
          <Field label="Langue attendue">
            <select className={inputClass} value={form.expected_lang} onChange={(e) => set("expected_lang", e.target.value)}>
              <option value="kab">Kabyle</option>
              <option value="fr">Français</option>
            </select>
          </Field>
        </div>

        <Field label="Consigne envoyée au modèle" hint="Envoyée telle quelle (précédée du texte de compréhension s'il y en a un).">
          <textarea rows={3} {...kabyleInput} value={form.prompt} onChange={(e) => set("prompt", e.target.value)} />
        </Field>
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Texte source" hint="Pour les traductions : le texte à traduire (sert aux métriques).">
            <textarea rows={2} {...kabyleInput} value={form.source_text ?? ""} onChange={(e) => set("source_text", e.target.value || null)} />
          </Field>
          <Field label="Texte de compréhension" hint="Uniquement pour la catégorie Compréhension.">
            <textarea rows={2} {...kabyleInput} value={form.context ?? ""} onChange={(e) => set("context", e.target.value || null)} />
          </Field>
        </div>

        <Field label="Réponses de référence" hint="Plusieurs variantes acceptables possibles (orthographe, tournures).">
          <div className="space-y-2">
            {form.references.map((ref, i) => (
              <div key={i} className="flex gap-2">
                <input
                  {...kabyleInput}
                  value={ref}
                  onChange={(e) => set("references", form.references.map((r, j) => (j === i ? e.target.value : r)))}
                />
                <Button
                  variant="ghost"
                  size="sm"
                  aria-label="Retirer cette référence"
                  onClick={() => set("references", form.references.filter((_, j) => j !== i))}
                  disabled={form.references.length === 1}
                >
                  ✕
                </Button>
              </div>
            ))}
            <Button size="sm" onClick={() => set("references", [...form.references, ""])}>
              + Ajouter une variante
            </Button>
          </div>
        </Field>

        <div className="grid gap-3 sm:grid-cols-5">
          <Field label="Notation">
            <select className={inputClass} value={form.grading} onChange={(e) => set("grading", e.target.value as ItemFields["grading"])}>
              <option value="auto+human">Auto + humaine</option>
              <option value="auto">Automatique</option>
              <option value="human">Humaine</option>
            </select>
          </Field>
          <Field label="Difficulté">
            <select className={inputClass} value={form.difficulty} onChange={(e) => set("difficulty", Number(e.target.value))}>
              <option value={1}>1 · facile</option>
              <option value={2}>2 · moyen</option>
              <option value={3}>3 · difficile</option>
            </select>
          </Field>
          <Field label="Partie">
            <select className={inputClass} value={form.split} onChange={(e) => set("split", e.target.value as ItemFields["split"])}>
              <option value="public">Publique</option>
              <option value="private">Privée</option>
            </select>
          </Field>
          <Field label="Statut">
            <select className={inputClass} value={form.status} onChange={(e) => set("status", e.target.value as ItemFields["status"])}>
              <option value="draft">Brouillon</option>
              <option value="ready">Prêt</option>
            </select>
          </Field>
          {!item && (
            <Field label="Identifiant" hint="Vide = automatique">
              <input className={inputClass} value={customId} onChange={(e) => setCustomId(e.target.value)} placeholder="auto" />
            </Field>
          )}
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Source">
            <input className={inputClass} value={form.source} onChange={(e) => set("source", e.target.value)} />
          </Field>
          <Field label="Notes">
            <input className={inputClass} value={form.notes} onChange={(e) => set("notes", e.target.value)} />
          </Field>
        </div>

        {form.status === "ready" && problems.length > 0 && (
          <Alert tone="amber">Pour passer en « Prêt », il manque : {problems.join(", ")}.</Alert>
        )}
        {error && <Alert>{error}</Alert>}

        <div className="flex justify-between gap-2 pt-2">
          <div>{item && <Button variant="danger" onClick={remove}>Supprimer</Button>}</div>
          <div className="flex gap-2">
            <Button variant="ghost" onClick={onClose}>
              Annuler
            </Button>
            <Button variant="primary" onClick={save} disabled={saving || !form.prompt.trim()}>
              Enregistrer
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  );
}
