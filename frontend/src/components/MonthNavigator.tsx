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
    <div className="flex items-center justify-between bg-white rounded-xl shadow-sm border border-gray-200 px-2 py-2">
      <button
        type="button"
        onClick={onPrevious}
        className="px-4 py-2.5 text-primary font-semibold rounded-lg
          hover:bg-primary/10 active:bg-primary/20
          transition-colors duration-150"
      >
        ← Anterior
      </button>
      <h2 className="text-xl font-bold text-gray-800">
        {getMonthLabel(year, month)}
      </h2>
      <button
        type="button"
        onClick={onNext}
        className="px-4 py-2.5 text-primary font-semibold rounded-lg
          hover:bg-primary/10 active:bg-primary/20
          transition-colors duration-150"
      >
        Proximo →
      </button>
    </div>
  );
}
