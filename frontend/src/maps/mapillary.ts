// Mapillary Graph API (free, requires a client token).
// Set VITE_MAPILLARY_TOKEN in frontend/.env to enable real 360° photos.

export const MAPILLARY_TOKEN: string =
  (import.meta.env.VITE_MAPILLARY_TOKEN as string | undefined) ?? "";

export interface MapillaryImage {
  id: string;
  lng: number;
  lat: number;
  width: number;
  height: number;
  captured_at: string;
  url: string;
}

export function hasMapillary(): boolean {
  return MAPILLARY_TOKEN.length > 0;
}

export async function fetchNearestImage(
  lng: number,
  lat: number
): Promise<MapillaryImage | null> {
  if (!hasMapillary()) return null;

  const params = new URLSearchParams({
    access_token: MAPILLARY_TOKEN,
    fields: "id,computed_geometry,width,height,captured_at",
    closeto: `${lng},${lat}`,
    radius: "1000",
    limit: "1",
  });
  const url = `https://graph.mapillary.com/images?${params.toString()}`;

  try {
    const res = await fetch(url);
    if (!res.ok) return null;
    const data = await res.json();
    const img = data?.data?.[0];
    if (!img?.id) return null;

    const coords = img.computed_geometry?.coordinates ?? [lng, lat];
    return {
      id: img.id,
      lng: coords[0],
      lat: coords[1],
      width: img.width ?? 0,
      height: img.height ?? 0,
      captured_at: img.captured_at ?? "",
      url: `https://images.mapillary.com/${img.id}/thumb-2048.jpg`,
    };
  } catch {
    return null;
  }
}

export function mapillaryViewerUrl(id: string): string {
  return `https://www.mapillary.com/app/?focus=photo&pKey=${id}`;
}
