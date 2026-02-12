/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                background: "#09090b", // Deep black/gray
                surface: "#18181b",    // Slightly lighter
                primary: "#a855f7",    // Purple (ReconFlow brand)
                secondary: "#3b82f6",  // Blue
                accent: "#ec4899",     // Pink
                success: "#22c55e",
                warning: "#eab308",
                error: "#ef4444",
                border: "#27272a",
                foreground: "#fafafa",
            },
            fontFamily: {
                sans: ['Inter', 'sans-serif'],
                mono: ['Fira Code', 'monospace'],
            },
            animation: {
                'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
            }
        },
    },
    plugins: [],
}
