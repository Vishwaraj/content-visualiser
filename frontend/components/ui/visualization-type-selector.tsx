"use client";

import React from "react";
import { GitBranch, Network } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export type VisualizationType = "flowchart" | "mindmap";

interface VisualizationTypeSelectorProps {
  value: VisualizationType;
  onChange: (type: VisualizationType) => void;
  disabled?: boolean;
}

const visualizationOptions = [
  {
    id: "flowchart",
    name: "Flowchart",
    description: "Visualize sequential steps and decisions.",
    icon: GitBranch,
    colorClass: "bg-blue-500/20 text-blue-600 dark:text-blue-400",
  },
  {
    id: "mindmap",
    name: "Mindmap",
    description: "Explore hierarchical concepts and ideas.",
    icon: Network,
    colorClass: "bg-purple-500/20 text-purple-600 dark:text-purple-400",
  },
];

const VisualizationTypeSelector: React.FC<VisualizationTypeSelectorProps> = ({
  value,
  onChange,
  disabled = false,
}) => {
  return (
    <div
      className={cn(
        "grid gap-4 sm:grid-cols-2",
        disabled && "opacity-50 cursor-not-allowed",
      )}
    >
      {visualizationOptions.map((option) => (
        <Card
          key={option.id}
          className={cn(
            "relative cursor-pointer transition-all hover:shadow-lg",
            value === option.id
              ? "ring-2 ring-primary border-primary"
              : "border-border hover:border-primary/50",
          )}
          onClick={() => !disabled && onChange(option.id as VisualizationType)}
        >
          {value === option.id && (
            <span className="absolute -top-2 -right-2 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold animate-pulse">
              ✓
            </span>
          )}
          <CardContent className="flex items-center space-x-4 p-4">
            <div
              className={cn(
                "flex h-10 w-10 shrink-0 items-center justify-center rounded-lg",
                option.colorClass,
              )}
            >
              <option.icon className="h-5 w-5" />
            </div>
            <div className="flex-1">
              <h3 className="text-md font-semibold">{option.name}</h3>
              <p className="text-sm text-muted-foreground">
                {option.description}
              </p>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

export default VisualizationTypeSelector;
