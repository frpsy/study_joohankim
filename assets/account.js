// Account panel uses a fully prepared Auth SDK before user interaction.
import { getDb, signInWithGoogle, signOutUser, onUserChange } from "./firebase.js?v=20261101-auth-fix";

const toggle = document.getElementById("settings-toggle");
const panel = document.getElementById("settings");
const closeButton = document.getElementById("account-close");
const state = document.getElementById("account-state");
const action = document.getElementById("account-action");
const historyLink = document.getElementById("account-history");
let signedIn = false;
let generation = 0;
let authStarted = false;
let authReady = false;
let authAttempt = 0;

function openPanel(open) {
  panel.hidden = !open;
  toggle.setAttribute("aria-expanded", String(open));
  if (open) {
    ensureAuth();
    panel.scrollIntoView({ block:"nearest", behavior:"auto" });
  } else {
    toggle.focus?.({preventScroll:true});
  }
}
function syncHash() {
  if (location.hash === "#settings") openPanel(true);
}
toggle.addEventListener("click", () => openPanel(panel.hidden));
closeButton.addEventListener("click", () => openPanel(false));
window.addEventListener("hashchange", syncHash);

function errorMessage(err) {
  const code = err && err.code;
  if (code === "auth/popup-blocked" || code === "auth/operation-not-supported-in-this-environment")
    return "로그인 창이 차단되었습니다. Safari 또는 Chrome에서 사이트를 직접 열어 다시 시도해 주세요.";
  if (code === "auth/unauthorized-domain")
    return "로그인 허용 도메인 설정이 필요합니다. 관리자에게 알려 주세요.";
  if (code === "auth/popup-closed-by-user" || code === "auth/cancelled-popup-request")
    return "로그인이 취소되었습니다. 다시 시도해 주세요.";
  if (code === "auth/network-request-failed")
    return "인터넷 연결을 확인한 뒤 다시 시도해 주세요.";
  if (code === "auth/not-ready")
    return "로그인 준비 중입니다. 잠시 후 다시 눌러 주세요.";
  return "로그인에 실패했습니다. 브라우저와 네트워크를 확인한 뒤 다시 시도해 주세요.";
}
function setReady(user) {
  signedIn = !!user;
  authReady = true;
  action.disabled = false;
  action.textContent = user ? "로그아웃" : "Google로 로그인";
  toggle.textContent = "계정";
  toggle.setAttribute("aria-label", user ? "내 계정 관리" : "로그인 및 계정 관리");
  historyLink.hidden = !user;
  state.textContent = user
    ? (user.displayName || user.email || "사용자") + " · 로그인됨"
    : "학습·복습 완료 상태를 저장하려면 로그인하세요.";
}
action.addEventListener("click", () => {
  if (!authReady) { ensureAuth(true); return; }
  // No await before signInWithPopup. The browser sees a direct user gesture.
  const request = signedIn ? signOutUser() : signInWithGoogle();
  action.disabled = true;
  state.textContent = signedIn ? "로그아웃 중" : "Google 로그인 창 여는 중";
  Promise.resolve(request).catch(err => {
    state.textContent = errorMessage(err);
  }).finally(() => {
    action.disabled = false;
  });
});
function clearBadges() {
  document.querySelectorAll(".lecture .progress-badges").forEach(node => node.remove());
}
async function showBadges(user, token) {
  try {
    const { db, fs } = await getDb();
    const snap = await fs.getDocs(fs.collection(db, "studyUsers", user.uid, "progress"));
    if (token !== generation) return;
    clearBadges();
    snap.forEach(doc => {
      const data = doc.data();
      const card = document.querySelector(`.lecture[data-video-id="${CSS.escape(doc.id)}"]`);
      if (!card || !(data.study || data.review)) return;
      const box = document.createElement("div");
      box.className = "progress-badges";
      if (data.study) box.append(Object.assign(document.createElement("span"), {textContent:"학습 완료"}));
      if (data.review) box.append(Object.assign(document.createElement("span"), {textContent:"복습 완료"}));
      card.querySelector(".tags")?.after(box);
    });
  } catch {
    // Badges are optional and should never prevent reading the page.
  }
}
function ensureAuth(retry = false) {
  if (authStarted && !retry) return;
  const attempt = ++authAttempt;
  authStarted = true;
  authReady = false;
  action.disabled = true;
  action.textContent = "로그인 준비 중";
  state.textContent = "로그인 연결 중";
  // Slow SDK delivery must not leave the button permanently unavailable.
  if (typeof window.setTimeout === "function") window.setTimeout(() => {
    if (attempt !== authAttempt || authReady) return;
    action.disabled = false;
    action.textContent = "연결 다시 시도";
    state.textContent = "로그인 연결이 지연됩니다. 연결 상태를 확인한 뒤 다시 시도해 주세요.";
  }, 8000);
  let observer;
  try {
    observer = onUserChange(user => {
      if (attempt !== authAttempt) return;
      const token = ++generation;
      clearBadges();
      setReady(user);
      if (user) showBadges(user, token);
    });
  } catch (err) {
    observer = Promise.reject(err);
  }
  Promise.resolve(observer).catch(() => {
    if (attempt !== authAttempt) return;
    authStarted = false;
    authReady = false;
    action.disabled = false;
    action.textContent = "연결 다시 시도";
    state.textContent = "로그인 연결 실패 · 다시 시도해 주세요.";
  });
}
if (location.hash === "#settings") syncHash();
if (typeof window.requestIdleCallback === "function") {
  window.requestIdleCallback(ensureAuth, {timeout:1000});
} else {
  ensureAuth();
}
