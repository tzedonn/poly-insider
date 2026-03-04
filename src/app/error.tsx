"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-zinc-950 p-8 text-zinc-100">
      <h2 className="text-xl font-bold">Something went wrong</h2>
      <pre className="max-w-lg overflow-auto rounded bg-zinc-900 p-4 text-sm text-red-400">
        {error.message}
      </pre>
      <button
        onClick={reset}
        className="rounded bg-indigo-600 px-4 py-2 text-sm font-medium hover:bg-indigo-500"
      >
        Try again
      </button>
    </div>
  );
}
