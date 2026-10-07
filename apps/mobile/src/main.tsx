import React from "react";
import { createRoot } from "react-dom/client";
import Home from "../../web/src/app/page";
import { Providers } from "../../web/src/app/providers";
import "../../web/src/app/globals.css";
import "./mobile.css";
import { setupAndroid } from "./platform";

setupAndroid();
createRoot(document.getElementById("root")!).render(<React.StrictMode><Providers><Home /></Providers></React.StrictMode>);
