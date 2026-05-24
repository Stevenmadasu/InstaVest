"use client";

import { initializeApp, getApps, getApp } from "firebase/app";
import { getDataConnect, connectDataConnectEmulator, DataConnect } from "firebase/data-connect";

const firebaseConfig = {
  apiKey: "AIzaSyAAOeEbl4xrtpalGuPIBmfV4yM823lRosg",
  authDomain: "instavest-46ad9.firebaseapp.com",
  projectId: "instavest-46ad9",
  storageBucket: "instavest-46ad9.firebasestorage.app",
  messagingSenderId: "522550963836",
  appId: "1:522550963836:web:961bf43f9c0419fd5163f9",
  measurementId: "G-3ZELMMTHTD"
};

const connectorConfig = {
  service: "instavest-db",         // Your Firebase Data Connect service ID
  location: "us-central1",          // Deployment region for Cloud SQL
  connector: "instavest-connector"  // Custom schema connector name
};

let dataConnectInstance: DataConnect | null = null;

export function getDataConnectInstance(): DataConnect | null {
  if (typeof window === "undefined") return null;
  if (!dataConnectInstance) {
    const app = getApps().length ? getApp() : initializeApp(firebaseConfig);
    dataConnectInstance = getDataConnect(app, connectorConfig);
    
    // Automatically connect to the local emulator in development environments
    if (process.env.NODE_ENV === "development") {
      connectDataConnectEmulator(dataConnectInstance, "localhost", 9399);
      console.log("[InstaVest] Connected to Firebase Data Connect Local Emulator (Port 9399) ✓");
    }
  }
  return dataConnectInstance;
}
