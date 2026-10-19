import { useEffect, useState, useCallback } from "react";
import { listEntities } from "../api";
import { useWorkspaceStore } from "../store/workspaceState";
import type { UniversalEntity } from "../types";
import EntityList from "./EntityList";
import EntityDetailCard, { DetailBlock } from "./EntityDetailCard";
import RelationBlock from "./RelationBlock";

interface PersonData {
  entity: UniversalEntity;
  fullName: string;
  roles: string[];
  phone: string;
  email: string;
  address: string;
  companyCount: number;
}

function extractPeople(entities: UniversalEntity[]): PersonData[] {
  const people: PersonData[] = [];
  const seen = new Set<string>();

  function addPerson(name: string, role: string, entity: UniversalEntity) {
    const key = name.toLowerCase();
    if (!name) return;
    if (seen.has(key)) {
      const existing = people.find((p) => p.fullName.toLowerCase() === key);
      if (existing && !existing.roles.includes(role)) existing.roles.push(role);
      return;
    }
    seen.add(key);
    const company = entity.properties?.company;
    const geo = entity.properties?.geo;
    const footprint = entity.properties?.digital_footprint;
    people.push({
      entity,
      fullName: name,
      roles: [role],
      phone: company?.phone || footprint?.phones?.[0] || "",
      email: company?.email || footprint?.emails?.[0] || "",
      address: company?.address || geo?.address || "",
      companyCount: 0,
    });
  }

  for (const e of entities) {
    if (e.entity_type === "person") {
      addPerson(e.entity_name, "Особа", e);
    }
    const company = e.properties?.company;
    if (company) {
      if (company.director) addPerson(company.director, "Директор", e);
      if (company.contact_person) addPerson(company.contact_person, "Контактна особа", e);
      if (company.founders) {
        company.founders.split(/[,;]/).forEach((f) => {
          addPerson(f.trim(), "Засновник", e);
        });
      }
    }
  }

  for (const p of people) {
    p.companyCount = entities.filter((e) => {
      const c = e.properties?.company;
      if (!c) return false;
      return [c.director, c.contact_person, c.founders].some(
        (f) => f && f.toLowerCase().includes(p.fullName.toLowerCase())
      );
    }).length;
  }

  return people;
}

