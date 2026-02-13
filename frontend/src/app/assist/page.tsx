"use client";

import Link from "next/link";
import { useState } from "react";
import { Loader2, Database, SendHorizonal } from "lucide-react";
import { Button } from "@/components/ui/button";
import { FlickeringGrid } from "@/components/ui/flickering-grid";

export default function AssistPage() {
  const [repoUrl, setRepoUrl] = useState("");
  const [question, setQuestion] = useState("");

  const [repoLoading, setRepoLoading] = useState(false);
  const [isRepoReady, setIsRepoReady] = useState(false);

  const [askLoading, setAskLoading] = useState(false);
  const [response, setResponse] = useState<string | null>(null);

  const [error, setError] = useState("");

  // ✅ Step 1: Load repo / prepare assistant
  const handleRepoEnter = async () => {
    setError("");
    setResponse(null);

    if (!repoUrl.trim()) {
      setError("Please enter a repository URL.");
      return;
    }

    setRepoLoading(true);
    setIsRepoReady(false);

    // ✅ Simulated loading
    setTimeout(() => {
      setRepoLoading(false);
      setIsRepoReady(true);
    }, 2000);
  };

  // ✅ Step 2: Ask question
  const handleAsk = async () => {
    setError("");
    setResponse(null);

    if (!question.trim()) {
      setError("Please enter your question.");
      return;
    }

    setAskLoading(true);

    // ✅ Simulated response
    setTimeout(() => {
      setResponse(
        `✅ Response for: "${question}"\n\nRepo: ${repoUrl}\n\n📌 Sample Answer:\nThis is where your AI response will be shown.`
      );
      setAskLoading(false);
    }, 1500);
  };

  return (
    <div className="relative min-h-screen overflow-hidden p-10">
      {/* ✅ SAME BACKGROUND AS BEFORE */}
      <div className="absolute inset-0 z-0">
        <FlickeringGrid
          className="w-full h-full"
          squareSize={4}
          gridGap={6}
          flickerChance={0.06} // ✅ slow animation
         color="rgb(59, 130, 246)"   // blue-500
          maxOpacity={0.8}
        />
      </div>

      {/* ✅ PAGE CONTENT */}
      <div className="relative z-10">
        {/* Header */}
        <div className="mb-10">
          <Link href="/" className="text-xl font-bold gradient-text">
            CognitoForge
          </Link>
        </div>

        {/* Card */}
        <div className="max-w-2xl mx-auto glass p-8 rounded-lg">
          <h1 className="text-3xl font-bold mb-3">
            Code <span className="gradient-text">Assist</span>
          </h1>
          <p className="text-muted-foreground mb-8">
            Enter your repository URL, then ask questions to get code assistance.
          </p>

          {/* ✅ Repo URL Input (HIDE AFTER RESPONSE COMES) */}
          {!response && (
            <div className="space-y-3 mb-6">
              <label htmlFor="repoUrl" className="block text-sm font-medium">
                Repository URL
              </label>

              <input
                id="repoUrl"
                type="url"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                placeholder="https://github.com/username/repository"
                className="w-full px-4 py-3 bg-background border border-border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-colors"
                disabled={repoLoading || isRepoReady}
              />

              <Button
                variant="purple"
                size="lg"
                className="w-full"
                onClick={handleRepoEnter}
                disabled={repoLoading || isRepoReady}
              >
                {repoLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Loading Repository...
                  </>
                ) : isRepoReady ? (
                  <>
                    <Database className="mr-2 h-4 w-4" />
                    Repository Loaded ✅
                  </>
                ) : (
                  <>
                    <Database className="mr-2 h-4 w-4" />
                    Enter
                  </>
                )}
              </Button>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="mb-6 bg-red-900/20 border border-red-700/50 text-red-300 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          {/* ✅ Question Box after repo loaded */}
          {isRepoReady && (
            <div className="space-y-3 mt-8">
              <label htmlFor="question" className="block text-sm font-medium">
                Ask your question
              </label>

              <textarea
                id="question"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                rows={4}
                placeholder="Example: Explain the authentication flow of this repo..."
                className="w-full px-4 py-3 bg-background border border-border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-colors resize-none"
                disabled={askLoading}
              />

              <Button
                variant="purple"
                size="lg"
                className="w-full"
                onClick={handleAsk}
                disabled={askLoading}
              >
                {askLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating Response...
                  </>
                ) : (
                  <>
                    <SendHorizonal className="mr-2 h-4 w-4" />
                    Ask
                  </>
                )}
              </Button>
            </div>
          )}

          {/* ✅ Response */}
          {response && (
            <div className="mt-8 p-5 rounded-lg border border-[#614334]/40 bg-black/20">
              <h2 className="font-semibold mb-3 text-lg">Response</h2>
              <pre className="text-sm whitespace-pre-wrap text-muted-foreground">
                {response}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
