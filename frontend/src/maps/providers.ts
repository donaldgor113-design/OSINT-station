import type { StyleSpecification } from "maplibre-gl";

export type ProviderKind = "map" | "image";

export interface MapProvider {
  id: string;
  label: string;
  kind: ProviderKind;
  // "mock" = needs an external service/key that isn't configured yet
  mock: boolean;
  detail: string;
  style?: StyleSpecification;
}

const osmStyle = {
  version: 8,
  sources: {
    osm: {
      type: "raster",
      tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
      tileSize: 256,
      attribution: "© OpenStreetMap contributors",
    },
  },
  layers: [{ id: "osm", type: "raster", source: "osm" }],
} as StyleSpecification;

const darkStyle = {
  version: 8,
  sources: {
    dark: {
      type: "raster",
      tiles: ["https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png"],
      tileSize: 256,
      attribution: "© OpenStreetMap contributors © CARTO",
    },
  },
  layers: [{ id: "dark", type: "raster", source: "dark" }],
} as StyleSpecification;

export const PROVIDERS: MapProvider[] = [
  {
    id: "osm",
    label: "OpenStreetMap",
    kind: "map",
    mock: false,
    detail: "Безкоштовна базова карта",
    style: osmStyle,
  },
  {
    id: "dark",
    label: "Темна (CARTO)",
    kind: "map",
    mock: false,
    detail: "Темна карта",
    style: darkStyle,
  },
  {
    id: "satellite",
    label: "Супутник (mock)",
    kind: "image",
    mock: true,
    detail: "Супутникові знімки — потребує ключ Maxar/Sentinel",
  },
  {
    id: "mapillary",
    label: "Mapillary (360°)",
    kind: "image",
    mock: true,
    detail: "Краудсорсні вуличні фото 360° — безкоштовний API",
  },
];

export function getProvider(id: string): MapProvider {
  return PROVIDERS.find((p) => p.id === id) ?? PROVIDERS[0];
}

export function getStyle(id: string): StyleSpecification {
  return getProvider(id).style ?? osmStyle;
}
