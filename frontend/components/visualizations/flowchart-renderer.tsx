"use client";

import React, { useEffect, useState } from "react";
import mermaid from "mermaid";

interface FlowchartRendererProps {
  mermaidCode: string;
}

const FlowchartRenderer: React.FC<FlowchartRendererProps> = ({ mermaidCode }) => {
  const [renderedSvg, setRenderedSvg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Initialize mermaid based on theme preference
    const initializeMermaid = () => {
      if (typeof window === "undefined") return;

      const media = window.matchMedia("(prefers-color-scheme: dark)");
      const isDark = media.matches;

      mermaid.initialize({
        startOnLoad: false,
        securityLevel: "loose",
        theme: "base",
        themeVariables: {
          background: "transparent",
          lineColor: isDark ? "#e5e7eb" : "#020617",
          primaryBorderColor: isDark ? "#f9fafb" : "#020617",
          secondaryBorderColor: isDark ? "#e5e7eb" : "#1e293b",
          tertiaryBorderColor: isDark ? "#d1d5db" : "#475569",
          primaryTextColor: isDark ? "#f9fafb" : "#020617",
          secondaryTextColor: isDark ? "#e5e7eb" : "#1f2937",
          tertiaryTextColor: isDark ? "#d1d5db" : "#4b5563",
          primaryColor: isDark ? "#111827" : "#e5e7eb",
          secondaryColor: isDark ? "#1f2937" : "#f3f4f6",
          tertiaryColor: isDark ? "#020617" : "#ffffff",
        },
      });
    };

    initializeMermaid(); // Initialize on mount
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    media.addEventListener("change", initializeMermaid); // Re-initialize on theme change

    return () => {
      media.removeEventListener("change", initializeMermaid);
    };
  }, []);

  useEffect(() => {
    if (!mermaidCode) {
      setRenderedSvg(null);
      setError(null);
      return;
    }

    let cancelled = false;

    async function renderDiagram() {
      try {
        const { svg } = await mermaid.render(
          `mermaid-diagram-${Date.now()}`,
          mermaidCode,
        );
        if (!cancelled) {
          setRenderedSvg(svg);
          setError(null);
        }
      } catch (err) {
        console.error("Mermaid render error", err);
        if (!cancelled) {
          setError(
            "We generated a diagram, but couldn't render it. Try asking again or refining the question.",
          );
          setRenderedSvg(null);
        }
      }
    }

    void renderDiagram();

    return () => {
      cancelled = true;
    };
  }, [mermaidCode]);

  if (error) {
    return (
      <p className="text-xs text-red-500 dark:text-red-400">{error}</p>
    );
  }

  if (!renderedSvg) {
    return (
      <p className="text-xs text-zinc-500 dark:text-zinc-400">
        Generating diagram...
      </p>
    );
  }

  return (
    // eslint-disable-next-line react/no-danger
    <div
      className="mermaid-svg [&_svg]:h-auto [&_svg]:w-full"
      dangerouslySetInnerHTML={{ __html: renderedSvg }}
    />
  );
};

export default FlowchartRenderer;
