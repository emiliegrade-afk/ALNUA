"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ImageIcon, Upload } from "lucide-react";
import { cn } from "@/lib/utils";

interface ImageUploaderProps {
  file: File | null;
  onFileChange: (file: File | null) => void;
  disabled?: boolean;
  className?: string;
}

export function ImageUploader({
  file,
  onFileChange,
  disabled = false,
  className,
}: ImageUploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!file) {
      setPreviewUrl(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const acceptImage = useCallback(
    (candidate: File | undefined) => {
      if (!candidate || !candidate.type.startsWith("image/")) return;
      onFileChange(candidate);
    },
    [onFileChange]
  );

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    if (disabled) return;
    acceptImage(e.dataTransfer.files[0]);
  }

  return (
    <div className={cn("space-y-3", className)}>
      <div
        role="button"
        tabIndex={disabled ? -1 : 0}
        onClick={() => !disabled && inputRef.current?.click()}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            if (!disabled) inputRef.current?.click();
          }
        }}
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={cn(
          "relative flex min-h-[220px] cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed p-6 transition-colors outline-none focus-visible:ring-2 focus-visible:ring-copper/50",
          dragOver
            ? "border-copper bg-copper/10"
            : "border-copper/25 bg-obsidian-deep/40 hover:border-copper/45 hover:bg-copper/5",
          disabled && "pointer-events-none opacity-50"
        )}
      >
        {previewUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={previewUrl}
            alt="Aperçu"
            className="max-h-48 max-w-full rounded-lg object-contain"
          />
        ) : (
          <>
            <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full border border-copper/20 bg-copper/10">
              <Upload className="h-5 w-5 text-copper" />
            </div>
            <p className="text-sm font-medium text-ivory/90">
              Glisse ton logo ou identité visuelle ici
            </p>
            <p className="mt-1 text-xs text-titanium">
              PNG, JPG, WebP — ou clique pour parcourir
            </p>
          </>
        )}

        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          className="hidden"
          disabled={disabled}
          onChange={(e) => acceptImage(e.target.files?.[0])}
        />
      </div>

      {file && (
        <div className="flex items-center gap-2 text-xs text-titanium">
          <ImageIcon className="h-3.5 w-3.5 shrink-0 text-copper/70" />
          <span className="truncate">{file.name}</span>
          {!disabled && (
            <button
              type="button"
              onClick={() => onFileChange(null)}
              className="ml-auto text-copper-glow hover:underline"
            >
              Retirer
            </button>
          )}
        </div>
      )}
    </div>
  );
}
