// 공용 Firestore 연결 도우미. 빌드 없이 gstatic CDN의 ES 모듈을 직접 읽습니다.
import { firebaseConfig } from "./firebase-config.js";

const SDK = "https://www.gstatic.com/firebasejs/10.14.1";
let dbPromise = null;

export function getDb() {
  if (!dbPromise) {
    dbPromise = Promise.all([
      import(`${SDK}/firebase-app.js`),
      import(`${SDK}/firebase-firestore.js`)
    ]).then(([app, fs]) => ({
      db: fs.getFirestore(app.initializeApp(firebaseConfig)),
      fs
    }));
  }
  return dbPromise;
}
