import { motion } from "motion/react";

export function ProgressBar({
  value,
  color = "#00D4AA",
  label,
  valueLabel,
}: {
  value: number;
  color?: string;
  label?: string;
  valueLabel?: string;
}) {
  return (
    <div className="w-full">
      {(label || valueLabel) && (
        <div className="mb-2 flex items-center justify-between text-xs">
          <span className="text-muted-foreground">{label}</span>
          <span className="font-medium" style={{ color }}>
            {valueLabel ?? `${value}%`}
          </span>
        </div>
      )}
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-[#292929]">
        <motion.div
          className="h-full rounded-full"
          style={{ backgroundColor: color }}
          initial={{ width: "0%" }}
          whileInView={{ width: `${value}%` }}
          viewport={{ once: true, margin: "-40px" }}
          transition={{ duration: 1.2, ease: "easeOut" }}
        />
      </div>
    </div>
  );
}
