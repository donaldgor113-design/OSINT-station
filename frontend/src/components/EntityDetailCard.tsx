import type { ReactNode } from "react";
import type { UniversalEntity } from "../types";

interface DetailBlockProps {
  title: string;
  children: ReactNode;
}

export function DetailBlock({ title, children }: DetailBlockProps) {
  return (
    <div className="detail-block">
      <h4>{title}</h4>
      {children}
    </div>
  );
}

interface EntityDetailCardProps {
  entity: UniversalEntity;
  children?: ReactNode;
  onNavigate?: (entity: UniversalEntity) => void;
}

export default function EntityDetailCard({
  entity,
  children,
}: EntityDetailCardProps) {
  const meta = entity.properties?.metadata;
  const sources = meta?.sources || [];

  return (
    <div className="entity-detail-card">
      <div className="detail-header">
        <span className="entity-type">{entity.entity_type}</span>
        <h2>{entity.entity_name}</h2>
      </div>

      {children}

      <DetailBlock title="Джерела">
        {sources.length > 0 ? (
          sources.map((s, i) => (
            <div key={i} className="entity-row muted">
              {s.name} · довіра {(s.confidence * 100).toFixed(0)}%
              {s.last_verified && ` · ${s.last_verified.slice(0, 10)}`}
            </div>
          ))
        ) : (
          <div className="entity-row muted">Джерела відсутні</div>
        )}
      </DetailBlock>

      <div className="detail-actions">
        <button className="btn-secondary">Додати до звіту</button>
        <button className="btn-secondary">Прикріпити доказ</button>
      </div>
    </div>
  );
}
