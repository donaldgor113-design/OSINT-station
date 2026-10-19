import type { UniversalEntity } from "../types";

interface Relation {
  target_id: string;
  type: string;
  confidence: number;
}

interface RelationBlockProps {
  title: string;
  relations: Relation[];
  entities: UniversalEntity[];
  onNavigate: (entity: UniversalEntity) => void;
  renderExtra?: (entity: UniversalEntity) => React.ReactNode;
}

export default function RelationBlock({
  title,
  relations,
  entities,
  onNavigate,
  renderExtra,
}: RelationBlockProps) {
  if (relations.length === 0) return null;

  const related = relations
    .map((rel) => {
      const entity = entities.find((e) => e.entity_id === rel.target_id);
      return entity ? { entity, relation: rel } : null;
    })
    .filter(Boolean) as { entity: UniversalEntity; relation: Relation }[];

  if (related.length === 0) return null;

  return (
    <div className="relation-block">
      <h4>{title}</h4>
      {related.map(({ entity, relation }) => (
        <div
          key={entity.entity_id}
          className="relation-item"
          onClick={() => onNavigate(entity)}
        >
          <div className="relation-name">{entity.entity_name}</div>
          <div className="relation-type">{relation.type}</div>
          {renderExtra?.(entity)}
          <div className="relation-confidence">
            Довіра: {(relation.confidence * 100).toFixed(0)}%
          </div>
        </div>
      ))}
    </div>
  );
}
