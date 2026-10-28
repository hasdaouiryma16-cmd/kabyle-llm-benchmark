import { useState } from "react";
import { LATIN_KABYLE, TIFINAGH, TYPOGRAPHY } from "../lib/charsets";
import { insertAtCursor } from "../lib/insert";
import { cx } from "./ui";

/** Barre de caractères spéciaux : un clic insère le caractère dans le dernier champ actif. */
export function CharBar({ className }: { className?: string }) {
  const [set, setSet] = useState<"latin" | "tifinagh">("latin");
  const chars = set === "latin" ? [...LATIN_KABYLE, ...TYPOGRAPHY] : TIFINAGH;
  return (
    <div
      className={cx(
        "flex flex-wrap items-center gap-1 rounded-lg border border-stone-200 bg-stone-50 p-1.5 dark:border-neutral-800 dark:bg-neutral-950",
        className,
      )}
      aria-label="Caractères spéciaux"
    >
      <div className="mr-1 flex rounded-md bg-stone-200/70 p-0.5 text-xs dark:bg-neutral-800">
        {(["latin", "tifinagh"] as const).map((s) => (
          <button
            key={s}
            type="button"
            onMouseDown={(e) => e.preventDefault()}
            onClick={() => setSet(s)}
            className={cx(
              "rounded px-2 py-0.5",
              set === s ? "bg-white shadow-sm dark:bg-neutral-700" : "text-stone-500",
            )}
          >
            {s === "latin" ? "Latin" : "Tifinagh"}
          </button>
        ))}
      </div>
      {chars.map((c) => (
        <button
          key={c}
          type="button"
          title={`Insérer ${c} (U+${c.codePointAt(0)!.toString(16).toUpperCase().padStart(4, "0")})`}
          // Garde le focus dans le champ de saisie
          onMouseDown={(e) => e.preventDefault()}
          onClick={() => insertAtCursor(c)}
          className="kab h-8 min-w-8 rounded-md border border-transparent px-1.5 text-base hover:border-stone-300 hover:bg-white dark:hover:border-neutral-700 dark:hover:bg-neutral-800"
        >
          {c}
        </button>
      ))}
    </div>
  );
}
