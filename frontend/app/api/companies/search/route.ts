import { NextRequest, NextResponse } from "next/server";

function resolveBackendBaseUrl(): string {
  const envValue = process.env.NEXT_PUBLIC_API_URL?.trim();
  return (envValue || "http://localhost:8100").replace(/\/$/, "");
}

export async function GET(request: NextRequest) {
  const backendBaseUrl = resolveBackendBaseUrl();
  const targetUrl = new URL("/companies/search", backendBaseUrl);

  request.nextUrl.searchParams.forEach((value, key) => {
    targetUrl.searchParams.set(key, value);
  });

  try {
    const response = await fetch(targetUrl.toString(), {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
      cache: "no-store",
    });

    const contentType = response.headers.get("content-type") ?? "application/json";
    const bodyText = await response.text();

    return new NextResponse(bodyText, {
      status: response.status,
      headers: {
        "content-type": contentType,
      },
    });
  } catch (error) {
    const detail =
      error instanceof Error ? error.message : "백엔드 검색 API 프록시에 실패했습니다.";

    return NextResponse.json(
      { detail },
      { status: 502 },
    );
  }
}
