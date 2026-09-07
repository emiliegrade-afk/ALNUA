/* Spark frontend — maquette AETHER, marque SPARK */

const state = {
  discussions: [{ id: 1, title: "Nouvelle discussion", messages: [] }],
  active: 0,
  deep: true,
  pc: true,
  attachment: null,
  busy: false,
};

const chatEl = document.getElementById("chat");
const discList = document.getElementById("discList");
const input = document.getElementById("input");
const attachChip = document.getElementById("attachChip");
const attachName = document.getElementById("attachName");
const statusRight = document.getElementById("statusRight");

function api() {
  return window.pywebview && window.pywebview.api;
}

function refreshStatus() {
  const pc = state.pc ? '<b class="ok">Actif</b>' : "<b>Off</b>";
  const ds = state.deep ? "<b>Connecté</b>" : "<b>Off</b>";
  statusRight.innerHTML = `Accès PC: ${pc} &nbsp;|&nbsp; Deep Search: ${ds}`;
}

function paintToggle(el, on, label) {
  el.dataset.on = on ? "1" : "0";
  el.classList.toggle("on", on);
  el.querySelector("span:last-child").innerHTML = `${label} <b>${on ? "ON" : "OFF"}</b>`;
}

function renderDiscussions() {
  discList.innerHTML = "";
  state.discussions.forEach((d, i) => {
    const row = document.createElement("div");
    row.className = "disc" + (i === state.active ? " active" : "");
    row.innerHTML = `<div class="bar"></div><span>${escapeHtml(d.title)}</span>`;
    row.onclick = () => {
      state.active = i;
      renderDiscussions();
      renderChat();
    };
    discList.appendChild(row);
  });
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderChat() {
  const d = state.discussions[state.active];
  chatEl.innerHTML = "";
  if (!d.messages.length) {
    const sys = document.createElement("div");
    sys.className = "sys";
    sys.textContent =
      "Bonjour Emilie. Spark est prêt — Deep Search et Accès PC activés. Joins un fichier ou pose ta question.";
    chatEl.appendChild(sys);
    return;
  }
  d.messages.forEach((m) => chatEl.appendChild(renderMessage(m)));
  chatEl.scrollTop = chatEl.scrollHeight;
}

function renderMessage(m) {
  if (m.role === "user") {
    const el = document.createElement("div");
    el.className = "msg-user";
    el.textContent = m.text;
    return el;
  }
  if (m.role === "system") {
    const el = document.createElement("div");
    el.className = "sys";
    el.textContent = m.text;
    return el;
  }
  const wrap = document.createElement("div");
  wrap.className = "msg-agent";
  const av = document.createElement("div");
  av.className = "avatar";
  av.textContent = "S";
  const body = document.createElement("div");
  body.className = "agent-body";
  if (m.thoughts && m.thoughts.length) {
    const th = document.createElement("div");
    th.className = "thought";
    th.innerHTML =
      "<strong>Thought Process:</strong>" +
      m.thoughts.map((t) => escapeHtml(t)).join("<br/>");
    body.appendChild(th);
  }
  const { text, codes } = splitCode(m.text || "");
  if (text) {
    const p = document.createElement("div");
    p.className = "agent-text";
    p.textContent = text;
    body.appendChild(p);
  }
  codes.forEach((code) => {
    const box = document.createElement("div");
    box.className = "code-wrap";
    box.innerHTML = `<div class="code-head"><button class="btn-copy" type="button">Copy</button></div>`;
    const pre = document.createElement("pre");
    pre.textContent = code;
    box.appendChild(pre);
    box.querySelector(".btn-copy").onclick = () => navigator.clipboard.writeText(code);
    body.appendChild(box);
  });
  wrap.appendChild(av);
  wrap.appendChild(body);
  return wrap;
}

function splitCode(raw) {
  if (!raw.includes("```")) return { text: stripMd(raw), codes: [] };
  const parts = raw.split("```");
  let text = "";
  const codes = [];
  parts.forEach((part, i) => {
    if (i % 2 === 0) text += stripMd(part);
    else {
      const lines = part.split("\n");
      if (/^[a-zA-Z0-9_+-]+$/.test(lines[0].trim())) lines.shift();
      codes.push(lines.join("\n").trim());
    }
  });
  return { text: text.trim(), codes };
}

function stripMd(t) {
  return t
    .replace(/\*{1,3}(.*?)\*{1,3}/gs, "$1")
    .replace(/_{1,2}(.*?)_{1,2}/gs, "$1")
    .replace(/`{1,3}(.*?)`{1,3}/gs, "$1")
    .replace(/^#{1,6}\s*/gm, "")
    .trim();
}

function current() {
  return state.discussions[state.active];
}

async function send() {
  const text = input.value.trim();
  if (!text || state.busy) return;
  input.value = "";
  const d = current();
  if (d.title === "Nouvelle discussion" || d.title.startsWith("Discussion ")) {
    d.title = text.slice(0, 40);
    renderDiscussions();
  }
  d.messages.push({ role: "user", text });
  const thoughts = ["> Spark analyse…"];
  if (state.deep) thoughts.push("> Deep Search IA en cours…");
  if (state.pc) thoughts.push("> Accès PC : contexte local autorisé");
  if (state.attachment) thoughts.push(`> Fichier joint : ${state.attachment.name}`);
  const pending = { role: "agent", text: "", thoughts };
  d.messages.push(pending);
  renderChat();
  state.busy = true;
  try {
    const a = api();
    let reply = "Spark hors ligne — Hub indisponible.";
    if (a && a.chat) {
      reply = await a.chat(text, state.deep, state.pc, state.attachment && state.attachment.path);
    }
    pending.text = reply || "";
    pending.thoughts = thoughts;
  } catch (e) {
    pending.text = "Erreur : " + (e && e.message ? e.message : String(e));
  }
  state.busy = false;
  renderChat();
}

document.getElementById("btnNew").onclick = () => {
  state.discussions.unshift({
    id: Date.now(),
    title: "Nouvelle discussion",
    messages: [],
  });
  state.active = 0;
  renderDiscussions();
  renderChat();
};

document.getElementById("togDeep").onclick = function () {
  state.deep = !state.deep;
  paintToggle(this, state.deep, "Deep Search");
  refreshStatus();
};
document.getElementById("togPc").onclick = function () {
  state.pc = !state.pc;
  paintToggle(this, state.pc, "PC Access");
  refreshStatus();
};

document.getElementById("btnSend").onclick = send;
input.addEventListener("keydown", (e) => {
  if (e.key === "Enter") send();
});

document.getElementById("btnAttach").onclick = async () => {
  const a = api();
  if (!a || !a.pick_file) return;
  const file = await a.pick_file();
  if (!file) return;
  state.attachment = file;
  attachName.textContent = file.name;
  attachChip.classList.add("show");
};

document.getElementById("btnMic").onclick = async () => {
  const a = api();
  if (a && a.toggle_mic) await a.toggle_mic();
};

window.addEventListener("pywebviewready", () => {
  renderDiscussions();
  renderChat();
  refreshStatus();
  input.focus();
});

// Fallback if opened without pywebview (dev browser)
renderDiscussions();
renderChat();
refreshStatus();