export default function PeopleView() {
  const currentId = useWorkspaceStore((s) => s.currentId);
  const [allEntities, setAllEntities] = useState<UniversalEntity[]>([]);
  const [people, setPeople] = useState<PersonData[]>([]);
  const [selected, setSelected] = useState<PersonData | null>(null);
  const [loading, setLoading] = useState(false);
  const [roleFilter, setRoleFilter] = useState<string>("all");

  useEffect(() => {
    if (currentId == null) {
      setAllEntities([]);
      setPeople([]);
      setSelected(null);
      return;
    }
    setLoading(true);
    listEntities(currentId)
      .then((entities) => {
        setAllEntities(entities);
        setPeople(extractPeople(entities));
      })
      .finally(() => setLoading(false));
  }, [currentId]);

  const filteredPeople = people.filter((p) => {
    if (roleFilter !== "all" && !p.roles.includes(roleFilter)) return false;
    return true;
  });

  const handleSelect = useCallback((person: PersonData) => {
    setSelected(person);
  }, []);

  const handleNavigate = useCallback((entity: UniversalEntity) => {
    if (entity.entity_type === "company") {
      const person = people.find((p) => p.entity.entity_id === entity.entity_id);
      if (person) setSelected(person);
    }
  }, [people]);

  if (currentId == null) {
    return (
      <div className="empty-state">
        <h3>Створіть дослідження</h3>
        <p className="muted">Щоб побачити осіб, створіть дослідження.</p>
      </div>
    );
  }

  const columns = [
    { key: "fullName" as const, label: "ПІБ", render: (p: PersonData) => <strong>{p.fullName}</strong> },
    { key: "roles" as const, label: "Ролі", render: (p: PersonData) => p.roles.join(", ") },
    { key: "phone" as const, label: "Телефон", render: (p: PersonData) => p.phone || "—" },
    { key: "email" as const, label: "Email", render: (p: PersonData) => p.email || "—" },
    { key: "companyCount" as const, label: "Пов'язаних компаній", render: (p: PersonData) => String(p.companyCount) },
  ];

  const selectedEntity = selected?.entity;
  const positionRels = selectedEntity?.relations?.filter(
    (r) => r.type === "director_of" || r.type === "owner_of"
  );
  const contactRels = selectedEntity?.relations?.filter(
    (r) => r.type === "phone_of" || r.type === "email_of"
  );
  const addressRels = selectedEntity?.relations?.filter(
    (r) => r.type === "registered_at"
  );
  const otherRels = selectedEntity?.relations?.filter(
    (r) => !["director_of", "owner_of", "phone_of", "email_of", "registered_at"].includes(r.type)
  );

  return (
    <div className="master-detail">
      <EntityList
        items={filteredPeople}
        columns={columns}
        onSelect={handleSelect}
        selectedId={selected?.entity.entity_id}
        searchKeys={["fullName" as const]}
        searchPlaceholder="Пошук по ПІБ..."
        emptyMessage="Персоналу не знайдено."
        filters={
          <div className="filter-row">
            <select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)} className="filter-select">
              <option value="all">Усі ролі</option>
              <option value="Директор">Директор</option>
              <option value="Засновник">Засновник</option>
              <option value="Контактна особа">Контактна особа</option>
            </select>
          </div>
        }
      />

      {selected && selectedEntity && (
        <EntityDetailCard entity={selectedEntity}>
          <DetailBlock title="Загальна інформація">
            <div className="entity-row"><span className="muted">ПІБ: </span>{selected.fullName}</div>
            <div className="entity-row"><span className="muted">Ролі: </span>{selected.roles.join(", ")}</div>
          </DetailBlock>

          <RelationBlock
            title="Посади"
            relations={positionRels || []}
            entities={allEntities}
            onNavigate={handleNavigate}
            renderExtra={(e) => <div className="muted">{e.entity_name}</div>}
          />

          <DetailBlock title="Контакти">
            {selected.phone && <div className="entity-row">Телефон: {selected.phone}</div>}
            {selected.email && <div className="entity-row">Email: {selected.email}</div>}
            {!selected.phone && !selected.email && <div className="muted">Контакти відсутні</div>}
            <RelationBlock title="" relations={contactRels || []} entities={allEntities} onNavigate={handleNavigate} />
          </DetailBlock>

          <DetailBlock title="Адреси">
            {selected.address && <div className="entity-row">{selected.address}</div>}
            <RelationBlock title="" relations={addressRels || []} entities={allEntities} onNavigate={handleNavigate} />
            {!selected.address && (!addressRels || addressRels.length === 0) && <div className="muted">Адреси відсутні</div>}
          </DetailBlock>

          <DetailBlock title="Соцмережі">
            <div className="muted">Профілі в соцмережах з'являться після пошуку.</div>
          </DetailBlock>

          <DetailBlock title="Міні-граф зв'язків">
            <div className="mini-graph">
              {selectedEntity.relations?.slice(0, 5).map((rel) => {
                const target = allEntities.find((e) => e.entity_id === rel.target_id);
                return (
                  <div key={rel.target_id} className="mini-graph-node" onClick={() => target && handleNavigate(target)}>
                    <span className="mini-graph-name">{target?.entity_name || rel.target_id}</span>
                    <span className="mini-graph-type">{rel.type}</span>
                  </div>
                );
              })}
              {(!selectedEntity.relations || selectedEntity.relations.length === 0) && (
                <div className="muted">Зв'язків відсутні</div>
              )}
            </div>
          </DetailBlock>

          <DetailBlock title="Медіа">
            <div className="muted">Фото людини з'являться після пошуку медіа.</div>
          </DetailBlock>

          <RelationBlock
            title="Інші зв'язки"
            relations={otherRels || []}
            entities={allEntities}
            onNavigate={handleNavigate}
          />
        </EntityDetailCard>
      )}

      {!selected && (
        <div className="detail-placeholder">
          <p className="muted">Оберіть особу зі списку для перегляду деталей.</p>
        </div>
      )}

      {loading && <div className="empty">Завантаження...</div>}
    </div>
  );
}
