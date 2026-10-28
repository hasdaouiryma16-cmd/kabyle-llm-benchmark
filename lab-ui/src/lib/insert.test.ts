import { describe, expect, it } from "vitest";
import { insertAtCursor, trackFocus } from "./insert";

describe("insertAtCursor", () => {
  it("insère au curseur et remplace la sélection", () => {
    const input = document.createElement("input");
    document.body.appendChild(input);
    input.value = "abcd";
    input.setSelectionRange(1, 3);
    let events = 0;
    input.addEventListener("input", () => events++);

    expect(insertAtCursor("ɛ", input)).toBe(true);
    expect(input.value).toBe("aɛd");
    expect(input.selectionStart).toBe(2);
    expect(events).toBe(1);
  });

  it("utilise le dernier champ qui a eu le focus", () => {
    const stop = trackFocus();
    const area = document.createElement("textarea");
    document.body.appendChild(area);
    area.focus();
    area.blur();
    expect(insertAtCursor("ⵣ")).toBe(true);
    expect(area.value).toBe("ⵣ");
    stop();
  });

  it("ne fait rien sans champ cible", () => {
    expect(insertAtCursor("x", null)).toBe(false);
  });
});
