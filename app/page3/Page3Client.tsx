"use client";

import { ChainlitContext } from "@chainlit/react-client";
import { RecoilRoot } from "recoil";

interface Page3ClientProps {
  apiClient: any;
  children: React.ReactNode;
}

export default function Page3Client({ apiClient, children }: Page3ClientProps) {
  return (
    <ChainlitContext.Provider value={apiClient}>
      <RecoilRoot>
        {children}
      </RecoilRoot>
    </ChainlitContext.Provider>
  );
}