import { useEffect, useState } from "react";
import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import { cx } from "./components/ui";
import { trackFocus } from "./lib/insert";
import { GradePage } from "./pages/GradePage";
import { GuidedPage } from "./pages/GuidedPage";
import { ResultsPage } from "./pages/ResultsPage";
import { RunsPage } from "./pages/RunsPage";
import { TestsPage } from "./pages/TestsPage";

const NAV = [
  { to: "/tests", label: "Tests" },
  { to: "/guided", label: "Mode guidé" },
  { to: "/runs", label: "Exécutions" },
  { to: "/grade", label: "Notation" },
  { to: "/results", label: "Résultats" },
];

function ThemeToggle() {
  const [dark, setDark] = useState(() => document.documentElement.classList.contains("dark"));
  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    try {
      localStorage.setItem("theme", dark ? "dark" : "light");
    } catch {
      /* stockage indisponible : le thème ne sera pas mémorisé */
    }
  }, [dark]);
  return (
    <button
      type="button"
      onClick={() => setDark((d) => !d)}
      className="rounded-md px-2 py-1 text-sm text-stone-600 hover:bg-stone-200/70 dark:text-stone-300 dark:hover:bg-neutral-800"
      aria-label={dark ? "Passer en mode clair" : "Passer en mode sombre"}
    >
      {dark ? "☀ Clair" : "☾ Sombre"}
    </button>
  );
}

export function App() {
  useEffect(() => trackFocus(), []);
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-30 border-b border-stone-200 bg-stone-50/90 backdrop-blur dark:border-neutral-800 dark:bg-neutral-950/90">
        <div className="mx-auto flex max-w-7xl items-center gap-6 px-4 py-3">
          <div className="flex items-center gap-2">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-teal-700 text-sm font-bold text-white">K</span>
            <div className="leading-tight">
              <div className="text-sm font-semibold">Kabyle LLM Benchmark</div>
              <div className="text-xs text-stone-500">Labo local</div>
            </div>
          </div>
          <nav className="flex flex-1 gap-1 overflow-x-auto">
            {NAV.map((n) => (
              <NavLink
                key={n.to}
                to={n.to}
                className={({ isActive }) =>
                  cx(
                    "whitespace-nowrap rounded-md px-3 py-1.5 text-sm",
                    isActive
                      ? "bg-white font-medium shadow-sm dark:bg-neutral-800"
                      : "text-stone-600 hover:bg-stone-200/70 dark:text-stone-400 dark:hover:bg-neutral-800/60",
                  )
                }
              >
                {n.label}
              </NavLink>
            ))}
          </nav>
          <ThemeToggle />
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-8">
        <Routes>
          <Route path="/" element={<Navigate to="/tests" replace />} />
          <Route path="/tests" element={<TestsPage />} />
          <Route path="/guided" element={<GuidedPage />} />
          <Route path="/runs" element={<RunsPage />} />
          <Route path="/grade" element={<GradePage />} />
          <Route path="/results" element={<ResultsPage />} />
        </Routes>
      </main>
    </div>
  );
}
