import { PROVIDERS, getProvider } from "../maps/providers";

interface Props {
  providerId: string;
  onProviderChange: (id: string) => void;
  onPromote?: () => void;
}

export default function PanelHeader({ providerId, onProviderChange, onPromote }: Props) {
  const provider = getProvider(providerId);

  return (
    <div className="panel-header">
      <select
        value={providerId}
        onChange={(e) => onProviderChange(e.target.value)}
        title={provider.detail}
      >
        {PROVIDERS.map((p) => (
          <option key={p.id} value={p.id}>
            {p.label}
          </option>
        ))}
      </select>
      {provider.mock && <span className="badge">mock</span>}
      {onPromote && (
        <button className="icon-btn" title="Зробити головним вікном" onClick={onPromote}>
          ⤢
        </button>
      )}
    </div>
  );
}
