"use client";

import { useEffect, useMemo, useState } from "react";
import { gradeColor, scoreToGrade, verdictColor } from "@/lib/colors";

interface CircleGaugeProps {
  score: number; // 0-100
  size?: number;
  strokeWidth?: number;
  grade?: string;
  verdict?: string;
  label?: string;
  durationMs?: number;
}

export default function CircleGauge({
  score,
  size = 160,
  strokeWidth = 12,
  grade,
  verdict,
  label,
  durationMs = 900,
}: CircleGaugeProps) {
  const clamped = Math.max(0, Math.min(100, score));
  const [displayScore, setDisplayScore] = useState(0);
  const resolvedGrade = grade ?? scoreToGrade(clamped);
  const color = verdict ? verdictColor(verdict) : gradeColor(resolvedGrade);

  const radius = size / 2 - strokeWidth;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - displayScore / 100);
  const center = size / 2;

  useEffect(() => {
    let frameId = 0;
    let startTime: number | null = null;

    setDisplayScore(0);

    const animate = (timestamp: number) => {
      if (startTime == null) {
        startTime = timestamp;
      }

      const elapsed = timestamp - startTime;
      const progress = Math.min(elapsed / durationMs, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayScore(clamped * eased);

      if (progress < 1) {
        frameId = window.requestAnimationFrame(animate);
      }
    };

    frameId = window.requestAnimationFrame(animate);
    return () => window.cancelAnimationFrame(frameId);
  }, [clamped, durationMs]);

  const roundedDisplayScore = useMemo(
    () => Math.round(displayScore),
    [displayScore],
  );

  return (
    <div
      className="relative inline-flex items-center justify-center"
      style={{ width: size, height: size }}
    >
      <svg width={size} height={size} className="-rotate-90">
        {/* 배경 원 */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="#e2e8f0"
          strokeWidth={strokeWidth}
        />
        {/* 점수 원 */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{
            transition: "stroke-dashoffset 0.8s ease, stroke 0.3s ease",
          }}
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center">
        <span
          className="font-bold leading-none"
          style={{ fontSize: size * 0.28, color }}
        >
          {roundedDisplayScore}
        </span>
        <span
          className="mt-1 text-[#64748b]"
          style={{ fontSize: size * 0.09 }}
        >
          {label ?? "점"}
        </span>
      </div>
    </div>
  );
}
