(() => {
  const STORAGE_KEY = "cosmic_reconciliation_mobile_v1";
  const $ = (id) => document.getElementById(id);
  const state = { memories: load() };

  function load() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      const parsed = raw ? JSON.parse(raw) : [];
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }

  function save() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state.memories));
    refreshStats();
  }

  function id() {
    return globalThis.crypto?.randomUUID?.() || `m-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  }

  function tokenize(text) {
    return new Set(String(text).toLowerCase().match(/[a-z0-9_'-]{2,}/g) || []);
  }

  function score(memory, query) {
    const q = tokenize(query);
    if (!q.size) return memory.importance || 0;
    const haystack = tokenize(`${memory.content} ${(memory.tags || []).join(" ")}`);
    let hits = 0;
    q.forEach((token) => { if (haystack.has(token)) hits += 1; });
    const lexical = hits / q.size;
    return lexical * 0.85 + Number(memory.importance || 0) * 0.15;
  }

  function humanDate(value) {
    try { return new Date(value).toLocaleString(); } catch { return value || ""; }
  }

  function renderMemories(target, memories, query = "") {
    target.innerHTML = "";
    if (!memories.length) {
      target.innerHTML = `<div class="empty">No memories here yet.</div>`;
      return;
    }
    memories.forEach((memory) => {
      const node = $("memoryTemplate").content.firstElementChild.cloneNode(true);
      node.dataset.id = memory.id;
      const numericScore = query ? score(memory, query) : Number(memory.importance || 0);
      node.querySelector(".score").textContent = query ? `match ${numericScore.toFixed(3)}` : `importance ${Number(memory.importance || 0).toFixed(2)}`;
      node.querySelector("time").textContent = humanDate(memory.createdAt);
      node.querySelector(".memory-content").textContent = memory.content;
      const tagRow = node.querySelector(".tag-row");
      (memory.tags || []).forEach((tag) => {
        const pill = document.createElement("span");
        pill.className = "tag";
        pill.textContent = tag;
        tagRow.appendChild(pill);
      });
      node.querySelector(".copy").addEventListener("click", async () => {
        try {
          await navigator.clipboard.writeText(memory.content);
          node.querySelector(".copy").textContent = "Copied";
          setTimeout(() => { node.querySelector(".copy").textContent = "Copy"; }, 1000);
        } catch {
          alert(memory.content);
        }
      });
      node.querySelector(".delete").addEventListener("click", () => {
        if (!confirm("Delete this local memory?")) return;
        state.memories = state.memories.filter((item) => item.id !== memory.id);
        save();
        search();
        renderVault();
      });
      target.appendChild(node);
    });
  }

  function search() {
    const query = $("search").value.trim();
    const ranked = [...state.memories]
      .map((memory) => ({ memory, value: score(memory, query) }))
      .filter((row) => !query || row.value > 0.02)
      .sort((a, b) => b.value - a.value || String(b.memory.createdAt).localeCompare(String(a.memory.createdAt)))
      .slice(0, 40)
      .map((row) => row.memory);
    renderMemories($("results"), ranked, query);
  }

  function remember() {
    const content = $("content").value.trim();
    if (!content) {
      $("saveStatus").textContent = "Write a memory first.";
      return;
    }
    const tags = $("tags").value.split(",").map((tag) => tag.trim()).filter(Boolean);
    state.memories.unshift({
      id: id(),
      content,
      tags,
      importance: Number($("importance").value),
      createdAt: new Date().toISOString(),
      source: "cosmic-memory-mobile"
    });
    save();
    $("content").value = "";
    $("tags").value = "";
    $("saveStatus").textContent = "Memory stored locally.";
    renderVault();
    setTimeout(() => { $("saveStatus").textContent = ""; }, 1800);
  }

  function refreshStats() {
    $("memoryCount").textContent = state.memories.length;
    const tags = new Set(state.memories.flatMap((memory) => memory.tags || []));
    $("tagCount").textContent = tags.size;
  }

  function renderVault() {
    renderMemories($("allMemories"), [...state.memories].sort((a, b) => String(b.createdAt).localeCompare(String(a.createdAt))));
  }

  function exportJson() {
    const payload = {
      format: "cosmic-reconciliation-mobile-export",
      version: 1,
      exportedAt: new Date().toISOString(),
      memories: state.memories
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `cosmic-memory-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  async function importJson(file) {
    if (!file) return;
    try {
      const payload = JSON.parse(await file.text());
      const incoming = Array.isArray(payload) ? payload : payload.memories;
      if (!Array.isArray(incoming)) throw new Error("No memories array found");
      const normalized = incoming
        .filter((item) => item && typeof item.content === "string")
        .map((item) => ({
          id: item.id || item.memory_id || id(),
          content: item.content,
          tags: Array.isArray(item.tags) ? item.tags : [],
          importance: Math.max(0, Math.min(1, Number(item.importance ?? 0.5))),
          createdAt: item.createdAt || item.created_at || new Date().toISOString(),
          source: item.source || "import"
        }));
      const byId = new Map(state.memories.map((item) => [item.id, item]));
      normalized.forEach((item) => byId.set(item.id, item));
      state.memories = [...byId.values()].sort((a, b) => String(b.createdAt).localeCompare(String(a.createdAt)));
      save();
      renderVault();
      search();
      alert(`Imported ${normalized.length} memories.`);
    } catch (error) {
      alert(`Import failed: ${error.message}`);
    }
  }

  document.querySelectorAll(".tab").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((tab) => tab.classList.toggle("active", tab === button));
      document.querySelectorAll(".panel").forEach((panel) => panel.classList.toggle("active", panel.id === button.dataset.tab));
      if (button.dataset.tab === "vault") renderVault();
    });
  });

  $("importance").addEventListener("input", () => { $("importanceValue").value = Number($("importance").value).toFixed(2); });
  $("saveBtn").addEventListener("click", remember);
  $("searchBtn").addEventListener("click", search);
  $("search").addEventListener("input", search);
  $("exportBtn").addEventListener("click", exportJson);
  $("importInput").addEventListener("change", (event) => importJson(event.target.files?.[0]));
  $("clearBtn").addEventListener("click", () => {
    if (!confirm("Erase every memory stored locally in this mobile app? This cannot be undone unless you exported a copy.")) return;
    state.memories = [];
    save();
    renderVault();
    search();
  });

  refreshStats();
  search();
  renderVault();
})();
