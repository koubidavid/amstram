export const runtime = "edge";
export const revalidate = 0;

export async function GET() {
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  try {
    await fetch(`${API_BASE}/api/health`, { cache: "no-store" });
    return Response.json({ status: "ok" });
  } catch {
    return Response.json({ status: "error" }, { status: 500 });
  }
}
