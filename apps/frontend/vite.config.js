import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        target: process.env.API_SERVICE_URL || 'http://localhost:8000',
        changeOrigin: true,
      },
      '/agent': {
        target: process.env.AGENT_SERVICE_URL || 'http://localhost:8001',
        changeOrigin: true,
      },
      '/simulation': {
        target: process.env.SIMULATION_SERVICE_URL || 'http://localhost:8002',
        changeOrigin: true,
      },
      '/analysis': {
        target: process.env.ANALYSIS_SERVICE_URL || 'http://localhost:8003',
        changeOrigin: true,
      },
      '/reports': {
        target: process.env.REPORT_SERVICE_URL || 'http://localhost:8004',
        changeOrigin: true,
      },
    },
  },
})
