import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";
import { initKeycloak } from "./lib/auth";

initKeycloak().then(() => {
  ReactDOM.createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
});
