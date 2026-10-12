import { useState } from "react";
import type { FormEvent } from "react";

interface Props {
  onSearch: (query: string) => void;
  loading: boolean;
}

export default function SearchBar({ onSearch, loading }: Props) {
  const [value, setValue] = useState("");

  function submit(e: FormEvent) {
    e.preventDefault();
    if (value.trim()) {
      onSearch(value.trim());
    }
  }

  return (
    <form className="search-bar" onSubmit={submit}>
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Введіть запит: IP, домен, ЄДРПОУ або назву компанії…"
      />
      <button type="submit" disabled={loading}>
        {loading ? "Пошук…" : "Шукати"}
      </button>
    </form>
  );
}
