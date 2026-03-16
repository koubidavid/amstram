interface ScoreGaugeProps {
  score: number;
  size?: "sm" | "md" | "lg";
}

export function ScoreGauge({ score, size = "md" }: ScoreGaugeProps) {
  const getColor = (s: number) => {
    if (s > 75) return "border-red-500 text-red-500";
    if (s > 50) return "border-orange-500 text-orange-500";
    if (s > 25) return "border-yellow-500 text-yellow-500";
    return "border-green-500 text-green-500";
  };

  const dimensions = {
    sm: "h-10 w-10 text-xs",
    md: "h-14 w-14 text-base",
    lg: "h-20 w-20 text-xl",
  };

  return (
    <div className={`flex items-center justify-center rounded-full border-4 font-bold ${getColor(score)} ${dimensions[size]}`}>
      {score}
    </div>
  );
}
