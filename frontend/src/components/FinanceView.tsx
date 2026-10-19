import { useEffect, useState, useCallback } from "react";
import { listEntities } from "../api";
import { useWorkspaceStore } from "../store/workspaceState";
import type { UniversalEntity } from "../types";
import EntityList from "./EntityList";
import EntityDetailCard, { DetailBlock } from "./EntityDetailCard";
import RelationBlock from "./RelationBlock";

type FinanceTab = "accounts" | "transactions" | "procurements";

interface FinanceData {
  entity: UniversalEntity;
  companyName: string;
  edrpou: string;
  capital: string;
  taxStatus: string;
  activities: string[];
  phone: string;
  email: string;
  address: string;
  status: string;
}

function extractFinance(entities: UniversalEntity[]): FinanceData[] {
  return entities
    .filter((e) => e.properties?.company)
    .map((e) => {
      const c = e.properties!.company!;
      return {
        entity: e,
        companyName: e.entity_name,
        edrpou: c.edrpou || "",
        capital: c.capital || "",
        taxStatus: c.tax_status || "",
        activities: c.activities || [],
        phone: c.phone || "",
        email: c.email || "",
        address: c.address || "",
        status: c.status || "",
      };
    })
    .filter((f) => f.capital || f.taxStatus || f.activities.length > 0 || f.edrpou);
}

export default function FinanceView() {
  const currentId = useWorkspaceStore((s) => s.currentId);
  const [allEntities, setAllEntities] = useState<UniversalEntity[]>([]);
  const [items, setItems] = useState<FinanceData[]>([]);
  const [selected, setSelected] = useState<FinanceData | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<FinanceTab>("accounts");
  const [companyFilter, setCompanyFilter] = useState<string>("");

  useEffect(() => {
    if (currentId == null) {
      setAllEntities([]);
      setItems([]);
      setSelected(null);
      return;
    }
    setLoading(true);
    listEntities(currentId)
      .then((entities) => {
        setAllEntities(entities);
        setItems(extractFinance(entities));
      })
      .finally(() => setLoading(false));
  }, [currentId]);

  const filteredItems = items.filter((f) => {
    if (companyFilter && !f.companyName.toLowerCase().includes(companyFilter.toLowerCase())) return false;
    return true;
  });

  const handleSelect = useCallback((item: FinanceData) => {
    setSelected(item);
  }, []);

  const handleNavigate = useCallback((entity: UniversalEntity) => {
    const item = items.find((i) => i.entity.entity_id === entity.entity_id);
    if (item) setSelected(item);
  }, [items]);

  if (currentId == null) {
    return (
      <div className="empty-state">
        <h3>Створіть дослідження</h3>
        <p className="muted">Щоб побачити фінанси, створіть дослідження.</p>
      </div>
    );
  }

  const tabs: { id: FinanceTab; label: string }[] = [
    { id: "accounts", label: "Рахунки" },
    { id: "transactions", label: "Транзакції" },
    { id: "procurements", label: "Закупівлі" },
  ];

  const columns = [
    { key: "companyName" as const, label: "Компанія", render: (f: FinanceData) => <strong>{f.companyName}</strong> },
    { key: "edrpou" as const, label: "ЄДРПОУ", render: (f: FinanceData) => f.edrpou || "—" },
    { key: "capital" as const, label: "Капітал", render: (f: FinanceData) => f.capital || "—" },
    { key: "taxStatus" as const, label: "Податковий статус", render: (f: FinanceData) => f.taxStatus || "—" },
    { key: "status" as const, label: "Статус", render: (f: FinanceData) => f.status || "—" },
  ];

  const selectedCompany = selected?.entity.properties?.company;

  return (
    <div>
      <div className="finance-tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`finance-tab ${activeTab === tab.id ? "active" : ""}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="filter-row" style={{ marginBottom: 12 }}>
        <input
          type="text"
          value={companyFilter}
          onChange={(e) => setCompanyFilter(e.target.value)}
          placeholder="Фільтр по компанії..."
          className="filter-input"
        />
      </div>

      <div className="master-detail">
        <EntityList
          items={filteredItems}
          columns={columns}
          onSelect={handleSelect}
          selectedId={selected?.entity.entity_id}
          searchKeys={["companyName" as const, "edrpou" as const]}
          searchPlaceholder="Пошук по компанії..."
          emptyMessage="Фінансових записів не знайдено."
        />

        {selected && selectedCompany && (
          <EntityDetailCard entity={selected.entity}>
            {activeTab === "accounts" && (
              <>
                <DetailBlock title="Рахунки">
                  <div className="entity-row"><span className="muted">Компанія: </span>{selected.companyName}</div>
                  <div className="entity-row"><span className="muted">ЄДРПОУ: </span>{selected.edrpou || "—"}</div>
                  <div className="entity-row"><span className="muted">Статутний капітал: </span>{selected.capital || "—"}</div>
                  <div className="entity-row"><span className="muted">Податковий статус: </span>{selected.taxStatus || "—"}</div>
                </DetailBlock>
                <DetailBlock title="Історія балансу">
                  <div className="muted">Історія балансу з'явиться після підключення банківських API.</div>
                </DetailBlock>
              </>
            )}

            {activeTab === "transactions" && (
              <>
                <DetailBlock title="Транзакції">
                  <div className="muted">Транзакції з'являться після підключення банківських API.</div>
                </DetailBlock>
                <DetailBlock title="Таймлайн операцій">
                  <div className="muted">Графік операцій з'явиться після підключення банківських API.</div>
                </DetailBlock>
                <DetailBlock title="Аномальні транзакції">
                  <div className="muted">Аномалії визначатимуться AI-модулем.</div>
                </DetailBlock>
              </>
            )}

            {activeTab === "procurements" && (
              <>
                <DetailBlock title="Закупівлі">
                  <div className="entity-row"><span className="muted">Компанія: </span>{selected.companyName}</div>
                  <div className="entity-row"><span className="muted">Статус: </span>{selected.status || "—"}</div>
                  <div className="muted" style={{ marginTop: 8 }}>Контракти закупівель з'являться після підключення Prozorro API.</div>
                </DetailBlock>
                <DetailBlock title="Документи">
                  <div className="muted">Документи контрактів з'являться після підключення.</div>
                </DetailBlock>
              </>
            )}

            <DetailBlock title="Контакти">
              {selected.phone && <div className="entity-row">Телефон: {selected.phone}</div>}
              {selected.email && <div className="entity-row">Email: {selected.email}</div>}
            </DetailBlock>

            <RelationBlock
              title="Зв'язані сутності"
              relations={selected.entity.relations || []}
              entities={allEntities}
              onNavigate={handleNavigate}
            />
          </EntityDetailCard>
        )}

        {!selected && (
          <div className="detail-placeholder">
            <p className="muted">Оберіть запис зі списку для перегляду деталей.</p>
          </div>
        )}

        {loading && <div className="empty">Завантаження...</div>}
      </div>
    </div>
  );
}
