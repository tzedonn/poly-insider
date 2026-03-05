"use client";

import { CATEGORY_LABELS } from "@/lib/categories";
import type { Category, Filters } from "@/lib/types";

const CATEGORIES: Category[] = ["sports", "crypto", "updown", "elon", "other"];
const AMOUNT_PRESETS = [0, 100, 1_000, 10_000, 100_000];

function formatPreset(n: number): string {
  if (n === 0) return "$0";
  if (n >= 100_000) return "$100K";
  if (n >= 10_000) return "$10K";
  if (n >= 1_000) return "$1K";
  return `$${n}`;
}

interface FilterBarProps {
  filters: Filters;
  onFiltersChange: (filters: Filters) => void;
}

export function FilterBar({ filters, onFiltersChange }: FilterBarProps) {
  function toggleCategory(cat: Category) {
    onFiltersChange({
      ...filters,
      categories: { ...filters.categories, [cat]: !filters.categories[cat] },
    });
  }

  function setMinAmount(amount: number) {
    onFiltersChange({ ...filters, minAmount: amount });
  }

  return (
    <div className="flex flex-wrap items-center gap-3 rounded-lg bg-zinc-900 p-3">
      <span className="text-xs font-medium text-zinc-500 uppercase">
        Categories
      </span>
      {CATEGORIES.map((cat) => (
        <button
          key={cat}
          onClick={() => toggleCategory(cat)}
          className={`rounded-full px-3 py-1 text-sm font-medium transition-colors ${
            filters.categories[cat]
              ? "bg-indigo-600 text-white"
              : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700"
          }`}
        >
          {CATEGORY_LABELS[cat]}
        </button>
      ))}

      <div className="mx-2 h-5 w-px bg-zinc-700" />

      <span className="text-xs font-medium text-zinc-500 uppercase">Min</span>
      {AMOUNT_PRESETS.map((preset) => (
        <button
          key={preset}
          onClick={() => setMinAmount(preset)}
          className={`rounded-full px-3 py-1 text-sm font-medium transition-colors ${
            filters.minAmount === preset
              ? "bg-indigo-600 text-white"
              : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700"
          }`}
        >
          {formatPreset(preset)}
        </button>
      ))}
    </div>
  );
}
