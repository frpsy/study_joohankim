// 공용 Firebase 연결 도우미. 빌드 없이 gstatic CDN의 ES 모듈을 직접 읽습니다.
// 데이터는 studyUsers/{uid}/... 아래에만 저장하며, 본인 외에는 읽고 쓸 수 없습니다(firestore.rules).
import { firebaseConfig } from "./firebase-config.js";

const SDK = "https://www.gstatic.com/firebasejs/10.14.1";
let ready = null;

function load() {
  if (!ready) {
    ready = Promise.all([
      import(`${SDK}/firebase-app.js`),
      import(`${SDK}/firebase-firestore.js`),
      import(`${SDK}/firebase-auth.js`)
    ]).then(([appMod, fs, auth]) => {
      const app = appMod.initializeApp(firebaseConfig);
      return {
        app,
        fs,
        auth,
        db: fs.getFirestore(app),
        authObj: auth.getAuth(app)
      };
    });
  }
  return ready;
}

// Firestore 인스턴스와 SDK 함수 묶음
export async function getDb() {
  const { db, fs } = await load();
  return { db, fs };
}

// 구글 로그인 (팝업)
export async function signInWithGoogle() {
  const { auth, authObj } = await load();
  const provider = new auth.GoogleAuthProvider();
  return auth.signInWithPopup(authObj, provider);
}

export async function signOutUser() {
  const { auth, authObj } = await load();
  return auth.signOut(authObj);
}

// 로그인 상태가 바뀔 때마다 콜백 (user 또는 null)
export async function onUserChange(callback) {
  const { auth, authObj } = await load();
  return auth.onAuthStateChanged(authObj, callback);
}
