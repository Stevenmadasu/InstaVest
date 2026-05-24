import { initializeApp, getApps, getApp, FirebaseApp } from "firebase/app";
import { getAnalytics, Analytics, isSupported } from "firebase/analytics";
import { getDatabase, Database } from "firebase/database";

const firebaseConfig = {
  apiKey: "AIzaSyAAOeEbl4xrtpalGuPIBmfV4yM823lRosg",
  authDomain: "instavest-46ad9.firebaseapp.com",
  projectId: "instavest-46ad9",
  storageBucket: "instavest-46ad9.firebasestorage.app",
  messagingSenderId: "522550963836",
  appId: "1:522550963836:web:961bf43f9c0419fd5163f9",
  measurementId: "G-3ZELMMTHTD",
  databaseURL: "https://instavest-46ad9-default-rtdb.firebaseio.com"
};

let app: FirebaseApp | undefined;
let analytics: Analytics | undefined;
let db: Database | undefined;

export function initFirebase() {
  if (typeof window !== "undefined") {
    if (!getApps().length) {
      app = initializeApp(firebaseConfig);
      console.log("Firebase initialized successfully on client-side");
      
      db = getDatabase(app);
      
      isSupported().then((supported) => {
        if (supported && app) {
          analytics = getAnalytics(app);
        }
      }).catch(err => {
        console.warn("Firebase Analytics not supported in this environment:", err);
      });
    } else {
      app = getApp();
      db = getDatabase(app);
    }
  }
  return { app, analytics, db };
}

export { app, analytics, db };
