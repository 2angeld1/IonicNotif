import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: {
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('react') || id.includes('react-dom') || id.includes('react-router-dom')) {
              return 'vendor';
            }
            if (id.includes('@ionic')) {
              return 'ionic';
            }
            if (id.includes('leaflet') || id.includes('react-leaflet')) {
              return 'leaflet';
            }
          }
        },
      },
    },
  },
  css: {
    lightningcss: {
      targets: {
        chrome: 120, // Targets modern browsers that support :host-context or handle it gracefully
      }
    }
  },
})
