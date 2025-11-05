import { useEffect, useState } from "react";

export default function ThemeToggle() {
  const [dark, setDark] = useState(() => {
    if (typeof window === "undefined") return false;
    const stored = localStorage.getItem("theme");
    if (stored) return stored === "dark";
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  });

  useEffect(() => {
    const root = document.documentElement;
    if (dark) {
      root.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      root.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  }, [dark]);

  return (
    <button
      className="btn-ghost"
      onClick={() => setDark((value) => !value)}
      aria-pressed={dark}
      title={dark ? "Byt till ljust läge" : "Byt till mörkt läge"}
    >
      {dark ? "☀️ Ljust" : "🌙 Mörkt"}
    </button>
  );
}
