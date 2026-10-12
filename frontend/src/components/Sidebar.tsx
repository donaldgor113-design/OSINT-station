import type { ReactNode } from "react";
import { GearIcon, ImageIcon, ListIcon, MapIcon, SearchIcon, SparkIcon, UserIcon } from "./icons";

interface NavItem {
  id: string;
  label: string;
  icon: ReactNode;
}

const MAIN: NavItem[] = [
  { id: "search", label: "Пошук", icon: <SearchIcon /> },
  { id: "geo", label: "Гео-мапи", icon: <MapIcon /> },
  { id: "images", label: "Зображення", icon: <ImageIcon /> },
  { id: "entities", label: "Сутності", icon: <ListIcon /> },
  { id: "analyze", label: "Аналіз", icon: <SparkIcon /> },
];

const BOTTOM: NavItem[] = [
  { id: "settings", label: "Налаштування", icon: <GearIcon /> },
  { id: "profile", label: "Профіль", icon: <UserIcon /> },
];

interface Props {
  active: string;
  onChange: (id: string) => void;
}

function NavButton({ item, active, onChange }: { item: NavItem; active: boolean; onChange: (id: string) => void }) {
  return (
    <button
      className={`nav-item ${active ? "nav-active" : ""}`}
      onClick={() => onChange(item.id)}
    >
      {item.icon}
      <span>{item.label}</span>
    </button>
  );
}

export default function Sidebar({ active, onChange }: Props) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <span className="brand-dot" />
        OSINT Workspace
      </div>

      <nav className="sidebar-nav">
        {MAIN.map((item) => (
          <NavButton key={item.id} item={item} active={active === item.id} onChange={onChange} />
        ))}
      </nav>

      <nav className="sidebar-nav sidebar-bottom">
        {BOTTOM.map((item) => (
          <NavButton key={item.id} item={item} active={active === item.id} onChange={onChange} />
        ))}
      </nav>
    </aside>
  );
}
