import { useEffect, useState, useCallback } from "react";
import { listEntities } from "../api";
import { useWorkspaceStore } from "../store/workspaceState";
import type { UniversalEntity } from "../types";
import EntityList from "./EntityList";
import EntityDetailCard, { DetailBlock } from "./EntityDetailCard";
import RelationBlock from "./RelationBlock";
import MiniMap from "./MiniMap";

function extractCompanies(entities: UniversalEntity[]): UniversalEntity[] {
  return entities.filter(
    (e) => e.entity_type === "company" || e.properties?.company
  );
}

export default function CompaniesView() {
  const currentId = useWorkspaceStore((s) => s.currentId);
  const [allEntities, setAllEntities] = useState<UniversalEntity[]>([]);
  const [companies, setCompanies] = useState<UniversalEntity[]>([]);
  const [selected, setSelected] = useState<UniversalEntity | null>(null);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [kvedFilter, setKvedFilter] = useState<string>("");

  useEffect(() => {
    if (currentId == null) {
      setAllEntities([]);
      setCompanies([]);
      setSelected(null);
      return;
    }
    setLoading(true);
    listEntities(currentId)
      .then((entities) => {
        setAllEntities(entities);
        setCompanies(extractCompanies(entities));
      })
      .finally(() => setLoading(false));
  }, [currentId]);

  const filteredCompanies = companies.filter((c) => {
    const company = c.properties?.company;
    if (statusFilter !== "all" && company?.status !== statusFilter) return false;
    if (kvedFilter && !company?.activities?.some((a) => a.toLowerCase().includes(kvedFilter.toLowerCase()))) return false;
    return true;
  });

  const handleSelect = useCallback((company: UniversalEntity) => {
    setSelected(company);
  }, []);

  const handleNavigate = useCallback((entity: UniversalEntity) => {
    if (entity.entity_type === "person") {
      setSelected(entity);
    }
  }, []);

  if (currentId == null) {
    return (
      <div className="empty-state">
        <h3>Створіть дослідження</h3>
        <p className="muted">Щоб побачити підприємства, створіть дослідження.</p>
      </div>
    );
  }

  const columns = [
    { key: "entity_name" as const, label: "Назва", render: (c: UniversalEntity) => <strong>{c.entity_name}</strong> },
    { key: "edrpou" as const, label: "ЄДРПОУ", render: (c: UniversalEntity) => c.properties?.company?.edrpou || "—" },
    { key: "status" as const, label: "Статус", render: (c: UniversalEntity) => c.properties?.company?.status || "—" },
    { key: "activities" as const, label: "КВЕД", render: (c: UniversalEntity) => c.properties?.company?.activities?.join("; ") || "—" },
    { key: "registered_at" as const, label: "Дата реєстрації", render: (c: UniversalEntity) => c.properties?.company?.registered_at || "—" },
    { key: "person_count" as const, label: "Пов'язаних осіб", render: (c: UniversalEntity) => String(c.relations?.length || 0) },
  ];

  const selectedCompany = selected?.properties?.company;
  const directorRel = selected?.relations?.find((r) => r.type === "director_of");
  const ownerRels = selected?.relations?.filter((r) => r.type === "owner_of" || r.type === "beneficiary_of");
  const contactRels = selected?.relations?.filter((r) => r.type === "phone_of" || r.type === "email_of");
  const otherPersonRels = selected?.relations?.filter(
    (r) => r.type !== "director_of" && r.type !== "owner_of" && r.type !== "beneficiary_of" && r.type !== "phone_of" && r.type !== "email_of"
  );

  return (
    <div className="master-detail">
      <EntityList
        items={filteredCompanies}
        columns={columns}
        onSelect={handleSelect}
        selectedId={selected?.entity_id}
        searchKeys={["entity_name" as const, "edrpou" as const]}
        searchPlaceholder="Пошук по назві або ЄДРПОУ..."
        emptyMessage="Підприємств не знайдено."
        filters={
          <div className="filter-row">
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="filter-select">
              <option value="all">Усі статуси</option>
              <option value="active">Активна</option>
              <option value="inactive">Припинена</option>
            </select>
            <input
              type="text"
              value={kvedFilter}
              onChange={(e) => setKvedFilter(e.target.value)}
              placeholder="Фільтр по КВЕД..."
              className="filter-input"
            />
          </div>
        }
      />

      {selected && selectedCompany && (
        <EntityDetailCard entity={selected}>
          <DetailBlock title="Юридична інформація">
            <div className="legal-grid">
              <div className="entity-row"><span className="muted">ЄДРПОУ: </span>{selectedCompany.edrpou || "—"}</div>
              <div className="entity-row"><span className="muted">Форма: </span>{selectedCompany.legal_form || "—"}</div>
              <div className="entity-row"><span className="muted">Адреса: </span>{selectedCompany.address || "—"}</div>
              <div className="entity-row"><span className="muted">Статус: </span>{selectedCompany.status || "—"}</div>
              <div className="entity-row"><span className="muted">КВЕД: </span>{selectedCompany.activities?.join("; ") || "—"}</div>
              <div className="entity-row"><span className="muted">Дата реєстрації: </span>{selectedCompany.registered_at || "—"}</div>
            </div>
          </DetailBlock>

          {selectedCompany.address && (
            <DetailBlock title="Розташування">
              <MiniMap address={selectedCompany.address} />
            </DetailBlock>
          )}

          <RelationBlock
            title="Керівництво"
            relations={directorRel ? [directorRel] : []}
            entities={allEntities}
            onNavigate={handleNavigate}
            renderExtra={(e) => <div className="muted">{e.properties?.company?.director || e.entity_name}</div>}
          />

          <RelationBlock
            title="Власники / бенефіціари"
            relations={ownerRels}
            entities={allEntities}
            onNavigate={handleNavigate}
          />

          <RelationBlock
            title="Контакти"
            relations={contactRels}
            entities={allEntities}
            onNavigate={handleNavigate}
          />

          <DetailBlock title="Фінанси">
            <div className="entity-row"><span className="muted">Статутний капітал: </span>{selectedCompany.capital || "—"}</div>
            <div className="entity-row"><span className="muted">Податковий статус: </span>{selectedCompany.tax_status || "—"}</div>
            <button className="btn-link">Відкрити у Фінансах</button>
          </DetailBlock>

          <RelationBlock
            title="Зв'язані особи"
            relations={otherPersonRels}
            entities={allEntities}
            onNavigate={handleNavigate}
          />
        </EntityDetailCard>
      )}

      {!selected && (
        <div className="detail-placeholder">
          <p className="muted">Оберіть підприємство зі списку для перегляду деталей.</p>
        </div>
      )}

      {loading && <div className="empty">Завантаження...</div>}
    </div>
  );
}
