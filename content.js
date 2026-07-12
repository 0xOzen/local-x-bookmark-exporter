(() => {
  "use strict";

  if (globalThis.__localXBookmarkExporterInstalled) return;
  globalThis.__localXBookmarkExporterInstalled = true;

  const lib = globalThis.LocalXBookmarkLib;
  const scraper = globalThis.LocalXBookmarkScraper;
  const { t } = globalThis.LocalXBookmarkI18n;
  const state = {
    running: false,
    stopRequested: false,
    records: new Map(),
    overlay: null,
    startedAt: null
  };

  function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  function createOverlay() {
    document.getElementById("local-x-bookmark-exporter-root")?.remove();

    const host = document.createElement("div");
    host.id = "local-x-bookmark-exporter-root";
    host.style.cssText = "position:fixed;right:18px;bottom:18px;z-index:2147483647";
    const shadow = host.attachShadow({ mode: "closed" });
    shadow.innerHTML = `
      <style>
        *{box-sizing:border-box}.panel{width:320px;padding:16px;border:1px solid #303846;border-radius:16px;background:#0b0e14;color:#f5f7fa;box-shadow:0 18px 55px rgba(0,0,0,.48);font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
        .top{display:flex;align-items:center;justify-content:space-between;gap:12px}.badge{color:#70efb3;font-size:10px;font-weight:800;letter-spacing:.13em}.title{margin:7px 0 0;font-size:16px;font-weight:800}
        .count{margin:14px 0 5px;font-size:28px;font-weight:850}.label,.detail{color:#aab3c0;font-size:12px;line-height:1.45}.track{height:5px;margin:13px 0;border-radius:999px;background:#222a36;overflow:hidden}.bar{width:35%;height:100%;border-radius:inherit;background:#557fff;animation:move 1.2s ease-in-out infinite alternate}
        button{border:0;border-radius:9px;padding:8px 11px;background:#242c38;color:#f5f7fa;font-weight:700;cursor:pointer}.stop{background:#572d34;color:#ffc1c8}.close{display:none}.error{color:#ff9e9e}.success{color:#70efb3}@keyframes move{to{transform:translateX(185%)}}
      </style>
      <div class="panel">
        <div class="top"><div><div class="badge"></div><div class="title"></div></div><button class="stop" type="button"></button><button class="close" type="button"></button></div>
        <div class="count">0</div><div class="label"></div>
        <div class="track"><div class="bar"></div></div>
        <div class="detail"></div>
      </div>`;

    document.documentElement.appendChild(host);
    const elements = {
      host,
      badge: shadow.querySelector(".badge"),
      title: shadow.querySelector(".title"),
      count: shadow.querySelector(".count"),
      label: shadow.querySelector(".label"),
      detail: shadow.querySelector(".detail"),
      track: shadow.querySelector(".track"),
      stop: shadow.querySelector(".stop"),
      close: shadow.querySelector(".close")
    };

    elements.badge.textContent = t("panelBadge");
    elements.title.textContent = t("panelRunningTitle");
    elements.label.textContent = t("recordsFound");
    elements.detail.textContent = t("keepOpen");
    elements.stop.textContent = t("stopButton");
    elements.close.textContent = t("closeButton");

    elements.stop.addEventListener("click", () => {
      state.stopRequested = true;
      elements.stop.disabled = true;
      elements.detail.textContent = t("stopping");
    });
    elements.close.addEventListener("click", () => host.remove());
    state.overlay = elements;
    return elements;
  }

  function updateOverlay(cycle, idleRounds) {
    if (!state.overlay) return;
    state.overlay.count.textContent = String(state.records.size);
    state.overlay.detail.textContent = t("scanProgress", [cycle, idleRounds]);
  }

  function finishOverlay(message, kind = "success") {
    if (!state.overlay) return;
    state.overlay.title.textContent = kind === "error" ? t("panelFailedTitle") : t("panelCompleteTitle");
    state.overlay.title.className = `title ${kind}`;
    state.overlay.detail.textContent = message;
    state.overlay.track.style.display = "none";
    state.overlay.stop.style.display = "none";
    state.overlay.close.style.display = "inline-block";
  }

  function collectVisible(maxBookmarks) {
    const capturedAt = new Date().toISOString();
    let added = 0;
    for (const record of scraper.collectBookmarks(document, capturedAt)) {
      if (maxBookmarks > 0 && state.records.size >= maxBookmarks) break;
      if (!state.records.has(record.id)) {
        state.records.set(record.id, record);
        added += 1;
      }
    }
    return added;
  }

  function scrollForward() {
    const articles = [...document.querySelectorAll('article[data-testid="tweet"]')];
    const lastArticle = articles.at(-1);
    if (lastArticle) lastArticle.scrollIntoView({ block: "end", behavior: "auto" });
    window.scrollBy({ top: Math.max(700, Math.floor(window.innerHeight * 0.82)), behavior: "auto" });
  }

  function download(payload, format) {
    const content = lib.serialize(payload, format);
    const blob = new Blob([content], { type: lib.mimeType(format) });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = lib.exportFileName(format);
    anchor.style.display = "none";
    document.documentElement.appendChild(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 10000);
  }

  async function runExport(rawOptions) {
    if (state.running) throw new Error(t("alreadyRunning"));

    const options = {
      format: ["json", "csv", "markdown"].includes(rawOptions?.format) ? rawOptions.format : "json",
      scrollDelayMs: Math.min(5000, Math.max(800, Number(rawOptions?.scrollDelayMs) || 1800)),
      maxIdleRounds: Math.min(30, Math.max(3, Number(rawOptions?.maxIdleRounds) || 10)),
      maxBookmarks: Math.max(0, Number(rawOptions?.maxBookmarks) || 0)
    };

    state.running = true;
    state.stopRequested = false;
    state.records = new Map();
    state.startedAt = new Date().toISOString();
    const startScrollY = window.scrollY;
    createOverlay();

    let idleRounds = 0;
    let cycle = 0;
    let reason = "no-new-cards";

    try {
      while (!state.stopRequested) {
        cycle += 1;
        const added = collectVisible(options.maxBookmarks);
        idleRounds = added > 0 ? 0 : idleRounds + 1;
        updateOverlay(cycle, idleRounds);

        if (options.maxBookmarks > 0 && state.records.size >= options.maxBookmarks) {
          reason = "configured-limit";
          break;
        }
        if (idleRounds >= options.maxIdleRounds) {
          reason = "no-new-cards";
          break;
        }

        scrollForward();
        await sleep(options.scrollDelayMs);
      }

      if (state.stopRequested) reason = "user-stopped";
      collectVisible(options.maxBookmarks);

      const bookmarks = [...state.records.values()];
      if (bookmarks.length === 0) throw new Error(t("noBookmarksFound"));

      const payload = {
        meta: {
          schemaVersion: 1,
          sourcePage: location.href,
          method: "local DOM scrolling",
          completeness: "best-effort; X does not expose a total count to this exporter",
          startedAt: state.startedAt,
          exportedAt: new Date().toISOString(),
          count: bookmarks.length,
          stopReason: reason,
          options
        },
        bookmarks
      };

      download(payload, options.format);
      finishOverlay(t("downloadComplete", bookmarks.length));
      setTimeout(() => window.scrollTo({ top: startScrollY, behavior: "auto" }), 250);
    } catch (error) {
      finishOverlay(error.message || String(error), "error");
      throw error;
    } finally {
      state.running = false;
    }
  }

  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (message?.type !== "LOCAL_X_START_BOOKMARK_EXPORT") return false;
    if (state.running) {
      sendResponse({ ok: false, error: t("alreadyRunning") });
      return false;
    }

    runExport(message.options).catch((error) => console.error("Local X bookmark export failed", error));
    sendResponse({ ok: true });
    return false;
  });
})();
