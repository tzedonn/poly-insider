"use client";

import { useEffect, useRef, useState } from "react";
import { CATEGORY_LABELS, VISIBLE_CATEGORIES } from "@/lib/categories";
import type { Category, Filters } from "@/lib/types";

const AMOUNT_PRESETS: { label: string; value: number }[] = [
  { label: "None", value: 0 },
  { label: "$100", value: 100 },
  { label: "$1K", value: 1_000 },
  { label: "$10K", value: 10_000 },
  { label: "$100K", value: 100_000 },
];

function formatMinLabel(n: number): string {
  const preset = AMOUNT_PRESETS.find((p) => p.value === n);
  return preset ? preset.label : `$${n}`;
}

interface FilterBarProps {
  filters: Filters;
  onFiltersChange: (filters: Filters) => void;
}

function useClickOutside(ref: React.RefObject<HTMLElement | null>, onClose: () => void) {
  useEffect(() => {
    function handler(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [ref, onClose]);
}

export function FilterBar({ filters, onFiltersChange }: FilterBarProps) {
  const [catOpen, setCatOpen] = useState(false);
  const [amtOpen, setAmtOpen] = useState(false);
  const catRef = useRef<HTMLDivElement>(null);
  const amtRef = useRef<HTMLDivElement>(null);

  useClickOutside(catRef, () => setCatOpen(false));
  useClickOutside(amtRef, () => setAmtOpen(false));

  const selectedCount = VISIBLE_CATEGORIES.filter((c) => filters.categories[c]).length;

  function toggleCategory(cat: Category) {
    onFiltersChange({
      ...filters,
      categories: { ...filters.categories, [cat]: !filters.categories[cat] },
    });
  }

  function selectAll() {
    const updated = { ...filters.categories };
    for (const cat of VISIBLE_CATEGORIES) updated[cat] = true;
    onFiltersChange({ ...filters, categories: updated });
  }

  function clearAll() {
    const updated = { ...filters.categories };
    for (const cat of VISIBLE_CATEGORIES) updated[cat] = false;
    onFiltersChange({ ...filters, categories: updated });
  }

  function setMinAmount(value: number) {
    onFiltersChange({ ...filters, minAmount: value });
    setAmtOpen(false);
  }

  return (
    <div className="flex items-center gap-2">
      <div className="relative" ref={catRef}>
        <button
          onClick={() => { setCatOpen(!catOpen); setAmtOpen(false); }}
          className="flex items-center gap-1.5 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-sm text-zinc-300 hover:border-zinc-600 hover:bg-zinc-800 transition-colors"
        >
          Categories
          {selectedCount < VISIBLE_CATEGORIES.length && (
            <span className="rounded-full bg-blue-600 px-1.5 text-xs font-medium text-white">
              {selectedCount}
            </span>
          )}
          <svg className="h-3.5 w-3.5 text-zinc-500" viewBox="0 0 16 16" fill="currentColor">
            <path d="M4.5 6l3.5 4 3.5-4z" />
          </svg>
        </button>

        {catOpen && (
          <div className="absolute left-0 top-full z-50 mt-1 w-52 rounded-lg border border-zinc-700 bg-zinc-900 py-1 shadow-xl">
            <div className="flex items-center justify-between border-b border-zinc-800 px-3 py-1.5">
              <button onClick={selectAll} className="text-xs text-blue-400 hover:text-blue-300">
                Select All
              </button>
              <button onClick={clearAll} className="text-xs text-zinc-500 hover:text-zinc-400">
                Clear All
              </button>
            </div>
            {VISIBLE_CATEGORIES.map((cat) => (
              <label
                key={cat}
                className="flex cursor-pointer items-center gap-2.5 px-3 py-1.5 text-sm text-zinc-300 hover:bg-zinc-800/60"
              >
                <input
                  type="checkbox"
                  checked={filters.categories[cat]}
                  onChange={() => toggleCategory(cat)}
                  className="h-3.5 w-3.5 rounded border-zinc-600 bg-zinc-800 text-blue-500 accent-blue-500"
                />
                {CATEGORY_LABELS[cat]}
              </label>
            ))}
          </div>
        )}
      </div>

      <div className="relative" ref={amtRef}>
        <button
          onClick={() => { setAmtOpen(!amtOpen); setCatOpen(false); }}
          className="flex items-center gap-1.5 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-sm text-zinc-300 hover:border-zinc-600 hover:bg-zinc-800 transition-colors"
        >
          Min: {formatMinLabel(filters.minAmount)}
          <svg className="h-3.5 w-3.5 text-zinc-500" viewBox="0 0 16 16" fill="currentColor">
            <path d="M4.5 6l3.5 4 3.5-4z" />
          </svg>
        </button>

        {amtOpen && (
          <div className="absolute left-0 top-full z-50 mt-1 w-36 rounded-lg border border-zinc-700 bg-zinc-900 py-1 shadow-xl">
            {AMOUNT_PRESETS.map(({ label, value }) => (
              <button
                key={value}
                onClick={() => setMinAmount(value)}
                className={`flex w-full items-center gap-2 px-3 py-1.5 text-left text-sm transition-colors ${
                  filters.minAmount === value
                    ? "bg-zinc-800 text-blue-400"
                    : "text-zinc-300 hover:bg-zinc-800/60"
                }`}
              >
                <span className={`h-2 w-2 rounded-full border ${
                  filters.minAmount === value
                    ? "border-blue-500 bg-blue-500"
                    : "border-zinc-600"
                }`} />
                {label}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
