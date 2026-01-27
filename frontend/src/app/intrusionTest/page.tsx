"use client";

import Link from "next/link";
import { useState } from "react";
import { motion } from "framer-motion";
import { Play, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function IntrusionTestPage() {
  const [repoUrl, setRepoUrl] = useState("https://github.com/OWASP/NodeGoat");
  const [analysisType, setAnalysisType] = useState("comprehensive");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    // Testing only: simulate loading
    setTimeout(() => {
      setIsLoading(false);
      alert(`Repo: ${repoUrl}\nAnalysis Type: ${analysisType}`);
    }, 1500);
  };

  return (
    <div className="min-h-screen p-10">
      {/* Top Website Name */}
      <div className="mb-10">
        <Link href="/" className="text-xl font-bold gradient-text">
          CognitoForge
        </Link>
      </div>

      {/* Form Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-2xl mx-auto"
      >
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold mb-4">
            Intrusion <span className="gradient-text">Test</span>
          </h1>
          <p className="text-muted-foreground">
            Enter repository URL and select analysis type for testing
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6 glass p-8 rounded-lg">
          {/* Repo URL */}
          <div>
            <label htmlFor="repoUrl" className="block text-sm font-medium mb-2">
              Repository URL
            </label>
            <input
              id="repoUrl"
              type="url"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              className="w-full px-4 py-3 bg-background border border-border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-colors"
              placeholder="https://github.com/username/repository"
              required
              disabled={isLoading}
            />
          </div>

          {/* Dropdown */}
          <div>
            <label
              htmlFor="analysisType"
              className="block text-sm font-medium mb-2"
            >
              Analysis Type
            </label>
            <select
              id="analysisType"
              value={analysisType}
              onChange={(e) => setAnalysisType(e.target.value)}
              className="w-full px-4 py-3 bg-background border border-border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-colors"
              required
              disabled={isLoading}
            >
              <option value="comprehensive">Comprehensive Security Audit</option>
              <option value="quick">Intrusion Test</option>
              <option value="cicd">Load Test ,Performance Test</option>
            </select>
          </div>

          {/* Submit Button */}
          <Button variant="purple" type="submit" size="lg" className="w-full" disabled={isLoading}>
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Initializing Analysis...
              </>
            ) : (
              <>
                <Play className="mr-2 h-4 w-4" />
                Start Intrusion Test
              </>
            )}
          </Button>
        </form>
      </motion.div>
    </div>
  );
}
