import { useEffect, useMemo, useState } from "react";

export interface ExplorerItem {
  id: string;
  category: string;
  prompt: string;
  source_text: string | null;
  context: string | null;
  references: string[];
  answers: { model_key: string; output: string | null; score: number | null }[];
}

export interface ExplorerModel {
  key: string;
  family: string;
  method: string;
  methodLabel: string;
  color: string;
}

export interface ExplorerText {
  pickCategory: string;
  allCategories: string;
  pickTest: string;
  search: string;
  sortBy: string;
  sortScore: string;
  sortModel: string;
  context: string;
  prompt: string;
  source: string;
  references: string;
  answer: string;
  noAnswer: string;
  score: string;
  showMore: string;
  showLess: string;
  scoreScale: string[];
}

/** Affiche le gras Markdown (**…**) des modèles sans interpréter de HTML. */
function Rich({ text }: { text: string }) {
  const parts = text.split(/\*\*(.+?)\*\*/gs);
  return <>{parts.map((p, i) => (i % 2 === 1 ? <strong key={i}>{p}</strong> : p))}</>;
}

function Pips({ score }: { score: number | null }) {
  return (
    <span className="pips" aria-hidden="true">
      {[1, 2, 3].map((n) => (
        <i key={n} className={score !== null && score >= n ? "on" : ""} />
      ))}
    </span>
  );
}

function Answer({ text, model, score, output }: { text: ExplorerText; model?: ExplorerModel; score: number | null; output: string | null }) {
  const long = (output ?? "").length > 360;
  const [open, setOpen] = useState(false);
  return (
    <div className="ans">
      <div className="ans-model">
        <strong>{model?.family ?? "?"}</strong>
        <span className="method-tag" style={{ ["--c" as string]: model?.color }}>
          {model?.methodLabel}
        </span>
        <div className="grade">
          <Pips score={score} />
          <span>
            {score ?? "—"}/3 · {score !== null ? text.scoreScale[score] : ""}
          </span>
        </div>
      </div>
      <div>
        <div className={`ans-out kab${long && !open ? " clamp" : ""}`}>{output?.trim() ? <Rich text={output.trim()} /> : text.noAnswer}</div>
        {long && (
          <button type="button" className="more" onClick={() => setOpen((o) => !o)} aria-expanded={open}>
            {open ? text.showLess : text.showMore}
          </button>
        )}
      </div>
    </div>
  );
}

export default function AnswerExplorer({
  items,
  models,
  categories,
  text,
}: {
  items: ExplorerItem[];
  models: ExplorerModel[];
  categories: { id: string; label: string }[];
  text: ExplorerText;
}) {
  const [category, setCategory] = useState("all");
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(items[0]?.id ?? "");
  const [sort, setSort] = useState<"score" | "model">("score");

  // Un lien direct (#comp-0001) ouvre ce test
  useEffect(() => {
    const id = decodeURIComponent(location.hash.slice(1));
    if (items.some((i) => i.id === id)) setSelected(id);
  }, [items]);

  const catLabel = (id: string) => categories.find((c) => c.id === id)?.label ?? id;
  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    return items.filter(
      (i) =>
        (category === "all" || i.category === category) &&
        (!q || [i.prompt, i.source_text ?? "", i.context ?? "", ...i.references].some((s) => s.toLowerCase().includes(q))),
    );
  }, [items, category, query]);

  const item = items.find((i) => i.id === selected) ?? visible[0];
  const modelOf = (key: string) => models.find((m) => m.key === key);
  const order = models.map((m) => m.key);
  const answers = item
    ? [...item.answers].sort((a, b) =>
        sort === "score" ? (b.score ?? -1) - (a.score ?? -1) || order.indexOf(a.model_key) - order.indexOf(b.model_key) : order.indexOf(a.model_key) - order.indexOf(b.model_key),
      )
    : [];

  const pick = (id: string) => {
    setSelected(id);
    history.replaceState(null, "", `#${id}`);
  };

  return (
    <div className="explorer">
      <aside className="ex-side">
        <label className="field">
          {text.pickCategory}
          <select value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="all">{text.allCategories}</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.label}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span className="sr-only">{text.search}</span>
          <input type="search" placeholder={text.search} value={query} onChange={(e) => setQuery(e.target.value)} />
        </label>
        <ul className="ex-list" aria-label={text.pickTest}>
          {visible.map((i) => (
            <li key={i.id}>
              <button type="button" aria-current={item?.id === i.id} onClick={() => pick(i.id)}>
                <small>
                  {catLabel(i.category)} · {i.id}
                </small>
                <span className="kab">{(i.source_text ?? i.prompt).slice(0, 70)}</span>
              </button>
            </li>
          ))}
        </ul>
      </aside>

      {item && (
        <div className="ex-item">
          <div className="card ex-q">
            <dl>
              <div>
                <dt>
                  {catLabel(item.category)} · {item.id}
                </dt>
              </div>
              {item.context && (
                <div>
                  <dt>{text.context}</dt>
                  <dd className="kab">{item.context}</dd>
                </div>
              )}
              <div>
                <dt>{text.prompt}</dt>
                <dd className="kab">{item.prompt}</dd>
              </div>
              {item.source_text && (
                <div>
                  <dt>{text.source}</dt>
                  <dd className="kab">{item.source_text}</dd>
                </div>
              )}
              {item.references.length > 0 && (
                <div>
                  <dt>{text.references}</dt>
                  <dd className="kab ref">{item.references.join(" · ")}</dd>
                </div>
              )}
            </dl>
          </div>
          <div className="card" style={{ padding: 0 }}>
            <div className="ans-head" style={{ padding: "14px 18px", borderBottom: "1px solid var(--line)" }}>
              <strong>
                {answers.length} {text.answer.toLowerCase()}s
              </strong>
              <div className="seg" style={{ margin: 0 }} role="group" aria-label={text.sortBy}>
                <button type="button" aria-pressed={sort === "score"} onClick={() => setSort("score")}>
                  {text.sortBy} {text.sortScore}
                </button>
                <button type="button" aria-pressed={sort === "model"} onClick={() => setSort("model")}>
                  {text.sortBy} {text.sortModel}
                </button>
              </div>
            </div>
            {answers.map((a) => (
              <Answer key={a.model_key} text={text} model={modelOf(a.model_key)} score={a.score} output={a.output} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
