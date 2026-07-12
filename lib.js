(() => {
  "use strict";

  const CSV_FIELDS = [
    "id",
    "url",
    "authorHandle",
    "authorName",
    "postedAt",
    "text",
    "language",
    "mediaUrls",
    "capturedAt"
  ];

  function normalizeStatusUrl(href, base = "https://x.com") {
    if (!href) return null;

    try {
      const url = new URL(href, base);
      const match = url.pathname.match(/^\/([^/]+)\/status\/(\d+)/);
      if (!match || match[1].toLowerCase() === "i") return null;
      return `https://x.com/${match[1]}/status/${match[2]}`;
    } catch (_error) {
      return null;
    }
  }

  function csvCell(value) {
    const normalized = Array.isArray(value)
      ? value.join(" | ")
      : value === null || value === undefined
        ? ""
        : String(value);
    return `"${normalized.replace(/"/g, '""')}"`;
  }

  function toCsv(records) {
    const rows = [CSV_FIELDS.map(csvCell).join(",")];
    for (const record of records) {
      rows.push(CSV_FIELDS.map((field) => csvCell(record[field])).join(","));
    }
    return `\uFEFF${rows.join("\r\n")}`;
  }

  function markdownCell(value) {
    const normalized = Array.isArray(value)
      ? value.join("<br>")
      : value === null || value === undefined
        ? ""
        : String(value);
    return normalized.replace(/\|/g, "\\|").replace(/\r?\n/g, "<br>");
  }

  function toMarkdown(payload) {
    const lines = [
      "# X Bookmark Export",
      "",
      `Exported: ${payload.meta.exportedAt}`,
      `Records: ${payload.meta.count}`,
      `Method: ${payload.meta.method}`,
      "",
      "| Author | Date | Bookmark | Text | Media |",
      "| --- | --- | --- | --- | --- |"
    ];

    for (const record of payload.bookmarks) {
      const author = record.authorName
        ? `${record.authorName} (@${record.authorHandle})`
        : `@${record.authorHandle}`;
      const link = `[Open post](${record.url})`;
      const media = (record.mediaUrls || [])
        .map((url, index) => `[Media ${index + 1}](${url})`)
        .join("<br>");
      lines.push(
        `| ${markdownCell(author)} | ${markdownCell(record.postedAt)} | ${link} | ${markdownCell(record.text)} | ${media} |`
      );
    }

    return `${lines.join("\n")}\n`;
  }

  function serialize(payload, format) {
    if (format === "csv") return toCsv(payload.bookmarks);
    if (format === "markdown") return toMarkdown(payload);
    return `${JSON.stringify(payload, null, 2)}\n`;
  }

  function mimeType(format) {
    if (format === "csv") return "text/csv;charset=utf-8";
    if (format === "markdown") return "text/markdown;charset=utf-8";
    return "application/json;charset=utf-8";
  }

  function fileExtension(format) {
    if (format === "markdown") return "md";
    if (format === "csv") return "csv";
    return "json";
  }

  function exportFileName(format, date = new Date()) {
    const stamp = date.toISOString().replace(/[:.]/g, "-");
    return `local-x-bookmarks-${stamp}.${fileExtension(format)}`;
  }

  const api = {
    CSV_FIELDS,
    normalizeStatusUrl,
    csvCell,
    toCsv,
    toMarkdown,
    serialize,
    mimeType,
    fileExtension,
    exportFileName
  };

  globalThis.LocalXBookmarkLib = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})();
