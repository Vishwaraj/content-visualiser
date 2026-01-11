import * as React from "react";
import { cn } from "@/lib/utils";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {}

export function Card({ className, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-zinc-200 bg-white/80 p-5 shadow-sm backdrop-blur-sm dark:border-zinc-800 dark:bg-zinc-900/70 sm:p-6",
        className,
      )}
      {...props}
    />
  );
}

export interface CardHeaderProps
  extends React.HTMLAttributes<HTMLDivElement> {}

export function CardHeader({ className, ...props }: CardHeaderProps) {
  return (
    <div className={cn("mb-3 flex flex-col gap-1", className)} {...props} />
  );
}

export interface CardTitleProps extends React.HTMLAttributes<HTMLDivElement> {}

export function CardTitle({ className, ...props }: CardTitleProps) {
  return (
    <div
      className={cn(
        "text-sm font-medium text-zinc-800 dark:text-zinc-200",
        className,
      )}
      {...props}
    />
  );
}

export interface CardContentProps
  extends React.HTMLAttributes<HTMLDivElement> {}

export function CardContent({ className, ...props }: CardContentProps) {
  return <div className={cn("mt-1", className)} {...props} />;
}


