'use client';

import dynamic from 'next/dynamic';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Header } from '@/components/layout/Header';
import Hero from '@/components/Hero';
//import { ShaderAnimation } from '@/components/ShaderAnimation';

// ✅ Lazy-loaded sections
const FeaturesSection = dynamic(
  () => import('@/components/FeaturesSection'),
  { ssr: false, loading: () => null }
);



const CTASection = dynamic(
  () => import('@/components/CTASection'),
  { ssr: false, loading: () => null }
);

// ✅ Hero wrapper
function HeroSection() {
  return (
    <section className="relative min-h-screen overflow-hidden">
      <Hero
        headline={{
          line1: "AI-Powered",
          line2: "Red Team Testing",
        }}
        subtitle="CognitoForge simulates intelligent adversarial attacks on your code and CI/CD pipelines."
        buttons={{
          primary: {
            text: "Get Started Free",
            onClick: () => (window.location.href = "/demo"),
          },
          secondary: {
            text: "Learn More",
            onClick: () => {
              const el = document.getElementById("features");
              el?.scrollIntoView({ behavior: "smooth" });
            },
          },
        }}
      />
    </section>
  );
}

// ✅ Default export
export default function HomePage() {
  const isDev = process.env.NODE_ENV === 'development';

  return (
    <div className="min-h-screen">

      {/* Disable heavy background in development */}
      {/* {!isDev && <ShaderAnimation />}  */}

      {/* Header */}
      <Header></Header>
      {/* Main content */}
      <main>
        <HeroSection />
        <FeaturesSection />
        
        <CTASection />
      </main>

      {/* Footer */}
      <footer className="py-12 text-center text-sm opacity-70">
        © 2025 CognitoForge. All rights reserved.
      </footer>
    </div>
  );
}
