import { useState, useMemo } from "react";
import type { UniversalEntity } from "../types";

interface Column<T> {
  key: string;
  label: string;
  render: (item: T) => React.ReactNode;
  sortable?: boolean;
}

interface EntityListProps<T> {
  items: T[];
  columns: Column<T>[];
  onSelect: (item: T) => void;
  selectedId?: string;
  filters?: React.ReactNode;
  searchKeys?: (keyof T)[];
  searchPlaceholder?: string;
  emptyMessage?: string;
}

export default function EntityList<T extends { entity_id: string }>({
  items,
  columns,
  onSelect,
  selectedId,
  filters,
  searchKeys,
  searchPlaceholder = "Пошук...",
  emptyMessage = "Нічого не знайдено",
}: EntityListProps<T>) {
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    if (!search || !searchKeys || searchKeys.length === 0) return items;
    const q = search.toLowerCase();
    return items.filter((item) =>
      searchKeys.some((key) => String(item[key]).toLowerCase().includes(q))
    );
  }, [items, search, searchKeys]);

  return (
    <div className="entity-list-panel">
      {searchKeys && searchKeys.length > 0 && (
        <div className="entity-list-search">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={searchPlaceholder}
            className="search-input"
          />
        </div>
      )}
      {filters && <div className="entity-list-filters">{filters}</div>}
      <div className="entity-list-count">Знайдено: {filtered.length}</div>
      <div className="entity-list">
        {filtered.length === 0 ? (
          <div className="empty">{emptyMessage}</div>
        ) : (
          filtered.map((item) => (
            <div
              key={item.entity_id}
              className={`entity-list-item ${selectedId === item.entity_id ? "active" : ""}`}
              onClick={() => onSelect(item)}
            >
              {columns.map((col) => (
                <div key={col.key} className="entity-list-cell">
                  {col.render(item)}
                </div>
              ))}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
