import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const POLYMARKET_API = "https://data-api.polymarket.com/trades";

export async function GET() {
  try {
    const res = await fetch(`${POLYMARKET_API}?limit=100`, {
      cache: "no-store",
    });

    if (!res.ok) {
      return NextResponse.json(
        { error: "Upstream API error" },
        { status: res.status },
      );
    }

    const data = await res.json();
    return NextResponse.json(data, {
      headers: { "Cache-Control": "no-store, max-age=0" },
    });
  } catch {
    return NextResponse.json(
      { error: "Failed to fetch trades" },
      { status: 502 },
    );
  }
}
