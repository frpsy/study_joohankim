// 공통 학습 상태: 완료 버튼으로 즉시 저장하며 기존 계정별 기록을 보존한다.
import { getDb, onUserChange } from "./firebase.js?v=20261031-review";

function el(tag, attrs = {}, text = "") {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v;
    else node.setAttribute(k, v);
  }
  if (text) node.textContent = text;
  return node;
}
function setStatus(box, message, isError = false) {
  box.textContent = message;
  box.dataset.state = isError ? "error" : "ok";
}

function mount(root) {
  const lectureId = root.dataset.lecture;
  root.classList.add("study-progress");
  root.setAttribute("role", "group");
  root.setAttribute("aria-label", "학습 상태");
  const body = el("div", { class: "study-progress-body" });
  const status = el("p", { class: "study-progress-status", role: "status", "aria-live": "polite" });
  root.append(body, status);
  setStatus(status, "로그인 상태 확인 중");
  let generation = 0;

  function renderSignedOut() {
    body.replaceChildren(el("a", { class: "study-login-link", href: "../index.html#settings" }, "로그인 후 학습 기록"));
    setStatus(status, "");
  }

  async function renderSignedIn(user, token) {
    const current = () => token === generation;
    body.replaceChildren();
    setStatus(status, "학습 기록 불러오는 중");
    let db, fs, progressRef, progress;
    try {
      ({ db, fs } = await getDb());
      if (!current()) return;
      progressRef = fs.doc(db, "studyUsers", user.uid, "progress", lectureId);
      const saved = await fs.getDoc(progressRef);
      progress = saved.exists() ? saved.data() : {};
    } catch {
      if (!current()) return;
      setStatus(status, "기록을 불러오지 못했습니다. 다시 시도해 주세요.", true);
      const retry = el("button", { type: "button", class: "btn secondary" }, "다시 불러오기");
      retry.addEventListener("click", () => {
        if (current()) renderSignedIn(user, ++generation);
      });
      body.replaceChildren(retry);
      return;
    }
    if (!current()) return;
    setStatus(status, "");
    let busy = false;
    let pendingKind = null;
    const buttons = {};
    const names = { study: "학습 완료", review: "복습 완료" };
    function refresh() {
      for (const kind of Object.keys(names)) {
        const done = !!progress[kind];
        buttons[kind].textContent = busy && kind === pendingKind ? "저장 중…" : names[kind] + (done ? " ✓" : "");
        buttons[kind].dataset.complete = String(done);
        buttons[kind].setAttribute("aria-label", names[kind] + (done ? " 취소" : ""));
        buttons[kind].setAttribute("title", done ? "눌러서 완료 취소" : "눌러서 완료 기록");
        buttons[kind].disabled = busy;
      }
    }
    for (const kind of Object.keys(names)) {
      const button = el("button", { type: "button", class: "btn secondary study-status-button", id: "sp-" + kind });
      buttons[kind] = button;
      button.addEventListener("click", async () => {
        if (!current() || busy) return;
        busy = true;
        pendingKind = kind;
        root.setAttribute("aria-busy", "true");
        refresh();
        setStatus(status, "저장 중");
        const value = !progress[kind];
        try {
          const batch = fs.writeBatch(db);
          // Only write the chosen field; concurrent updates to the other status
          // must not be overwritten with this tab's potentially older value.
          batch.set(progressRef, { [kind]: value, updatedAt: fs.serverTimestamp() }, { merge: true });
          batch.set(fs.doc(fs.collection(db, "studyUsers", user.uid, "history")), {
            lectureId, kind, value, at: fs.serverTimestamp()
          });
          await batch.commit();
          if (!current()) return;
          progress = { ...progress, [kind]: value };
          setStatus(status, value ? names[kind] + " 저장됨" : names[kind] + " 취소됨");
        } catch {
          if (current()) setStatus(status, "저장하지 못했습니다. 다시 눌러 주세요.", true);
        } finally {
          if (current()) { busy = false; pendingKind = null; root.setAttribute("aria-busy", "false"); refresh(); }
        }
      });
    }
    body.replaceChildren(buttons.study, buttons.review);
    refresh();
  }

  function startAuth() {
    Promise.resolve(onUserChange(user => {
      const token = ++generation;
      root.setAttribute("aria-busy", "false");
      if (user) renderSignedIn(user, token);
      else renderSignedOut();
    })).catch(() => {
      body.replaceChildren(el("a", { class: "study-login-link", href: "../index.html#settings" }, "로그인 다시 연결"));
      setStatus(status, "로그인 상태를 확인하지 못했습니다.", true);
    });
  }
  if (typeof window !== "undefined" && typeof window.requestIdleCallback === "function") {
    window.requestIdleCallback(startAuth, { timeout: 1800 });
  } else startAuth();
}

const root = document.getElementById("study-progress");
if (root && root.dataset.lecture) mount(root);
