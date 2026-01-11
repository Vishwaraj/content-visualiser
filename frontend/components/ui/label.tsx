import * as React from "react";
import { cn } from "@/lib/utils";

export interface LabelProps
  extends React.LabelHTMLAttributes<HTMLLabelElement> {}

export const Label = React.forwardRef<HTMLLabelElement, LabelProps>(
  ({ className, ...props }, ref) => {
    return (
      <label
        ref={ref}
        className={cn(
          "text-xs font-medium text-zinc-700 dark:text-zinc-300",
          className,
        )}
        {...props}
      />
    );
  },
);

Label.displayName = "Label";


