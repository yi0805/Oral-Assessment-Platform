const STORAGE_KEY = "capstone_gradebook_state_v1";

export function loadGradebookState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function saveGradebookState(state) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}
