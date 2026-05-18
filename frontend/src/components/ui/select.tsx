"use client";

import * as SelectPrimitive from "@radix-ui/react-select";
import { Check, ChevronDown } from "lucide-react";
import { forwardRef } from "react";
import { cn } from "@/lib/utils";

export const Select = SelectPrimitive.Root;
export const SelectValue = SelectPrimitive.Value;
export const SelectGroup = SelectPrimitive.Group;

export const SelectTrigger = forwardRef<
  React.ElementRef<typeof SelectPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Trigger>
>(({ className, children, ...props }, ref) => (
  <SelectPrimitive.Trigger
    ref={ref}
    className={cn(
      "flex h-11 w-full items-center justify-between gap-2 rounded-[12px] border border-[var(--color-border)] bg-paper-white px-3 text-[15px] text-ink",
      "will-change-transform transition-[border-color,box-shadow,transform] duration-[var(--motion-micro)] ease-[var(--ease-out)] active:scale-[0.99]",
      "focus-visible:border-generated focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)]",
      "disabled:cursor-not-allowed disabled:opacity-60 disabled:active:scale-100",
      "tap-target",
      className,
    )}
    {...props}
  >
    {children}
    <SelectPrimitive.Icon asChild>
      <ChevronDown className="size-4 text-ink-subtle" strokeWidth={2} />
    </SelectPrimitive.Icon>
  </SelectPrimitive.Trigger>
));
SelectTrigger.displayName = "SelectTrigger";

export const SelectContent = forwardRef<
  React.ElementRef<typeof SelectPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Content>
>(({ className, children, position = "popper", ...props }, ref) => (
  <SelectPrimitive.Portal>
    <SelectPrimitive.Content
      ref={ref}
      position={position}
      className={cn(
        "z-50 min-w-[var(--radix-select-trigger-width)] overflow-hidden rounded-[12px] border border-[var(--color-border)] bg-paper-white shadow-lg",
        "origin-[var(--radix-select-content-transform-origin)] will-change-transform",
        "transition-[opacity,transform] duration-[var(--motion-enter)] ease-[var(--ease-out)]",
        "data-[state=closed]:opacity-0 data-[state=closed]:scale-[0.96]",
        "data-[state=open]:opacity-100 data-[state=open]:scale-100",
        "data-[state=closed]:duration-[var(--motion-exit)]",
        position === "popper" && "translate-y-1",
        className,
      )}
      {...props}
    >
      <SelectPrimitive.Viewport className="p-1">{children}</SelectPrimitive.Viewport>
    </SelectPrimitive.Content>
  </SelectPrimitive.Portal>
));
SelectContent.displayName = "SelectContent";

export const SelectItem = forwardRef<
  React.ElementRef<typeof SelectPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Item>
>(({ className, children, ...props }, ref) => (
  <SelectPrimitive.Item
    ref={ref}
    className={cn(
      "relative flex cursor-pointer select-none items-center rounded-[8px] py-1.5 pl-8 pr-3 text-sm text-ink outline-none",
      "focus:bg-paper-warm",
      "data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
      className,
    )}
    {...props}
  >
    <span className="absolute left-2 flex size-4 items-center justify-center">
      <SelectPrimitive.ItemIndicator>
        <Check className="size-4 text-validated" strokeWidth={2.5} />
      </SelectPrimitive.ItemIndicator>
    </span>
    <SelectPrimitive.ItemText>{children}</SelectPrimitive.ItemText>
  </SelectPrimitive.Item>
));
SelectItem.displayName = "SelectItem";
