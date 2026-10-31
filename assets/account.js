// 홈의 설정 버튼에서 구글 로그인과 로그아웃을 한 번에 처리합니다. 로그인 상태는 모든 강의 페이지에 공유됩니다.
import { signInWithGoogle, signOutUser, onUserChange } from "./firebase.js?v=20261031-account";

const toggle = document.getElementById("settings-toggle");
const panel = document.getElementById("settings");
const state = document.getElementById("account-state");
const action = document.getElementById("account-action");
let signedIn = false;

function openPanel(open) {
  panel.hidden = !open;
  toggle.setAttribute("aria-expanded", String(open));
}
if (location.hash === "#settings") openPanel(true);

toggle.addEventListener("click", () => {
  const open = panel.hidden;
  panel.hidden = !open;
  toggle.setAttribute("aria-expanded", String(open));
});

action.addEventListener("click", async () => {
  action.disabled = true;
  try {
    if (signedIn) await signOutUser();
    else await signInWithGoogle();
  } catch (err) {
    state.textContent = "처리하지 못했습니다. 잠시 후 다시 시도해 주세요.";
  } finally {
    action.disabled = false;
  }
});

onUserChange((user) => {
  signedIn = !!user;
  action.disabled = false;
  if (user) {
    state.textContent = `${user.displayName || user.email} 님으로 로그인되어 있습니다. 학습 기록이 모든 강의에 저장됩니다.`;
    action.textContent = "로그아웃";
  } else {
    state.textContent = "로그인하면 강의별 학습 완료·복습·메모를 저장하고 학습 이력을 볼 수 있습니다.";
    action.textContent = "구글로 로그인";
  }
});
