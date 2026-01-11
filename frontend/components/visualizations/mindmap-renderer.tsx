"use client";

import React, { useRef, useEffect } from 'react';
import { Markmap, loadCSS, loadJS } from 'markmap-view';
import { Transformer } from 'markmap-lib';
import { Toolbar } from 'markmap-toolbar';

// Register global styles for markmap-toolbar
// This is typically handled by importing the CSS directly, but for dynamic toolbar creation,
// we might need to ensure its styles are loaded.
// For Next.js, this is usually handled in globals.css or a dedicated layout CSS file.
// If not already globally available, ensure markmap-toolbar styles are injected.

interface MindmapRendererProps {
  markdown: string;
}

const transformer = new Transformer();

const MindmapRenderer: React.FC<MindmapRendererProps> = ({ markdown }) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const toolbarRef = useRef<HTMLDivElement>(null);
  const markmapRef = useRef<Markmap | null>(null);

  useEffect(() => {
    // Load markmap-view CSS and JS
    const { styles, scripts } = transformer.getAssets();
    if (styles) loadCSS(styles);
    if (scripts) loadJS(scripts, { getMarkmap: () => Markmap });

    if (svgRef.current) {
      const { root, features } = transformer.transform(markdown);

      // Ensure Markmap instance exists
      if (!markmapRef.current) {
        markmapRef.current = Markmap.create(svgRef.current, {
          duration: 500,
          maxWidth: 300,    
          initialExpandLevel: 2,
          // Example of depth-based color coding (customize as needed)
          // You might need to adjust this based on the actual Markmap API for colors
          color: (node) => {
            const colors = ['#a0a0a0', '#a1c1d1', '#a2d2c1', '#b2e2d1', '#c3f3e1', '#d4g4f1']; // Example colors
            const depth = node.level || 0;
            return colors[depth % colors.length];
          },
        }, root);
      } else {
        // If Markmap instance already exists, just update data
        markmapRef.current.setData(root);
        markmapRef.current.fit();
      }

      // Initialize toolbar if not already present
      if (toolbarRef.current && !toolbarRef.current.hasChildNodes()) {
        const toolbar = Toolbar.create(markmapRef.current);
        toolbarRef.current.appendChild(toolbar.el);
      }
    }

    // Cleanup function
    return () => {
      // Destroy Markmap instance
      if (markmapRef.current) {
        markmapRef.current.destroy();
        markmapRef.current = null;
      }
      // Remove toolbar if it was added
      if (toolbarRef.current) {
        toolbarRef.current.innerHTML = ''; // Clear toolbar content
      }
    };
  }, [markdown]);

  return (
    <div className="mindmap-container w-full h-full relative">
      <svg ref={svgRef} className="markmap w-full h-full"></svg>
      <div ref={toolbarRef} className="markmap-toolbar absolute bottom-4 right-4 z-10"></div>
    </div>
  );
};

export default MindmapRenderer;
