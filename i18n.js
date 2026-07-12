(() => {
  "use strict";

  const FALLBACKS = {
    appName: "Local X Bookmark Exporter",
    appDescription: "Export rendered X bookmark cards to JSON, CSV, or Markdown without API keys or a backend.",
    localOnly: "LOCAL ONLY",
    popupTitle: "X Bookmark Exporter",
    intro: "Reads bookmark cards from the open X bookmarks page. It does not collect passwords, cookies, or session tokens.",
    formatLabel: "Export format",
    formatJson: "JSON (recommended)",
    formatCsv: "CSV",
    formatMarkdown: "Markdown",
    advancedSettings: "Advanced settings",
    delayLabel: "Wait between scrolls",
    delay1200: "1.2 seconds",
    delay1800: "1.8 seconds (recommended)",
    delay2500: "2.5 seconds",
    idleLabel: "Stop after no new records",
    idle6: "6 passes",
    idle10: "10 passes (recommended)",
    idle15: "15 passes",
    maxBookmarksLabel: "Maximum bookmarks (0 = unlimited)",
    startButton: "Start export",
    initialStatus: "Open x.com/i/bookmarks first.",
    privacyText: "Privacy: Data is processed only in the active tab and downloaded directly to your device. No backend is used.",
    checkingTab: "Checking the active tab...",
    openBookmarksError: "Open x.com/i/bookmarks first, then try again.",
    exportCouldNotStart: "Export could not start.",
    startedStatus: "Export started. Keep the tab open; progress appears in the lower-right corner.",
    panelBadge: "LOCAL EXPORT",
    panelRunningTitle: "Reading bookmarks",
    stopButton: "Stop",
    closeButton: "Close",
    recordsFound: "unique bookmarks found",
    keepOpen: "Keep this tab open. Data is processed only in this tab.",
    stopping: "Stopping. Collected records will be written to a file...",
    scanProgress: "Scan pass $1. Passes with no new records: $2.",
    panelFailedTitle: "Export failed",
    panelCompleteTitle: "Export complete",
    alreadyRunning: "An export is already running.",
    noBookmarksFound: "No bookmark cards were found. Wait for the page to load, then try again.",
    downloadComplete: "$1 records were saved to your Downloads folder."
  };

  function normalizeSubstitutions(substitutions) {
    if (substitutions === undefined || substitutions === null) return [];
    return Array.isArray(substitutions) ? substitutions.map(String) : [String(substitutions)];
  }

  function applyFallbackSubstitutions(message, substitutions) {
    return substitutions.reduce(
      (result, value, index) => result.replaceAll(`$${index + 1}`, value),
      message
    );
  }

  function t(key, substitutions) {
    const values = normalizeSubstitutions(substitutions);
    if (typeof chrome !== "undefined" && chrome.i18n?.getMessage) {
      const localized = chrome.i18n.getMessage(key, values);
      if (localized) return localized;
    }
    return applyFallbackSubstitutions(FALLBACKS[key] || key, values);
  }

  function localizeDocument(root = document) {
    for (const element of root.querySelectorAll("[data-i18n]")) {
      element.textContent = t(element.dataset.i18n);
    }

    if (typeof chrome !== "undefined" && chrome.i18n?.getUILanguage) {
      document.documentElement.lang = chrome.i18n.getUILanguage() || "en";
    }
  }

  globalThis.LocalXBookmarkI18n = { FALLBACKS, t, localizeDocument };
})();
