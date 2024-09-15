'use client';

import React from "react";
import { Playground } from "./playground";
import { RecoilRoot } from "recoil";
import { ChainlitAPI, ChainlitContext } from "@chainlit/react-client";
import "./index.css";

// 「/chainlit」がなくても動いた。サンプルコードは「mount_chainlit(app=app, target="cl_app.py", path="/chainlit")」としているので「/chainlit」がついている。
// LLM は FastAPI 形式にしないと動かない
const CHAINLIT_SERVER = "https://d206-34-173-37-132.ngrok-free.app/chainlit";

const apiClient = new ChainlitAPI(CHAINLIT_SERVER, "webapp");

export default function Page3Client() {
  return (
    <React.StrictMode>
      <ChainlitContext.Provider value={apiClient}>
        <RecoilRoot>
          <Playground />
        </RecoilRoot>
      </ChainlitContext.Provider>
    </React.StrictMode>
  );
}