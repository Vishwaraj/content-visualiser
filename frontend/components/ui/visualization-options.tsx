"use client";

import React from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider"; // Assuming a slider component exists
import { Input } from "@/components/ui/input"; // Assuming an input component exists
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"; // Assuming a select component exists
import { cn } from "@/lib/utils";

export interface VisualizationOptions {
  complexity: "simple" | "balanced" | "detailed";
  max_depth: number;
  style: string; // Placeholder for future style presets
}

interface VisualizationOptionsPanelProps {
  options: VisualizationOptions;
  onOptionsChange: (newOptions: VisualizationOptions) => void;
  disabled?: boolean;
}

const complexityLevels = [
  { value: "simple", label: "Simple" },
  { value: "balanced", label: "Balanced" },
  { value: "detailed", label: "Detailed" },
];

const VisualizationOptionsPanel: React.FC<VisualizationOptionsPanelProps> = ({
  options,
  onOptionsChange,
  disabled = false,
}) => {
  const [isOpen, setIsOpen] = React.useState(false);

  const handleComplexityChange = (value: string) => {
    onOptionsChange({
      ...options,
      complexity: value as "simple" | "balanced" | "detailed",
    });
  };

  const handleMaxDepthChange = (value: number[]) => {
    onOptionsChange({ ...options, max_depth: value[0] });
  };

  const handleStyleChange = (value: string) => {
    onOptionsChange({ ...options, style: value });
  };

  return (
    <Card className={cn(disabled && "opacity-70")}>
      <CardHeader
        className="flex flex-row items-center justify-between space-y-0 p-4 cursor-pointer"
        onClick={() => setIsOpen(!isOpen)}
      >
        <CardTitle className="text-md">Advanced Options</CardTitle>
        <Button variant="ghost" size="icon" disabled={disabled}>
          {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </Button>
      </CardHeader>
      {isOpen && (
        <CardContent className="space-y-4 p-4 pt-0">
          <div>
            <Label htmlFor="complexity-select" className="mb-2 block">Complexity</Label>
            <Select
              value={options.complexity}
              onValueChange={handleComplexityChange}
              disabled={disabled}
            >
              <SelectTrigger id="complexity-select">
                <SelectValue placeholder="Select complexity" />
              </SelectTrigger>
              <SelectContent>
                {complexityLevels.map((level) => (
                  <SelectItem key={level.value} value={level.value}>
                    {level.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="max-depth-slider" className="mb-2 block">Max Depth ({options.max_depth})</Label>
            <Slider
              id="max-depth-slider"
              min={2}
              max={6}
              step={1}
              value={[options.max_depth]}
              onValueChange={handleMaxDepthChange}
              disabled={disabled}
              className="mt-2"
            />
            <Input
              type="number"
              min={2}
              max={6}
              value={options.max_depth}
              onChange={(e) => handleMaxDepthChange([Number(e.target.value)])}
              disabled={disabled}
              className="mt-2 w-full"
            />
          </div>

          {/* Optional: Style Presets */}
          {/*
          <div>
            <Label htmlFor="style-select" className="mb-2 block">Style Preset</Label>
            <Select
              value={options.style}
              onValueChange={handleStyleChange}
              disabled={disabled}
            >
              <SelectTrigger id="style-select">
                <SelectValue placeholder="Select style" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="default">Default</SelectItem>
                <SelectItem value="dark">Dark Theme</SelectItem>
                <SelectItem value="light">Light Theme</SelectItem>
              </SelectContent>
            </Select>
          </div>
          */}
        </CardContent>
      )}
    </Card>
  );
};

export default VisualizationOptionsPanel;