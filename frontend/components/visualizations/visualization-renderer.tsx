"use client";

import React, { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';

interface VisualizationRendererProps {
  type: 'flowchart' | 'mindmap';
  content: string | null;
}

// Dynamically import MindmapRenderer and FlowchartRenderer to avoid SSR issues
// and ensure they are treated as client components.
const DynamicMindmapRenderer = dynamic(
  () => import('./mindmap-renderer'),
  {
    loading: () => <p className="text-sm text-zinc-500 dark:text-zinc-400">Loading Mindmap...</p>,
    ssr: false, // Ensure this component is not server-rendered
  }
);

const DynamicFlowchartRenderer = dynamic(
  () => import('./flowchart-renderer'),
  {
    loading: () => <p className="text-sm text-zinc-500 dark:text-zinc-400">Loading Flowchart...</p>,
    ssr: false, // Ensure this component is not server-rendered
  }
);

const VisualizationRenderer: React.FC<VisualizationRendererProps> = ({ type, content }) => {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (!isMounted || !content) {
    return (
      <p className="text-sm text-zinc-500 dark:text-zinc-400">
        Waiting for visualization data...
      </p>
    );
  }

  switch (type) {
    case 'flowchart':
      return <DynamicFlowchartRenderer mermaidCode={content} />;
    case 'mindmap':
      return <DynamicMindmapRenderer markdown={content} />;
    default:
      return (
        <p className="text-sm text-red-500 dark:text-red-400">
          Unsupported visualization type: {type}
        </p>
      );
  }
};

export default VisualizationRenderer;
