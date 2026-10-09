"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const source = fs.readFileSync(path.join(__dirname, "../popup.js"), "utf8");

async function runPopup(url) {
  let listener;
  const elements = {
    start: { disabled: false, addEventListener(_event, handler) { listener = handler; } },
    status: { textContent: "", className: "" },
    format: { value: "json" },
    delay: { value: "1800" },
    idleRounds: { value: "10" },
    maxBookmarks: { value: "2" }
  };
  const injections = [];
  const messages = [];
  const context = {
    URL,
    LocalXBookmarkI18n: { t: (key) => key, localizeDocument() {} },
    document: { getElementById: (id) => elements[id] },
    chrome: {
      tabs: {
        query: async () => [{ id: 42, url }],
        sendMessage: async (...args) => { messages.push(args); return { ok: true }; }
      },
      scripting: { executeScript: async (request) => { injections.push(request); } }
    }
  };
  vm.runInNewContext(source, context);
  await listener();
  return { elements, injections, messages };
}

(async () => {
  const accepted = [
    "https://x.com/i/history/bookmarks/",
    "https://x.com/i/history/bookmarks",
    "https://www.x.com/i/history/bookmarks/?sort=latest",
    "https://x.com:443/i/history/bookmarks/folder/123",
    "https://x.com/i/bookmarks",
    "https://x.com/i/bookmarks/",
    "https://www.x.com/i/bookmarks/folder/123?cursor=abc"
  ];
  const rejected = [
    "https://x.com/i/history/bookmarksevil",
    "https://x.com/i/bookmarksevil",
    "https://x.com/i/history",
    "https://x.com/home",
    "https://x.com.evil.example/i/history/bookmarks/",
    "https://evil.example/i/history/bookmarks/",
    "http://x.com/i/history/bookmarks/",
    "https://user:pass@x.com/i/history/bookmarks/",
    "https://x.com:444/i/history/bookmarks/",
    "https://x.com/i/history/bookmarks/#fragment",
    "not a URL",
    undefined
  ];
  for (const url of accepted) {
    const result = await runPopup(url);
    assert.equal(result.injections.length, 1, `Expected script injection on ${url}`);
    assert.equal(result.injections[0].target.tabId, 42);
    assert.equal(JSON.stringify(result.injections[0].files), JSON.stringify(["lib.js", "scraper.js", "i18n.js", "content.js"]));
    assert.equal(result.messages.length, 1);
    assert.equal(result.messages[0][0], 42);
    assert.equal(result.messages[0][1].type, "LOCAL_X_START_BOOKMARK_EXPORT");
    assert.equal(result.messages[0][1].options.maxBookmarks, 2);
    assert.equal(result.elements.status.className, "success");
  }
  for (const url of rejected) {
    const result = await runPopup(url);
    assert.equal(result.injections.length, 0, `Must not inject on ${url}`);
    assert.equal(result.messages.length, 0);
    assert.equal(result.elements.status.textContent, "openBookmarksError");
    assert.equal(result.elements.status.className, "error");
    assert.equal(result.elements.start.disabled, false);
  }
  console.log(`PASS popup route workflow: ${accepted.length} accepted, ${rejected.length} rejected`);
})().catch((error) => { console.error(error); process.exitCode = 1; });
