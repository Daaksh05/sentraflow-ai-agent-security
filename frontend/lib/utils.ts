import { ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatRiskScore(score: number): {
  color: string;
  bgColor: string;
  borderColor: string;
  label: string;
} {
  if (score < 30) {
    return {
      color: "text-emerald-400",
      bgColor: "bg-emerald-500/10",
      borderColor: "border-emerald-500/20",
      label: "LOW RISK",
    };
  }
  if (score < 70) {
    return {
      color: "text-amber-400",
      bgColor: "bg-amber-500/10",
      borderColor: "border-amber-500/20",
      label: "MODERATE",
    };
  }
  return {
    color: "text-rose-400",
    bgColor: "bg-rose-500/10",
    borderColor: "border-rose-500/20",
    label: "CRITICAL RISK",
  };
}
