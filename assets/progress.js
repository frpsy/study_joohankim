// 강의별 학습 기록: 학습 완료, 복습 완료, 이력. 구글 로그인 후 본인 데이터만 저장한다.
import { getDb, onUserChange } from "./firebase.js?v=20261031-review";

const TITLE = "학습 기록";

function el(tag, attrs = {}, text = "") {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v;
    else if (k === "for") node.htmlFor = v;
    else node.setAttribute(k, v);
  }
  if (text) node.textContent = text;
  return node;
}

function setStatus(box, message, isError = false) {
  box.textContent = message;
  box.dataset.state = isError ? "error" : "ok";
  if (isError && box.parentElement) box.parentElement.open = true;
}

async function mount(root) {
  const lectureId = root.dataset.lecture;
  root.classList.add("study-progress");
  const disclosure = el("details", { class: "study-record-disclosure" });
  const summary = el("summary", {}, TITLE);
  disclosure.append(summary);
  root.append(disclosure);
  function showSummary(progress = {}) {
    const marks = [];
    if (progress.study) marks.push("학습 완료");
    if (progress.review) marks.push("복습 완료");
    summary.textContent = marks.length ? `${TITLE} · ${marks.join(" · ")}` : TITLE;
  }
  const body = el("div", { class: "study-progress-body" });
  const status = el("p", { class: "study-progress-status", role: "status", "aria-live": "polite" });
  disclosure.append(body, status);

  function renderSignedOut() {
    body.replaceChildren(
      el("a", { class: "btn", href: "../index.html#settings" }, "홈에서 로그인하기")
    );
    setStatus(status, "");
  }

  let generation = 0;

  async function renderSignedIn(user, token) {
    const current = () => token === generation;
    body.replaceChildren();
    setStatus(status, "학습 기록 불러오는 중");
    // An anonymous reader never downloads Firestore. Authenticated records load
    // only when a valid session has been resolved.
    let db, fs;
    try {
      ({ db, fs } = await getDb());
    } catch {
      if (current()) setStatus(status, "학습 기록 연결 실패 · 다시 열어 주세요.", true);
      return;
    }
    if (!current()) return;
    const progressRef = fs.doc(db, "studyUsers", user.uid, "progress", lectureId);
    let progress = {};
    try {
      const p = await fs.getDoc(progressRef);
      progress = p.exists() ? p.data() : {};
    } catch (err) {
      if (!current()) return;
      setStatus(status, "저장된 기록을 읽지 못했습니다. ‘다시 불러오기’를 눌러 주세요.", true);
      const retry = el("button", { type: "button", class: "btn" }, "다시 불러오기");
      retry.addEventListener("click", () => {
        if (current()) renderSignedIn(user, ++generation);
      });
      body.replaceChildren(retry);
      return;
    }
    if (!current()) return;
    setStatus(status, "");

    showSummary(progress);
    const studyBox = el("input", { type: "checkbox", id: "sp-study" });
    studyBox.checked = !!progress.study;
    const reviewBox = el("input", { type: "checkbox", id: "sp-review" });
    reviewBox.checked = !!progress.review;
    const save = el("button", { type: "button", class: "btn" }, "저장");
    const historyLink = el("a", { class: "btn secondary", href: "../study-history.html" }, "학습 이력 보기");
    const settings = el("a", { class: "btn secondary", href: "../index.html#settings" }, "계정 설정");

    body.replaceChildren(
      el("label", { class: "study-check", for: "sp-study" }, ""),
      el("label", { class: "study-check", for: "sp-review" }, ""),
      el("div", { class: "actions" }, ""),
    );
    // 체크박스는 label 안에 넣어 접근성을 맞춘다
    const labels = body.querySelectorAll("label.study-check");
    labels[0].replaceChildren(studyBox, document.createTextNode(" 학습 완료"));
    labels[1].replaceChildren(reviewBox, document.createTextNode(" 복습 완료"));
    const actions = body.querySelector(".actions");
    actions.replaceChildren(save, historyLink, settings);

    save.addEventListener("click", async () => {
      if (!current()) return;
      save.disabled = true;
      setStatus(status, "저장 중");
      try {
        const nextProgress = { study: studyBox.checked, review: reviewBox.checked, updatedAt: fs.serverTimestamp() };
        const batch = fs.writeBatch(db);
        batch.set(progressRef, nextProgress, { merge: true });
        const log = [];
        if (!!progress.study !== studyBox.checked) log.push(["study", studyBox.checked]);
        if (!!progress.review !== reviewBox.checked) log.push(["review", reviewBox.checked]);
        for (const [kind, value] of log) {
          batch.set(fs.doc(fs.collection(db, "studyUsers", user.uid, "history")), {
            lectureId, kind, value, at: fs.serverTimestamp()
          });
        }
        await batch.commit();
        if (!current()) return;
        progress = { study: nextProgress.study, review: nextProgress.review };
        showSummary(progress);
        setStatus(status, "저장 완료");
      } catch (err) {
        if (!current()) return;
        setStatus(status, "저장에 실패했습니다. 잠시 후 다시 시도해 주세요.", true);
      } finally {
        if (current()) save.disabled = false;
      }
    });

  }

  let authStarted = false;
  function startAuth() {
    if (authStarted) return;
    authStarted = true;
    Promise.resolve(onUserChange((user) => {
      const token = ++generation;
      if (!user) disclosure.open = false;
      showSummary();
      if (user) renderSignedIn(user, token);
      else renderSignedOut();
    })).catch(() => {
      authStarted = false;
      setStatus(status, "로그인 상태 확인 실패 · 기록을 다시 열어 주세요.", true);
    });
  }
  disclosure.addEventListener("toggle", () => {
    if (disclosure.open) startAuth();
  });
  if (typeof window !== "undefined" && typeof window.requestIdleCallback === "function") {
    window.requestIdleCallback(startAuth, { timeout: 1800 });
  } else {
    startAuth();
  }
}

const root = document.getElementById("study-progress");
if (root && root.dataset.lecture) mount(root);
