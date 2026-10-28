import { useEffect, useState } from "react";

/**
 * Palette catégorielle validée (daltonisme, contraste) en mode clair et sombre.
 * Ordre fixe : la couleur suit le modèle (son rang dans la configuration), jamais son
 * classement, pour qu'un filtre ne repeigne pas les séries restantes.
 */
const LIGHT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"];
const DARK = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"];
export const OTHER = { light: "#898781", dark: "#898781" };

export function useDarkMode(): boolean {
  const [dark, setDark] = useState(() => document.documentElement.classList.contains("dark"));
  useEffect(() => {
    const observer = new MutationObserver(() =>
      setDark(document.documentElement.classList.contains("dark")),
    );
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
    return () => observer.disconnect();
  }, []);
  return dark;
}

export function seriesColor(index: number, dark: boolean): string {
  if (index < 0 || index >= LIGHT.length) return dark ? OTHER.dark : OTHER.light;
  return (dark ? DARK : LIGHT)[index];
}
