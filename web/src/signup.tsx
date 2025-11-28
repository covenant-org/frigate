import React from "react";
import ReactDOM from "react-dom/client";
import "@/api";
import "./index.css";
import SignupPage from "./pages/SignupPage";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <SignupPage />
  </React.StrictMode>,
);
