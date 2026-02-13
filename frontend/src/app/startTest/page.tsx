"use client";

import Link from "next/link";
import { useState } from "react";
import { motion } from "framer-motion";
import { Activity, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { FlickeringGrid } from "@/components/ui/flickering-grid";

export default function StartTestPage() {
  const [repoUrl, setRepoUrl] = useState("");
  const [testType, setTestType] = useState("load");
  const [errors, setErrors] = useState<string[]>([]);
  const [touched, setTouched] = useState({ repoUrl: false, testType: false });
  const [isLoading, setIsLoading] = useState(false);

  const validateRepoUrl = (url: string) => {
    const valid = url.startsWith("https://github.com/");
    return valid
      ? { isValid: true, errors: [] }
      : { isValid: false, errors: ["Repository URL must be a GitHub link"] };
  };

  const validateTestType = (type: string) => {
    const validTypes = ["load", "performance", "stress", "spike"];
    return validTypes.includes(type)
      ? { isValid: true, errors: [] }
      : { isValid: false, errors: ["Test type is invalid"] };
  };

  const validateForm = () => {
    const repoValidation = validateRepoUrl(repoUrl);
    const testValidation = validateTestType(testType);

    const combinedErrors = [...repoValidation.errors, ...testValidation.errors];

    setErrors(combinedErrors);
    return combinedErrors.length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setTouched({ repoUrl: true, testType: true });

    if (!validateForm()) return;

    setIsLoading(true);

    // Testing purpose only (fake loading)
    setTimeout(() => {
      setIsLoading(false);
      alert(`Repo: ${repoUrl}\nTest Type: ${testType}`);
    }, 1500);
  };

  const handleRepoUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setRepoUrl(e.target.value);
    if (touched.repoUrl) validateForm();
  };

  const handleTestTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setTestType(e.target.value);
    if (touched.testType) validateForm();
  };

  return (
    <div className="relative min-h-screen overflow-hidden p-10">
      {/* ✅ Background */}
      <div className="absolute inset-0 z-0">
        <FlickeringGrid
          className="w-full h-full"
          squareSize={4}
          gridGap={6}
          flickerChance={0.05}
          color="rgb(59, 130, 246)"   // blue-500
          maxOpacity={0.8}
        />
      </div>

      {/* ✅ Page Content */}
      <div className="relative z-10">
        {/* Website Name */}
        <div className="mb-10">
          <Link href="/" className="text-xl font-bold gradient-text">
            CognitoForge
          </Link>
        </div>

        {/* Form */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-2xl mx-auto"
        >
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold mb-4">
              Load / <span className="gradient-text">Performance Testing</span>
            </h1>
            <p className="text-muted-foreground">
              Select test type and repository URL to simulate load/performance
              testing
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6 glass p-8 rounded-lg">
            {/* Errors */}
            {errors.length > 0 && (
              <div className="bg-red-900/20 border border-red-700/50 text-red-300 px-4 py-3 rounded-lg">
                <ul className="text-sm space-y-1">
                  {errors.map((error, index) => (
                    <li key={index}>• {error}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Repo URL */}
            <div>
              <label htmlFor="repoUrl" className="block text-sm font-medium mb-2">
                Repository URL
              </label>
              <input
                id="repoUrl"
                type="url"
                value={repoUrl}
                onChange={handleRepoUrlChange}
                onBlur={() => setTouched((prev) => ({ ...prev, repoUrl: true }))}
                className={`w-full px-4 py-3 bg-background border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-colors ${
                  touched.repoUrl && errors.some((e) => e.includes("Repository URL"))
                    ? "border-red-500"
                    : "border-border"
                }`}
                placeholder="https://github.com/username/repository"
                required
                disabled={isLoading}
              />
            </div>

            {/* Dropdown */}
            <div>
              <label htmlFor="testType" className="block text-sm font-medium mb-2">
                Test Type
              </label>
              <select
                id="testType"
                value={testType}
                onChange={handleTestTypeChange}
                onBlur={() => setTouched((prev) => ({ ...prev, testType: true }))}
                className={`w-full px-4 py-3 bg-background border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-colors ${
                  touched.testType && errors.some((e) => e.includes("Test type"))
                    ? "border-red-500"
                    : "border-border"
                }`}
                required
                disabled={isLoading}
              >
                <option value="load">Load Test</option>
                <option value="performance">Quick Test</option>
                <option value="stress">Stress Test</option>
                <option value="spike">Spike Test</option>

                {/* NOTE: these options had duplicate value="spike" earlier, kept same to avoid breaking */}
                <option value="spike">Capacity</option>
                <option value="spike">Soak</option>
              </select>
            </div>

            {/* Submit */}
            <Button
              variant="purple"
              type="submit"
              size="lg"
              className="w-full !bg-[#614334] hover:!bg-[#523628] !text-white"
              disabled={isLoading || errors.length > 0}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Running Test...
                </>
              ) : (
                <>
                  <Activity className="mr-2 h-4 w-4" />
                  Start Test
                </>
              )}
            </Button>
          </form>
        </motion.div>
      </div>
    </div>
  );
}
