"use strict";

const folderInput = document.querySelector("#folder-input");
const filesInput = document.querySelector("#files-input");
const fileActions = document.querySelector("#file-actions");
const folderButton = document.querySelector("#choose-folder");
const filesButton = document.querySelector("#choose-files");
const fileStatus = document.querySelector("#file-status");
const folderNote = document.querySelector("#folder-note");
const searchForm = document.querySelector("#search-form");
const searchButton = document.querySelector("#search-button");
const textQuery = document.querySelector("#text-query");
const speakerQuery = document.querySelector("#speaker-query");
const status = document.querySelector("#status");
const resultCount = document.querySelector("#result-count");
const resultOutput = document.querySelector("#results");
const downloadButton = document.querySelector("#download-button");
const fileErrors = document.querySelector("#file-errors");
const fileErrorList = document.querySelector("#file-error-list");

let selectedFiles = [];
let localSearchAvailable = false;
let staticCorpus = [];
let compressedCorpusPromise = null;

function comparePaths(left, right) {
  const leftParts = (left.webkitRelativePath || left.name).split("/");
  const rightParts = (right.webkitRelativePath || right.name).split("/");
  const partCount = Math.min(leftParts.length, rightParts.length);

  for (let index = 0; index < partCount; index += 1) {
    if (leftParts[index] < rightParts[index]) return -1;
    if (leftParts[index] > rightParts[index]) return 1;
  }

  return leftParts.length - rightParts.length;
}

function updateSelectedFiles(fileList) {
  selectedFiles = Array.from(fileList)
    .filter((file) => file.name.toLowerCase().endsWith(".txt"))
    .sort(comparePaths);

  const ignoredCount = fileList.length - selectedFiles.length;
  if (selectedFiles.length === 0) {
    fileStatus.textContent = "TXTファイルが見つかりません。";
  } else {
    const countLabel = `${selectedFiles.length.toLocaleString()} 個のTXTファイルを選択しました。`;
    fileStatus.textContent = ignoredCount
      ? `${countLabel} TXT以外の${ignoredCount.toLocaleString()}ファイルは無視しました。`
      : countLabel;
  }

  resultOutput.value = "";
  if (resultCount) resultCount.textContent = "検索結果はここに表示されます。";
  setStatus("検索条件を入力して検索してください。");
  downloadButton.disabled = true;
  fileErrors.hidden = true;
  fileErrorList.replaceChildren();
}

function splitLines(content) {
  if (content.length === 0) return [];

  const lines = content.split(/\r\n|\n|\r/);
  if (/(?:\r\n|\n|\r)$/.test(content)) lines.pop();
  return lines;
}

function lineMatches(line, text, speaker) {
  const tabIndex = line.indexOf("\t");
  const hasTab = tabIndex !== -1;

  if (text !== null) {
    const searchableText = hasTab ? line.slice(tabIndex + 1) : line;
    if (!searchableText.includes(text)) return false;
  }

  if (speaker !== null && (!hasTab || !line.slice(0, tabIndex).includes(speaker))) {
    return false;
  }

  return true;
}

function setStatus(message, kind = "") {
  if (status) {
    status.textContent = message;
    status.dataset.kind = kind;
  } else {
    fileStatus.textContent = message;
  }
}

function showFileErrors(errors) {
  fileErrorList.replaceChildren();
  for (const error of errors) {
    const item = document.createElement("li");
    item.textContent = error;
    fileErrorList.append(item);
  }
  fileErrors.hidden = errors.length === 0;
}

async function searchFiles(text, speaker) {
  const matches = [];
  const errors = [];
  const decoder = new TextDecoder("utf-8", { fatal: true });

  for (let fileIndex = 0; fileIndex < selectedFiles.length; fileIndex += 1) {
    const file = selectedFiles[fileIndex];
    try {
      const content = decoder.decode(await file.arrayBuffer());
      const lines = splitLines(content);

      for (let lineIndex = 0; lineIndex < lines.length; lineIndex += 1) {
        const line = lines[lineIndex];
        if (lineMatches(line, text, speaker)) {
          matches.push(`${file.name}:${lineIndex + 1}: ${line.trimEnd()}`);
        }
      }
    } catch (error) {
      errors.push(`${file.webkitRelativePath || file.name}: ${error.message}`);
    }

    if ((fileIndex + 1) % 12 === 0) {
      setStatus(`検索中... ${fileIndex + 1} / ${selectedFiles.length} ファイル`);
      await new Promise((resolve) => setTimeout(resolve, 0));
    }
  }

  return { matches, errors };
}

