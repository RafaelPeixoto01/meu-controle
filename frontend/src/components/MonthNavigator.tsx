import { getMonthLabel } from "../utils/date";

interface MonthNavigatorProps {
  year: number;
  month: number;
  onPrevious: () => void;
  onNext: () => void;
}

export default function MonthNavigator({
  year,
  month,
  onPrevious,
  onNext,
}: MonthNavigatorProps) {
  return (
    <div className="flex items-center justify-between bg-surface rounded-2xl shadow-lg shadow-black/[0.04] border border-slate-100/80 px-3 py-3">
      <button
        type="button"
        onClick={onPrevious}
        className="px-4 py-2.5 text-primary font-semibold rounded-xl
          hover:bg-primary/10 active:bg-primary/20 active:scale-[0.97]
          transition-all duration-150"
      >
        ← Anterior
      </button>
      <h2 className="text-xl font-bold text-text">
        {getMonthLabel(year, month)}
      </h2>
      <button
        type="button"
        onClick={onNext}
        className="px-4 py-2.5 text-primary font-semibold rounded-xl
          hover:bg-primary/10 active:bg-primary/20 active:scale-[0.97]
          transition-all duration-150"
      >
        Proximo →
      </button>
    </div>
  );
}
