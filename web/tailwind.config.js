/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,ts}'],
  theme: { extend: { colors: { canvas: '#FAFAFA', card: '#FFFFFF', border: '#E4E4E7', ink: '#18181B', muted: '#71717A', sidebar: '#0F1729', primary: '#6366F1', primaryHover: '#4F46E5', success: '#16A34A', warning: '#D97706', danger: '#DC2626' }, boxShadow: { card: '0 1px 2px rgba(0,0,0,0.04)' }, borderRadius: { card: '10px' } } }, plugins: [],
}