async function searchLocalCorpus(text, speaker) {
  const parameters = new URLSearchParams();
  if (text !== null) parameters.set("text", text);
  if (speaker !== null) parameters.set("by", speaker);

  const response = await fetch(new URL(`api/search?${parameters.toString()}`, document.baseURI), {
    cache: "no-store",
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || `HTTP ${response.status}`);
  }
  return payload.matches;
}

async function searchStaticCorpus(text, speaker) {
  if (compressedCorpusPromise === null) {
    compressedCorpusPromise = loadCompressedCorpus();
  }
  const compressedLoaded = await compressedCorpusPromise;
  if (!compressedLoaded) {
    setStatus("圧縮データを読み込めないため、TXTファイルを個別に読み込みます。");
  }

  const matchesByFile = Array.from({ length: staticCorpus.length }, () => []);
  const errors = [];
  const decoder = new TextDecoder("utf-8", { fatal: true });
  let nextFileIndex = 0;
  let processed = 0;

  async function searchWorker() {
    while (nextFileIndex < staticCorpus.length) {
      const fileIndex = nextFileIndex;
      nextFileIndex += 1;
      const file = staticCorpus[fileIndex];

      try {
        if (file.content === null) {
          const response = await fetch(file.url);
          if (!response.ok) throw new Error(`HTTP ${response.status}`);
          file.content = decoder.decode(await response.arrayBuffer());
        }

        const lines = splitLines(file.content);
        for (let lineIndex = 0; lineIndex < lines.length; lineIndex += 1) {
          const line = lines[lineIndex];
          if (lineMatches(line, text, speaker)) {
            const filename = file.path.slice(file.path.lastIndexOf("/") + 1);
            matchesByFile[fileIndex].push(
              `${filename}:${lineIndex + 1}: ${line.trimEnd()}`,
            );
          }
        }
      } catch (error) {
        errors.push(`${file.path}: ${error.message}`);
      }

      processed += 1;
      if (processed % 20 === 0 || processed === staticCorpus.length) {
        setStatus(`検索中... ${processed} / ${staticCorpus.length} ファイル`);
        await new Promise((resolve) => setTimeout(resolve, 0));
      }
    }
  }

  const workerCount = Math.min(8, staticCorpus.length);
  await Promise.all(Array.from({ length: workerCount }, () => searchWorker()));
  return { matches: matchesByFile.flat(), errors };
}

async function loadCompressedCorpus() {
  try {
    if (typeof DecompressionStream !== "function") {
      throw new Error("このブラウザーはgzip展開に対応していません。");
    }

    const response = await fetch(new URL("exported-corpus.json.gz", document.baseURI));
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    if (!response.body) throw new Error("圧縮データを読み込めませんでした。");

    const decompressed = response.body.pipeThrough(new DecompressionStream("gzip"));
    const payload = await new Response(decompressed).json();
    if (!Array.isArray(payload.files)) throw new Error("圧縮データの形式が正しくありません。");

    staticCorpus = payload.files.map((file) => {
      if (typeof file.path !== "string" || typeof file.content !== "string") {
        throw new Error("圧縮データに不正なファイルがあります。");
      }
      return { path: file.path, content: file.content };
    });
    fileStatus.textContent =
      `圧縮データから ${staticCorpus.length.toLocaleString()} 個のTXTファイルを読み込みました。`;
    return true;
  } catch (error) {
    fileStatus.textContent = `圧縮データを利用できません (${error.message})。`;
    return false;
  }
}

