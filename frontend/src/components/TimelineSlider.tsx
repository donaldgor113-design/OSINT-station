import type { ChangeEvent } from "react";
import { useMapStore } from "../store/mapState";

const DATES = [
  "2018-05-12",
  "2020-09-01",
  "2022-03-15",
  "2024-06-30",
  "2026-01-01",
];

export default function TimelineSlider() {
  const timestamp = useMapStore((s) => s.timestamp);
  const setTimestamp = useMapStore((s) => s.setTimestamp);

  const index = timestamp ? DATES.indexOf(timestamp) : DATES.length - 1;
  const safeIndex = index >= 0 ? index : DATES.length - 1;

  function onChange(e: ChangeEvent<HTMLInputElement>) {
    setTimestamp(DATES[Number(e.target.value)]);
  }

  return (
    <div className="timeline">
      <span className="muted">Таймлайн:</span>
      <input
        type="range"
        min={0}
        max={DATES.length - 1}
        step={1}
        value={safeIndex}
        onChange={onChange}
      />
      <span className="muted">{timestamp ?? DATES[DATES.length - 1]}</span>
    </div>
  );
}
