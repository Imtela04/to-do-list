// Apply immediately to avoid flash
if (localStorage.getItem("darkMode") === "true") {
    document.documentElement.classList.add("dark");
}

export function initDarkMode(toggleId) {
    const btn = document.getElementById(toggleId);
    if (!btn) return;

    // Set initial button text
    btn.textContent = localStorage.getItem("darkMode") === "true" ? "☀️" : "🌙";

    btn.addEventListener("click", () => {
        document.documentElement.classList.toggle("dark");
        const isDark = document.documentElement.classList.contains("dark");
        localStorage.setItem("darkMode", isDark);
        btn.textContent = isDark ? "☀️" : "🌙";
    });
}