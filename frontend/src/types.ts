export interface Source {
  name: string;
  confidence: number;
  last_verified: string | null;
}

export interface GeoProperty {
  coordinates: number[];
  city: string;
  country: string;
  address: string;
}

export interface DigitalFootprint {
  emails: string[];
  phones: string[];
  social_accounts: string[];
  ip_addresses: string[];
}

export interface Metadata {
  sources: Source[];
  completeness: number;
  risk_level: string;
}

export interface Properties {
  geo?: GeoProperty | null;
  temporal?: {
    created?: string | null;
    updated?: string | null;
    observed_at?: string | null;
  } | null;
  digital_footprint?: DigitalFootprint | null;
  metadata?: Metadata | null;
  domain?: {
    registrar?: string;
    expires?: string;
    status?: string[];
    note?: string;
  } | null;
  company?: {
    edrpou?: string;
    legal_form?: string;
    address?: string;
    director?: string;
    contact_person?: string;
    phone?: string;
    email?: string;
    founders?: string;
    status?: string;
    registered_at?: string;
    activities?: string[];
    capital?: string;
    tax_status?: string;
    contacts?: string;
    website?: string;
    opendatabot_url?: string;
    images?: string[];
    socials?: { network: string; url: string }[];
    mentions?: { title: string; url: string }[];
    wikipedia?: string | null;
    legal_note?: string;
  } | null;
  document?: {
    url?: string;
    snippet?: string;
  } | null;
  [key: string]: unknown;
}

export interface Relation {
  target_id: string;
  type: string;
  confidence: number;
}

export interface UniversalEntity {
  id: number;
  entity_type: string;
  entity_id: string;
  entity_name: string;
  properties?: Properties | null;
  relations: Relation[];
  raw_data: Record<string, unknown>;
}

export interface TierInfo {
  name: string;
  entities_count: number;
  confidence: number;
  duration_ms: number;
  skipped: boolean;
  skip_reason?: string | null;
  error?: string | null;
}

export interface SearchResponse {
  query: string;
  source: string;
  query_type?: string;
  intent?: string;
  confidence?: number;
  results: UniversalEntity[];
  tiers?: TierInfo[];
  stopped_at?: string | null;
}

export type SourceName =
  | "shodan"
  | "google_maps"
  | "whois"
  | "telegram"
  | "company_registry"
  | "company_profile"
  | "web_search"
  | "social_browser";

export interface AnalyzeResponse {
  summary: string;
  cross_check: string;
  anomalies: string[];
}

export interface Workspace {
  id: number;
  name: string;
  description: string;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface GeocodeResult {
  lat: number;
  lng: number;
  address: string;
  city: string;
  country: string;
}

export interface ImageAnalysis {
  sha256: string;
  width: number;
  height: number;
  gps: { lat: number; lng: number } | null;
  datetime: string;
  device: string;
  address: { address: string; city: string; country: string } | null;
  ai_description: string;
  checks: { level: "error" | "warn"; text: string }[];
  vision: { status: "ok" | "mismatch" | "unchecked"; detail: string } | null;
  consistency: { status: "ok" | "mismatch" | "unchecked"; detail: string };
}

export interface AiProvider {
  name: string;
  label: string;
  local: boolean;
  configured: boolean;
  custom?: boolean;
  id?: number;
  kind?: string;
}

export interface AiProviderInput {
  name: string;
  kind: "openai" | "ollama" | "claude";
  base_url: string;
  api_key: string;
  model: string;
}
