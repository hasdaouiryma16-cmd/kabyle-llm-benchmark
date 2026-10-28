import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

/** Palette catégorielle validée (daltonisme) ; la couleur suit le modèle, pas son rang. */
const LIGHT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"];
const DARK = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"];

function useDark() {
  const [dark, setDark] = useState(false);
  useEffect(() => {
    const read = () => setDark(document.documentElement.dataset.theme === "dark");
    read();
    const observer = new MutationObserver(read);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    return () => observer.disconnect();
  }, []);
  return dark;
}

const axis = { stroke: "var(--muted)", tick: { fill: "var(--muted)", fontSize: 12 }, tickLine: false };
const tooltipStyle = {
  background: "var(--surface)",
  border: "1px solid var(--line)",
  borderRadius: 10,
  color: "var(--ink)",
  fontSize: 13,
};

export interface SeriesModel {
  key: string;
  label: string;
  colorIndex: number;
}

export function CategoryChart({
  rows,
  models,
  unit,
}: {
  rows: Record<string, string | number | null>[];
  models: SeriesModel[];
  unit: string;
}) {
  const dark = useDark();
  const [hidden, setHidden] = useState<string[]>([]);
  const color = (i: number) => (i < LIGHT.length ? (dark ? DARK : LIGHT)[i] : "#898781");
  return (
    <div>
      <div className="chips" role="group" aria-label="Modèles">
        {models.map((m) => (
          <button
            key={m.key}
            type="button"
            className={hidden.includes(m.key) ? "chip off" : "chip"}
            onClick={() => setHidden((h) => (h.includes(m.key) ? h.filter((k) => k !== m.key) : [...h, m.key]))}
            aria-pressed={!hidden.includes(m.key)}
          >
            <span className="dot" style={{ background: color(m.colorIndex) }} />
            {m.label}
          </button>
        ))}
      </div>
      <ResponsiveContainer width="100%" height={360}>
        <BarChart data={rows} barGap={2} barCategoryGap="20%">
          <CartesianGrid vertical={false} stroke="var(--line)" />
          <XAxis dataKey="category" {...axis} interval={0} />
          <YAxis domain={[0, 100]} unit={unit} {...axis} axisLine={false} width={48} />
          <Tooltip
            contentStyle={tooltipStyle}
            cursor={{ fill: "var(--line)", opacity: 0.35 }}
            formatter={(v, key) => [v === null || v === undefined ? "—" : `${v}${unit}`, models.find((m) => m.key === key)?.label ?? String(key)]}
          />
          {models
            .filter((m) => !hidden.includes(m.key))
            .map((m) => (
              <Bar key={m.key} dataKey={m.key} fill={color(m.colorIndex)} radius={[4, 4, 0, 0]} maxBarSize={26} />
            ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function BeforeAfterChart({
  rows,
  beforeLabel,
  afterLabel,
  beforeColor,
  afterColor,
  unit,
}: {
  rows: { category: string; before: number | null; after: number | null }[];
  beforeLabel: string;
  afterLabel: string;
  beforeColor: number;
  afterColor: number;
  unit: string;
}) {
  const dark = useDark();
  const palette = dark ? DARK : LIGHT;
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={rows} barGap={2}>
        <CartesianGrid vertical={false} stroke="var(--line)" />
        <XAxis dataKey="category" {...axis} interval={0} fontSize={11} />
        <YAxis domain={[0, 100]} unit={unit} {...axis} axisLine={false} width={48} />
        <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "var(--line)", opacity: 0.35 }} formatter={(v) => `${v ?? "—"}${unit}`} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar dataKey="before" name={beforeLabel} fill={palette[beforeColor] ?? "#898781"} radius={[4, 4, 0, 0]} maxBarSize={26} />
        <Bar dataKey="after" name={afterLabel} fill={palette[afterColor] ?? "#898781"} radius={[4, 4, 0, 0]} maxBarSize={26} />
      </BarChart>
    </ResponsiveContainer>
  );
}
