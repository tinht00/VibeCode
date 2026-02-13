/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{vue,js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                surface: {
                    50: '#f0f4ff',
                    100: '#e0e7ff',
                    800: '#1e1b4b',
                    900: '#0f0a2e',
                    950: '#080520',
                },
                accent: {
                    400: '#a78bfa',
                    500: '#8b5cf6',
                    600: '#7c3aed',
                },
                cyan: {
                    400: '#22d3ee',
                    500: '#06b6d4',
                }
            },
            fontFamily: {
                display: ['Space Grotesk', 'sans-serif'],
                body: ['DM Sans', 'sans-serif'],
            },
            backdropBlur: {
                xs: '2px',
            },
            animation: {
                'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                'float': 'float 6s ease-in-out infinite',
                'glow': 'glow 2s ease-in-out infinite alternate',
            },
            keyframes: {
                float: {
                    '0%, 100%': { transform: 'translateY(0px)' },
                    '50%': { transform: 'translateY(-10px)' },
                },
                glow: {
                    '0%': { boxShadow: '0 0 5px rgba(139, 92, 246, 0.3)' },
                    '100%': { boxShadow: '0 0 20px rgba(139, 92, 246, 0.6), 0 0 40px rgba(6, 182, 212, 0.3)' },
                }
            }
        },
    },
    plugins: [],
}
