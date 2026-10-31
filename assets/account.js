// 홈의 설정 버튼에서 구글 로그인과 로그아웃을 한 번에 처리합니다. 로그인 상태는 모든 강의 페이지에 공유됩니다.
// 로그인하면 홈의 강의 카드에 학습 완료·복습 완료 표시를 붙입니다.
import { getDb, signInWithGoogle, signOutUser, onUserChange } from "./firebase.js?v=20261031-review";

const toggle = document.getElementById("settings-toggle");
const panel = document.getElementById("settings");
const state = document.getElementById("account-state");
const action = document.getElementById("account-action");
const historyLink = document.getElementById("account-history");
let signedIn = false;

function openPanel(open) {
  panel.hidden = !open;
  toggle.setAttribute("aria-expanded", String(open));
  if (open) panel.scrollIntoView({ block: "start" });
}
function syncHash() {
  if (location.hash === "#settings") openPanel(true);
}
syncHash();
window.addEventListener("hashchange", syncHash);

toggle.addEventListener("click", () => openPanel(panel.hidden));

function errorMessage(err) {
  const code = err && err.code;
  if (code === "auth/popup-blocked") return "팝업이 차단되었습니다. 브라우저에서 팝업을 허용한 뒤 다시 눌러 주세요.";
  if (code === "auth/popup-closed-by-user" || code === "auth/cancelled-popup-request") return "로그인 창이 닫혔습니다. 다시 눌러 주세요.";
  if (code === "auth/network-request-failed") return "인터넷 연결을 확인한 뒤 다시 시도해 주세요.";
  return "처리하지 못했습니다. 잠시 후 다시 시도해 주세요.";
}

action.addEventListener("click", async () => {
  action.disabled = true;
  try {
    if (signedIn) await signOutUser();
    else await signInWithGoogle();
  } catch (err) {
    state.textContent = errorMessage(err);
  } finally {
    action.disabled = false;
  }
});

function clearBadges() {
  document.querySelectorAll(".lecture .progress-badges").forEach((node) => node.remove());
}

async function showBadges(user) {
  try {
    const { db, fs } = await getDb();
    const snap = await fs.getDocs(fs.collection(db, "studyUsers", user.uid, "progress"));
    clearBadges();
    snap.forEach((doc) => {
      const data = doc.data();
      const card = document.querySelector(`.lecture[data-video-id="${CSS.escape(doc.id)}"]`);
      if (!card || !(data.study || data.review)) return;
      const box = document.createElement("div");
      box.className = "progress-badges";
      if (data.study) box.append(Object.assign(document.createElement("span"), { textContent: "학습 완료" }));
      if (data.review) box.append(Object.assign(document.createElement("span"), { textContent: "복습 완료" }));
      card.querySelector(".tags")?.after(box);
    });
  } catch {
    // 표시는 보조 기능이므로 실패해도 홈 사용에는 영향이 없습니다.
  }
}

onUserChange((user) => {
  signedIn = !!user;
  action.disabled = false;
  historyLink.hidden = !user;
  if (user) {
    state.textContent = `${user.displayName || user.email} 님으로 로그인되어 있습니다. 학습 기록이 모든 강의에 저장됩니다.`;
    action.textContent = "로그아웃";
    showBadges(user);
  } else {
    state.textContent = "로그인하면 강의별 학습 완료·복습·메모를 저장하고 학습 이력을 볼 수 있습니다.";
    action.textContent = "구글로 로그인";
    clearBadges();
  }
});
