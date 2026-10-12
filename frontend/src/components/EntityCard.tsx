import { useState } from "react";
import type { UniversalEntity } from "../types";
import MiniMap from "./MiniMap";

function LegalField({ label, value }: { label: string; value?: string }) {
  return (
    <div className="entity-row">
      <span className="muted">{label}: </span>
      {value ? value : <span className="not-found">інформація не знайдена</span>}
    </div>
  );
}

export default function EntityCard({ entity }: { entity: UniversalEntity }) {
  const [lightbox, setLightbox] = useState<string | null>(null);
  const geo = entity.properties?.geo;
  const meta = entity.properties?.metadata;
  const footprint = entity.properties?.digital_footprint;
  const domain = entity.properties?.domain;
  const company = entity.properties?.company;
  const document = entity.properties?.document;
  const source = meta?.sources?.[0];

  const hasGeo = geo && (geo.city || geo.country);
  const hasCoords = geo && geo.coordinates?.[0] !== 0;

  return (
    <article className="entity-card">
      <div className="entity-card-header">
        <span className="entity-type">{entity.entity_type}</span>
        <h2>{entity.entity_name}</h2>
      </div>

      {hasCoords && geo && (
        <MiniMap lng={geo.coordinates[0]} lat={geo.coordinates[1]} />
      )}

      {hasGeo && (
        <div className="entity-row">
          {[geo.city, geo.country].filter(Boolean).join(", ")}
        </div>
      )}

      {hasCoords && (
        <div className="entity-row muted">
          {geo.coordinates[1].toFixed(4)}, {geo.coordinates[0].toFixed(4)}
        </div>
      )}

      {footprint && footprint.ip_addresses.length > 0 && (
        <div className="entity-row muted">
          IP: {footprint.ip_addresses.join(", ")}
        </div>
      )}

      {domain && (
        <>
          {domain.registrar && (
            <div className="entity-row muted">Реєстратор: {domain.registrar}</div>
          )}
          {domain.expires && (
            <div className="entity-row muted">Діє до: {domain.expires.slice(0, 10)}</div>
          )}
          {domain.note && (
            <div className="entity-row warn">{domain.note}</div>
          )}
        </>
      )}

      {company && (
        <div className="company-block">
          {company.wikipedia && (
            <div className="company-section">
              <h4>Вікіпедія</h4>
              <a className="entity-row link" href={company.wikipedia} target="_blank" rel="noreferrer">
                {company.wikipedia}
              </a>
            </div>
          )}

          <div className="company-section">
            <h4>Юридична інформація</h4>
            <div className="legal-grid">
              <LegalField label="ЄДРПОУ" value={company.edrpou} />
              <LegalField label="Орг.-правова форма" value={company.legal_form} />
              <LegalField label="Юридична адреса" value={company.address} />
              <LegalField label="Директор" value={company.director} />
              <LegalField label="Контактна особа" value={company.contact_person} />
              <LegalField label="Телефон" value={company.phone} />
              <LegalField label="Email" value={company.email} />
              <LegalField label="Засновники" value={company.founders} />
              <LegalField label="Дата реєстрації" value={company.registered_at} />
              <LegalField label="Статус" value={company.status} />
              <LegalField label="КВЕД" value={company.activities?.join("; ") || ""} />
              <LegalField label="Статутний капітал" value={company.capital} />
              <LegalField label="Податковий статус" value={company.tax_status} />
              <LegalField label="Контакти" value={company.contacts} />
            </div>
            {company.legal_note && <div className="entity-row warn">{company.legal_note}</div>}
          </div>

          <div className="company-section">
            <h4>Посилання</h4>
            <div className="entity-row">
              <span className="muted">Сайт: </span>
              {company.website ? (
                <a className="link" href={company.website} target="_blank" rel="noreferrer">
                  {company.website}
                </a>
              ) : (
                <span className="not-found">інформація не знайдена</span>
              )}
            </div>
            <div className="entity-row">
              <span className="muted">OpenDataBot: </span>
              {company.opendatabot_url ? (
                <a className="link" href={company.opendatabot_url} target="_blank" rel="noreferrer">
                  {company.opendatabot_url}
                </a>
              ) : (
                <span className="not-found">інформація не знайдена</span>
              )}
            </div>
          </div>

          {company.socials && company.socials.length > 0 && (
            <div className="company-section">
              <h4>Соцмережі</h4>
              {company.socials.map((s, i) => (
                <a key={i} className="entity-row link" href={s.url} target="_blank" rel="noreferrer">
                  {s.network}
                </a>
              ))}
            </div>
          )}

          {company.mentions && company.mentions.length > 0 && (
            <div className="company-section">
              <h4>Згадки в мережі</h4>
              {company.mentions.map((m, i) => (
                <a key={i} className="entity-row link" href={m.url} target="_blank" rel="noreferrer">
                  {m.title}
                </a>
              ))}
            </div>
          )}

          {company.images && company.images.length > 0 && (
            <div className="company-section">
              <h4>Зображення</h4>
              <div className="images-row">
                {company.images.map((img, i) => (
                  <img
                    key={i}
                    src={img}
                    alt=""
                    className="thumb"
                    onClick={() => setLightbox(img)}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {lightbox && (
        <div className="lightbox" onClick={() => setLightbox(null)}>
          <button className="lightbox-close" onClick={() => setLightbox(null)}>✕</button>
          <img src={lightbox} alt="" onClick={(e) => e.stopPropagation()} />
        </div>
      )}

      {document && (
        <div className="company-section">
          {document.snippet && <div className="entity-row muted">{document.snippet}</div>}
          {document.url && (
            <a className="entity-row link" href={document.url} target="_blank" rel="noreferrer">
              {document.url}
            </a>
          )}
        </div>
      )}

      {source && (
        <div className="entity-row muted">
          Джерело: {source.name} · confidence {source.confidence}
        </div>
      )}
    </article>
  );
}
