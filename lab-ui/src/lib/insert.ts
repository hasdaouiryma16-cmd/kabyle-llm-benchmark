type Editable = HTMLInputElement | HTMLTextAreaElement;

let lastFocused: Editable | null = null;

const isEditable = (el: unknown): el is Editable =>
  (el instanceof HTMLTextAreaElement ||
    (el instanceof HTMLInputElement && ["text", "search", ""].includes(el.type))) &&
  !el.readOnly &&
  !el.disabled;

/** Mémorise le dernier champ de texte actif (appelé une fois au démarrage). */
export function trackFocus(doc: Document = document): () => void {
  const onFocus = (e: FocusEvent) => {
    if (isEditable(e.target)) lastFocused = e.target;
  };
  doc.addEventListener("focusin", onFocus);
  return () => doc.removeEventListener("focusin", onFocus);
}

/**
 * Insère du texte à la position du curseur dans le dernier champ actif et prévient React
 * (événement « input »), comme si le caractère avait été tapé.
 */
export function insertAtCursor(text: string, target: Editable | null = lastFocused): boolean {
  if (!target || !target.isConnected) return false;
  const start = target.selectionStart ?? target.value.length;
  const end = target.selectionEnd ?? start;
  target.setRangeText(text, start, end, "end");
  target.dispatchEvent(new Event("input", { bubbles: true }));
  target.focus();
  return true;
}
