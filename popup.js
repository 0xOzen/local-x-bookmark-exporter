(() => {
  "use strict";

  const { t, localizeDocument } = globalThis.LocalXBookmarkI18n;
  localizeDocument();

  const startButton = document.getElementById("start");
  const status = document.getElementById("status");

  function setStatus(message, kind = "") {
    status.textContent = message;
    status.className = kind;
  }

  function isBookmarksPage(url) {
    try {
      const parsed = new URL(url);
      const allowedHost = parsed.hostname === "x.com" || parsed.hostname === "www.x.com";
      const allowedRoute = ["/i/bookmarks", "/i/history/bookmarks"].some(
        (route) => parsed.pathname === route || parsed.pathname.startsWith(`${route}/`)
      );
      return parsed.protocol === "https:" && allowedHost && allowedRoute &&
        !parsed.username && !parsed.password && !parsed.port && !parsed.hash;
    } catch (_error) {
      return false;
    }
  }

  startButton.addEventListener("click", async () => {
    startButton.disabled = true;
    setStatus(t("checkingTab"));

    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab?.id || !isBookmarksPage(tab.url)) {
        throw new Error(t("openBookmarksError"));
      }

      const options = {
        format: document.getElementById("format").value,
        scrollDelayMs: Number(document.getElementById("delay").value),
        maxIdleRounds: Number(document.getElementById("idleRounds").value),
        maxBookmarks: Math.max(0, Number(document.getElementById("maxBookmarks").value) || 0)
      };

      await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        files: ["lib.js", "scraper.js", "i18n.js", "content.js"]
      });

      const response = await chrome.tabs.sendMessage(tab.id, {
        type: "LOCAL_X_START_BOOKMARK_EXPORT",
        options
      });

      if (!response?.ok) throw new Error(response?.error || t("exportCouldNotStart"));
      setStatus(t("startedStatus"), "success");
    } catch (error) {
      setStatus(error.message || String(error), "error");
      startButton.disabled = false;
    }
  });
})();
