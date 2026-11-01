// Keep authentication and the database as separate, on-demand downloads.
// Navigation and unsigned-in reading never need the Firestore SDK.
import { firebaseConfig } from "./firebase-config.js";

const SDK = "https://www.gstatic.com/firebasejs/10.14.1";
let appReady = null;
let authReady = null;
let preparedAuth = null;
let dbReady = null;

function appInstance() {
  if (!appReady) {
    appReady = import(`${SDK}/firebase-app.js`)
      .then(mod => mod.getApps().length ? mod.getApp() : mod.initializeApp(firebaseConfig))
      .catch(error => { appReady = null; throw error; });
  }
  return appReady;
}
function authInstance() {
  if (!authReady) {
    authReady = Promise.all([appInstance(), import(`${SDK}/firebase-auth.js`)])
      .then(([app, auth]) => {
        preparedAuth = { auth, authObj: auth.getAuth(app) };
        return preparedAuth;
      })
      .catch(error => { authReady = null; preparedAuth = null; throw error; });
  }
  return authReady;
}
function dbInstance() {
  if (!dbReady) {
    dbReady = Promise.all([appInstance(), import(`${SDK}/firebase-firestore.js`)])
      .then(([app, fs]) => ({ fs, db: fs.getFirestore(app) }))
      .catch(error => { dbReady = null; throw error; });
  }
  return dbReady;
}

export async function getDb() { return dbInstance(); }
export function signInWithGoogle() {
  // Firebase SDK is prepared before the click. Invoke popup synchronously
  // within the user gesture to prevent mobile Safari popup blocking.
  if (!preparedAuth) return Promise.reject(Object.assign(new Error('Auth not ready'), { code: 'auth/not-ready' }));
  return preparedAuth.auth.signInWithPopup(preparedAuth.authObj, new preparedAuth.auth.GoogleAuthProvider());
}
export async function signOutUser() {
  const { auth, authObj } = await authInstance();
  return auth.signOut(authObj);
}
export async function onUserChange(callback) {
  const { auth, authObj } = await authInstance();
  return auth.onAuthStateChanged(authObj, callback);
}
