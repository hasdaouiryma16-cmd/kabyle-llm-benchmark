import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ButtonHTMLAttributes,
  type ReactNode,
} from "react";

const cx = (...classes: (string | false | null | undefined)[]) => classes.filter(Boolean).join(" ");
export { cx };

type Variant = "primary" | "secondary" | "ghost" | "danger";

const VARIANTS: Record<Variant, string> = {
  primary: "bg-teal-700 text-white hover:bg-teal-800 dark:bg-teal-600 dark:hover:bg-teal-500",
  secondary:
    "border border-stone-300 bg-white text-stone-800 hover:bg-stone-100 dark:border-neutral-700 dark:bg-neutral-900 dark:text-stone-100 dark:hover:bg-neutral-800",
  ghost: "text-stone-700 hover:bg-stone-200/70 dark:text-stone-300 dark:hover:bg-neutral-800",
  danger: "bg-red-700 text-white hover:bg-red-800",
};

export function Button({
  variant = "secondary",
  size = "md",
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; size?: "sm" | "md" }) {
  return (
    <button
      type="button"
      {...props}
      className={cx(
        "inline-flex items-center justify-center gap-1.5 rounded-md font-medium transition-colors",
        "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-600",
        "disabled:cursor-not-allowed disabled:opacity-50",
        size === "sm" ? "px-2.5 py-1 text-xs" : "px-3.5 py-2 text-sm",
        VARIANTS[variant],
        className,
      )}
    />
  );
}

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={cx(
        "rounded-xl border border-stone-200 bg-white p-5 shadow-sm dark:border-neutral-800 dark:bg-neutral-900",
        className,
      )}
    >
      {children}
    </div>
  );
}

const TONES = {
  neutral: "bg-stone-100 text-stone-700 dark:bg-neutral-800 dark:text-stone-300",
  teal: "bg-teal-50 text-teal-800 dark:bg-teal-950 dark:text-teal-300",
  amber: "bg-amber-50 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
  red: "bg-red-50 text-red-800 dark:bg-red-950 dark:text-red-300",
  green: "bg-green-50 text-green-800 dark:bg-green-950 dark:text-green-300",
  violet: "bg-violet-50 text-violet-800 dark:bg-violet-950 dark:text-violet-300",
};

export function Badge({ children, tone = "neutral" }: { children: ReactNode; tone?: keyof typeof TONES }) {
  return (
    <span className={cx("inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium", TONES[tone])}>
      {children}
    </span>
  );
}

export const inputClass =
  "w-full rounded-md border border-stone-300 bg-white px-3 py-2 text-sm text-stone-900 placeholder:text-stone-400 " +
  "focus:border-teal-600 focus:outline-none focus:ring-2 focus:ring-teal-600/20 " +
  "dark:border-neutral-700 dark:bg-neutral-950 dark:text-stone-100";

/** Pour les sélecteurs et filtres en ligne (largeur selon le contenu). */
export const inlineInputClass = inputClass.replace("w-full ", "w-auto ");

export function Field({ label, hint, children }: { label: string; hint?: ReactNode; children: ReactNode }) {
  return (
    <label className="block space-y-1">
      <span className="text-xs font-medium uppercase tracking-wide text-stone-500 dark:text-stone-400">
        {label}
      </span>
      {children}
      {hint && <span className="block text-xs text-stone-500 dark:text-stone-400">{hint}</span>}
    </label>
  );
}

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: ReactNode; actions?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-stone-500 dark:text-stone-400">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-xl border border-dashed border-stone-300 p-10 text-center text-sm text-stone-500 dark:border-neutral-700 dark:text-stone-400">
      {children}
    </div>
  );
}

export function Alert({ children, tone = "red" }: { children: ReactNode; tone?: "red" | "amber" | "teal" }) {
  const tones = {
    red: "border-red-200 bg-red-50 text-red-800 dark:border-red-900 dark:bg-red-950/50 dark:text-red-300",
    amber: "border-amber-200 bg-amber-50 text-amber-900 dark:border-amber-900 dark:bg-amber-950/50 dark:text-amber-200",
    teal: "border-teal-200 bg-teal-50 text-teal-900 dark:border-teal-900 dark:bg-teal-950/50 dark:text-teal-200",
  };
  return <div className={cx("rounded-md border px-3 py-2 text-sm", tones[tone])}>{children}</div>;
}

export function Modal({
  open,
  title,
  onClose,
  children,
  wide,
}: {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
  wide?: boolean;
}) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-40 flex items-start justify-center overflow-y-auto bg-black/40 p-4 pt-12" onMouseDown={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={cx(
          "w-full rounded-xl border border-stone-200 bg-white shadow-xl dark:border-neutral-800 dark:bg-neutral-900",
          wide ? "max-w-4xl" : "max-w-lg",
        )}
        onMouseDown={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-stone-200 px-5 py-3 dark:border-neutral-800">
          <h2 className="font-semibold">{title}</h2>
          <Button variant="ghost" size="sm" onClick={onClose} aria-label="Fermer">
            ✕
          </Button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  );
}

export function Spinner() {
  return (
    <span
      aria-label="Chargement"
      className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-stone-300 border-t-teal-600"
    />
  );
}

export function ProgressBar({ ok, error, total }: { ok: number; error: number; total: number }) {
  const pct = (n: number) => (total ? (n / total) * 100 : 0);
  return (
    <div
      className="flex h-2 w-full overflow-hidden rounded-full bg-stone-200 dark:bg-neutral-800"
      role="progressbar"
      aria-valuenow={ok + error}
      aria-valuemax={total}
    >
      <div className="bg-teal-600" style={{ width: `${pct(ok)}%` }} />
      <div className="bg-red-500" style={{ width: `${pct(error)}%` }} />
    </div>
  );
}

// ── Notifications ───────────────────────────────────────────

type Toast = { id: number; message: string; tone: "ok" | "error" };
const ToastContext = createContext<(message: string, tone?: Toast["tone"]) => void>(() => {});

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const notify = useCallback((message: string, tone: Toast["tone"] = "ok") => {
    const id = Date.now() + Math.random();
    setToasts((t) => [...t, { id, message, tone }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), tone === "error" ? 7000 : 3500);
  }, []);
  return (
    <ToastContext.Provider value={notify}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex max-w-sm flex-col gap-2" aria-live="polite">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={cx(
              "rounded-lg px-4 py-2.5 text-sm shadow-lg",
              t.tone === "ok" ? "bg-stone-900 text-white dark:bg-stone-100 dark:text-stone-900" : "bg-red-700 text-white",
            )}
          >
            {t.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export const useToast = () => useContext(ToastContext);
