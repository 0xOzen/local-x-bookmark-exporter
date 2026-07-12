(() => {
  "use strict";

  const lib = globalThis.LocalXBookmarkLib;
  if (!lib) throw new Error("LocalXBookmarkLib must be loaded before scraper.js");

  function textOf(element) {
    if (!element) return "";
    return String(element.innerText || element.textContent || "").trim();
  }

  function findCanonicalUrl(article) {
    const timeLink = article.querySelector("time")?.closest("a[href*='/status/']");
    const candidates = [
      timeLink,
      ...article.querySelectorAll("a[href*='/status/']")
    ].filter(Boolean);

    for (const anchor of candidates) {
      const normalized = lib.normalizeStatusUrl(anchor.getAttribute("href"), location.href);
      if (normalized) return normalized;
    }
    return null;
  }

  function authorNameFrom(article, authorHandle) {
    const userBox = article.querySelector('[data-testid="User-Name"]');
    if (!userBox) return "";

    const profileLinks = [...userBox.querySelectorAll("a[href]")];
    const profileLink = profileLinks.find((anchor) => {
      try {
        return new URL(anchor.getAttribute("href"), location.href).pathname === `/${authorHandle}`;
      } catch (_error) {
        return false;
      }
    });

    if (profileLink) {
      const value = textOf(profileLink);
      if (value && value !== `@${authorHandle}`) return value.split("\n")[0].trim();
    }

    return textOf(userBox)
      .split("\n")
      .map((part) => part.trim())
      .find((part) => part && !part.startsWith("@") && part !== "·") || "";
  }

  function mediaUrlsFrom(article) {
    const urls = new Set();
    const selectors = [
      'img[src*="pbs.twimg.com/media"]',
      'img[src*="pbs.twimg.com/ext_tw_video_thumb"]',
      "video[poster]"
    ];

    for (const element of article.querySelectorAll(selectors.join(","))) {
      const value = element.getAttribute("src") || element.getAttribute("poster");
      if (value) urls.add(value);
    }
    return [...urls];
  }

  function extractBookmarkFromArticle(article, capturedAt = new Date().toISOString()) {
    if (!article?.querySelector('[data-testid="removeBookmark"]')) return null;

    const url = findCanonicalUrl(article);
    if (!url) return null;

    const match = url.match(/^https:\/\/x\.com\/([^/]+)\/status\/(\d+)$/);
    if (!match) return null;

    const textNode = article.querySelector('[data-testid="tweetText"]');
    const timeNode = article.querySelector("time[datetime]");

    return {
      id: match[2],
      url,
      authorHandle: match[1],
      authorName: authorNameFrom(article, match[1]),
      postedAt: timeNode?.getAttribute("datetime") || "",
      text: textOf(textNode),
      language: textNode?.getAttribute("lang") || "",
      mediaUrls: mediaUrlsFrom(article),
      capturedAt
    };
  }

  function collectBookmarks(root = document, capturedAt = new Date().toISOString()) {
    const records = new Map();
    for (const article of root.querySelectorAll('article[data-testid="tweet"]')) {
      const record = extractBookmarkFromArticle(article, capturedAt);
      if (record && !records.has(record.id)) records.set(record.id, record);
    }
    return [...records.values()];
  }

  globalThis.LocalXBookmarkScraper = {
    textOf,
    findCanonicalUrl,
    authorNameFrom,
    mediaUrlsFrom,
    extractBookmarkFromArticle,
    collectBookmarks
  };
})();
