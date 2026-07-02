"use client";

interface ScoreBarProps {
  label: string;
  value: number; // 0..1, or negative for penalty
  color: string;
  isPenalty?: boolean;
}

export default function ScoreBar({ label, value, color, isPenalty = false }: ScoreBarProps) {
  const pct = Math.min(100, Math.abs(value) * 100);
  return (
    <div>
      <div className="flex justify-between text-[11px] mb-1">
        <span className="text-muted">{label}</span>
        <span className="font-numeric text-ink">
          {isPenalty && value > 0 ? "-" : ""}
          {value.toFixed(2)}
        </span>
      </div>
      <div className="h-1.5 w-full bg-panel2 rounded-full overflow-hidden">
        <div
          className="h-full score-bar-fill rounded-full"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}
