/* eslint-disable @next/next/no-img-element */
"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import VisualizationRenderer from "@/components/visualizations/visualization-renderer";
import VisualizationTypeSelector, {
  VisualizationType,
} from "@/components/ui/visualization-type-selector"; // Import the selector

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function Home() {
  const [question, setQuestion] = useState("");
  const [visualizationType, setVisualizationType] = useState<VisualizationType>('flowchart'); // Default to flowchart
  const [visualizationContent, setVisualizationContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);

  const isDisabled = useMemo(
    () => loading || question.trim().length === 0,
    [loading, question],
  );

  function safeToastMessage(
    raw:
      | string
      | { message?: string }
      | { detail?: { message?: string } }
      | undefined
      | null,
    fallback: string,
  ): string {
    if (!raw) return fallback;
    if (typeof raw === "string") {
      const trimmed = raw.trim();
      return trimmed.length > 0 ? trimmed : fallback;
    }
    // Try nested message fields, otherwise fall back.
    // We explicitly avoid stringifying whole objects like [object Object].
    // eslint-disable-next-line @typescript-eslint/no-unnecessary-type-assertion
    const withMessage = raw as { message?: string; detail?: { message?: string } };
    const msg =
      withMessage.message ?? withMessage.detail?.message ?? undefined;
    if (typeof msg === "string" && msg.trim().length > 0) {
      return msg.trim();
    }
    return fallback;
  }

  // Poll backend for async visualization job status
  useEffect(() => {
    if (!jobId) return;

    let cancelled = false;
    let pollTimeout: ReturnType<typeof setTimeout> | null = null;
    let pollCount = 0;

    const poll = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/visualize/${jobId}`);
        const data = (await res.json()) as {
          job_id?: string;
          status?: string;
          visualization_type?: VisualizationType; // New field for visualization type
          content?: string; // New field for visualization content
          error?: string;
          detail?: { message?: string };
        };

        if (!res.ok) {
          const msg = safeToastMessage(
            data?.detail,
            "Error while checking diagram generation status.",
          );
          if (!cancelled) {
            setToast(msg);
            setLoading(false);
            setJobId(null);
          }
          return;
        }

        const status = data.status;
        if (!status) {
          if (!cancelled) {
            setToast("Unexpected response while checking job status.");
            setLoading(false);
            setJobId(null);
          }
          return;
        }

        if (status === "succeeded" && data.content && data.visualization_type) {
          if (!cancelled) {
            setVisualizationType(data.visualization_type);
            setVisualizationContent(data.content);
            setLoading(false);
            setJobId(null);
          }
          return;
        }

        if (status === "failed") {
          if (!cancelled) {
            let msg = safeToastMessage(
              data.error,
              "Diagram generation failed.",
            );
            // Patch: for suspected Gemini error spam, show a generic error
            if (
              typeof data.error === "string" &&
              (data.error.length > 260 || /\b(reason|trace|exception|status|google|genai|llm|response|status code|stack)/i.test(data.error))
            ) {
              msg = "Something went wrong with the AI backend. Our team has been notified. Please try again later.";
            }
            setToast(msg);
            setLoading(false);
            setJobId(null);
          }
          return;
        }

        // pending / running: schedule another poll with exponential backoff
        pollCount++;
        const pollInterval = Math.min(1000 * 1.5 ** pollCount, 15000);
        pollTimeout = setTimeout(poll, pollInterval);

      } catch (err) {
        console.error("Error while polling visualization job", err);
        if (!cancelled) {
          setToast("Error while checking diagram generation status.");
          setLoading(false);
          setJobId(null);
        }
      }
    };

    void poll();

    return () => {
      cancelled = true;
      if (pollTimeout) {
        clearTimeout(pollTimeout);
      }
    };
  }, [jobId]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setError(null);
    setToast(null);
    setVisualizationContent(null);

    try {
      const response = await fetch(`${API_BASE_URL}/visualize`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: question.trim(),
          visualization_type: visualizationType, // Send selected type to backend
        }),
      });

      const data = (await response.json()) as
        | { job_id?: string; status?: string }
        | { detail?: { message?: string } };

      if (!response.ok) {
        const msg = safeToastMessage(
          (data as { detail?: { message?: string } }).detail,
          "Something went wrong talking to the API.",
        );
        setToast(msg);
        setLoading(false);
        return;
      }

      if (!("job_id" in data) || !data.job_id) {
        throw new Error("Backend did not return a job id.");
      }

      setJobId(data.job_id);
    } catch (err) {
      console.error(err);
      setError(
        "Something went wrong talking to the API. Make sure the backend is running on the expected URL.",
      );
      setLoading(false);
    }
  }

  function handleExampleClick(example: string) {
    setQuestion(example);
  }

  return (
    <div className="flex min-h-screen justify-center bg-zinc-50 px-4 py-10 text-zinc-900 dark:bg-black dark:text-zinc-50">
      <main className="flex w-full max-w-4xl flex-col gap-8">
        <header className="flex flex-col gap-2">
          <div className="flex items-center gap-3">
            <span className="inline-flex h-9 w-9 items-center justify-center rounded-xl bg-zinc-900 text-sm font-semibold text-zinc-50 shadow-sm dark:bg-zinc-100 dark:text-zinc-900">
              CV
            </span>
            <div>
              <h1 className="text-xl font-semibold tracking-tight sm:text-2xl">
                Concept Visualizer
              </h1>
              <p className="text-sm text-zinc-600 dark:text-zinc-400">
                Ask &ldquo;How does X work?&rdquo; and get an auto-generated
                diagram from Gemini.
              </p>
            </div>
          </div>
        </header>

        <Card>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <Label htmlFor="question" className="text-xs uppercase tracking-wide">
              How does it work?
            </Label>
            {/* Visualization Type Selector */}
            <VisualizationTypeSelector
              value={visualizationType}
              onChange={setVisualizationType}
              disabled={loading}
            />
            <Textarea
              id="question"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder='For example: "How does OAuth 2.0 authorization code flow work?"'
              rows={4}
            />

            <div className="flex flex-col-reverse items-start justify-between gap-3 sm:flex-row sm:items-center">
              <div className="flex flex-wrap gap-2 text-xs">
                <span className="text-zinc-500 dark:text-zinc-400">
                  Try:
                </span>
                {[
                  "How does a URL request travel through a web app?",
                  "How does Kafka message consumption work end-to-end?",
                  "How does Git branching and merging work?",
                ].map((example) => (
                  <button
                    key={example}
                    type="button"
                    onClick={() => handleExampleClick(example)}
                    className="rounded-full border border-zinc-200 bg-zinc-50 px-3 py-1 text-[11px] text-zinc-700 transition hover:border-zinc-300 hover:bg-white dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:border-zinc-600 dark:hover:bg-zinc-800"
                  >
                    {example}
                  </button>
                ))}
              </div>

              <Button type="submit" disabled={isDisabled}>
                {loading ? "Generating diagram..." : "Generate diagram"}
              </Button>
            </div>
          </form>
        </Card>

        <section className="flex flex-col gap-4">
          {error && (
            <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800 dark:border-red-900 dark:bg-red-950/60 dark:text-red-200">
              {error}
            </div>
          )}

          {!visualizationContent && !loading && !error && (
            <div className="rounded-2xl border border-dashed border-zinc-300 bg-zinc-100/70 px-4 py-10 text-center text-sm text-zinc-500 dark:border-zinc-700 dark:bg-zinc-900/40 dark:text-zinc-400">
              Your diagram will appear here once you ask a question.
            </div>
          )}

          {loading && (
            <div className="rounded-2xl border border-zinc-200 bg-white/80 px-4 py-6 text-sm text-zinc-600 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/70 dark:text-zinc-300">
              <div className="flex items-center gap-3">
                <span className="inline-flex h-4 w-4 animate-spin rounded-full border-2 border-zinc-400 border-t-transparent dark:border-zinc-500 dark:border-t-transparent" />
                <span>
                  Generating a diagram with Gemini… this may take a few seconds.
                </span>
              </div>
            </div>
          )}

          {visualizationContent && (
            <div className="grid gap-4 lg:grid-cols-[minmax(0,2fr),minmax(0,1fr)]">
              <Card>
                <CardHeader>
                  <CardTitle>Diagram</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="rounded-xl border border-zinc-100 bg-zinc-50 p-3 dark:border-zinc-800 dark:bg-zinc-950">
                    <VisualizationRenderer
                      type={visualizationType}
                      content={visualizationContent}
                    />
                  </div>
                </CardContent>
              </Card>

              <Card className="text-xs">
                <CardHeader>
                  <CardTitle>{visualizationType === 'flowchart' ? 'Mermaid' : 'Markdown'} source</CardTitle>
                </CardHeader>
                <CardContent>
                  <pre className="rounded-xl bg-zinc-950/95 p-3 text-[11px] text-zinc-100 dark:bg-zinc-950">
                    <code>{visualizationContent}</code>
                  </pre>
                </CardContent>
              </Card>
            </div>
          )}
        </section>
      </main>

      {toast && (
        <div className="fixed inset-x-0 bottom-4 z-50 flex justify-center px-4">
          <div className="flex max-w-md items-center gap-3 rounded-full border border-amber-300 bg-amber-50/95 px-4 py-2 text-sm text-amber-900 shadow-lg backdrop-blur dark:border-amber-500/80 dark:bg-amber-900/90 dark:text-amber-50">
            <span>{toast}</span>
            <button
              type="button"
              onClick={() => setToast(null)}
              className="ml-auto text-xs text-amber-700 hover:text-amber-900 dark:text-amber-200 dark:hover:text-amber-50"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
