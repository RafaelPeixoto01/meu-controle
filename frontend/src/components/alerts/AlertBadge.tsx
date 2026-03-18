interface AlertBadgeProps {
  count: number;
  maxSeverity: "critico" | "atencao" | "informativo" | null;
}

export default function AlertBadge({ count, maxSeverity }: AlertBadgeProps) {
  if (count === 0 || !maxSeverity) return null;

  const bgColor = maxSeverity === "critico"
    ? "bg-red-500"
    : maxSeverity === "atencao"
      ? "bg-amber-500"
      : "bg-blue-500";

  return (
    <span
      className={`absolute -top-1.5 -right-1.5 ${bgColor} text-white text-[10px] font-bold min-w-[18px] h-[18px] flex items-center justify-center rounded-full px-1 leading-none`}
    >
      {count > 9 ? "9+" : count}
    </span>
  );
}