async function initializeCorpus() {
  try {
    const response = await fetch(new URL("api/status", document.baseURI), {
      cache: "no-store",
    });
    const contentType = response.headers.get("content-type") || "";
    if (response.ok && contentType.includes("application/json")) {
      const payload = await response.json();
      if (!payload.ok) throw new Error(payload.error || "ローカル検索を利用できません。");

      localSearchAvailable = true;
      fileActions.hidden = true;
      folderNote.hidden = true;
      fileStatus.textContent =
        `exported フォルダーから ${payload.file_count.toLocaleString()} 個のTXTファイルを検索できます。`;
      return;
    }
  } catch {
    localSearchAvailable = false;
  }

  try {
    const response = await fetch(new URL("exported-manifest.json", document.baseURI));
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const manifest = await response.json();
    if (!Array.isArray(manifest.files) || manifest.files.some((path) => typeof path !== "string")) {
      throw new Error("検索データの一覧が正しくありません。");
    }

    staticCorpus = manifest.files.map((path) => ({
      path,
      url: new URL(
        path.split("/").map((segment) => encodeURIComponent(segment)).join("/"),
        document.baseURI,
      ),
      content: null,
    }));
    fileActions.hidden = true;
    folderNote.hidden = true;
    fileStatus.textContent =
      `公開された exported/ フォルダーから ${staticCorpus.length.toLocaleString()} 個のTXTファイルを検索できます。検索時に圧縮データを読み込みます。`;
  } catch (error) {
    fileActions.hidden = false;
    fileStatus.textContent =
      `検索データを読み込めませんでした (${error.message})。フォルダーまたはTXTファイルを選択してください。`;
    if (!("webkitdirectory" in folderInput)) {
      folderButton.hidden = true;
      folderNote.hidden = false;
    }
  }
}

folderButton.addEventListener("click", () => folderInput.click());
filesButton.addEventListener("click", () => filesInput.click());
folderInput.addEventListener("change", () => updateSelectedFiles(folderInput.files));
filesInput.addEventListener("change", () => updateSelectedFiles(filesInput.files));

searchForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = textQuery.value === "" ? null : textQuery.value;
  const speaker = speakerQuery.value === "" ? null : speakerQuery.value;

  if (!localSearchAvailable && staticCorpus.length === 0 && selectedFiles.length === 0) {
    setStatus("先に検索するTXTファイルまたはフォルダーを選択してください。", "error");
    return;
  }
  if (text === null && speaker === null) {
    setStatus("文章または人物名を入力してください。", "error");
    return;
  }

  searchButton.disabled = true;
  downloadButton.disabled = true;
  fileErrors.hidden = true;
  setStatus(localSearchAvailable
    ? "exported フォルダーを検索しています..."
    : staticCorpus.length > 0
      ? "exported/ のファイルを検索しています..."
      : `検索中... 0 / ${selectedFiles.length} ファイル`);

  try {
    const { matches, errors } = localSearchAvailable
      ? { matches: await searchLocalCorpus(text, speaker), errors: [] }
      : staticCorpus.length > 0
        ? await searchStaticCorpus(text, speaker)
        : await searchFiles(text, speaker);
    resultOutput.value = matches.join("\n");
    if (resultCount) resultCount.textContent = `${matches.length.toLocaleString()} 件`;
    downloadButton.disabled = matches.length === 0;
    showFileErrors(errors);

    if (errors.length > 0) {
      setStatus(
        `${matches.length.toLocaleString()} 件見つかりました。${errors.length.toLocaleString()} ファイルを読み込めませんでした。`,
        "error",
      );
    } else {
      setStatus(
        matches.length > 0 ? "検索が完了しました。" : "一致する結果はありません。",
        matches.length > 0 ? "success" : "",
      );
    }
  } catch (error) {
    setStatus(`検索に失敗しました: ${error.message}`, "error");
  } finally {
    searchButton.disabled = false;
  }
});

initializeCorpus();

downloadButton.addEventListener("click", () => {
  const blob = new Blob([resultOutput.value], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "search-results.txt";
  link.click();
  URL.revokeObjectURL(url);
});
