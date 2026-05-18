"use client";

import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { forwardRef } from "react";
import { cn } from "@/lib/utils";

export const Dialog = DialogPrimitive.Root;
export const DialogTrigger = DialogPrimitive.Trigger;
export const DialogClose = DialogPrimitive.Close;
export const DialogPortal = DialogPrimitive.Portal;

export const DialogOverlay = forwardRef<
  React.ElementRef<typeof DialogPrimitive.Overlay>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Overlay>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Overlay
    ref={ref}
    className={cn(
      "fixed inset-0 z-50 bg-ink/40",
      "transition-opacity duration-[var(--motion-enter)] ease-[var(--ease-out)]",
      "data-[state=closed]:opacity-0 data-[state=open]:opacity-100",
      "data-[state=closed]:duration-[var(--motion-exit)]",
      className,
    )}
    {...props}
  />
));
DialogOverlay.displayName = "DialogOverlay";

export const DialogContent = forwardRef<
  React.ElementRef<typeof DialogPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content>
>(({ className, children, ...props }, ref) => (
  <DialogPortal>
    <DialogOverlay />
    <DialogPrimitive.Content
      ref={ref}
      className={cn(
        "fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2",
        "rounded-[20px] border border-[var(--color-border)] bg-paper-white p-5 shadow-lg",
        "origin-center will-change-transform",
        "transition-[opacity,transform] duration-[var(--motion-enter)] ease-[var(--ease-out)]",
        "data-[state=closed]:opacity-0 data-[state=closed]:scale-[0.96]",
        "data-[state=open]:opacity-100 data-[state=open]:scale-100",
        "data-[state=closed]:duration-[var(--motion-exit)]",
        "focus-visible:outline-none",
        className,
      )}
      {...props}
    >
      {children}
      <DialogPrimitive.Close
        aria-label="Close"
        className="absolute right-2 top-2 inline-flex tap-target items-center justify-center rounded-[10px] text-ink-subtle will-change-transform transition-[background-color,color,transform] duration-[var(--motion-micro)] ease-[var(--ease-out)] hover:bg-paper-warm hover:text-ink active:scale-[0.94] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)]"
      >
        <X className="size-4" strokeWidth={2} />
      </DialogPrimitive.Close>
    </DialogPrimitive.Content>
  </DialogPortal>
));
DialogContent.displayName = "DialogContent";

export const DialogHeader = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("flex flex-col gap-1 pr-8", className)} {...props} />
);

export const DialogTitle = forwardRef<
  React.ElementRef<typeof DialogPrimitive.Title>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Title>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Title
    ref={ref}
    className={cn("font-display text-xl text-ink", className)}
    {...props}
  />
));
DialogTitle.displayName = "DialogTitle";

export const DialogDescription = forwardRef<
  React.ElementRef<typeof DialogPrimitive.Description>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Description>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Description
    ref={ref}
    className={cn("text-sm text-ink-muted", className)}
    {...props}
  />
));
DialogDescription.displayName = "DialogDescription";
