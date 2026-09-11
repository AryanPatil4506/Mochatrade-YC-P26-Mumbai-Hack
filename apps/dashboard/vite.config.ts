import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Sentinel AI dashboard dev server.
//
// The three backend services (agent :8001, gateway :8002, executor :8003)
// have no CORS middleware configured. Rather than editing those backend
// files, the dev server proxies /api/<service>/* to the real service so
// every browser request is same-origin. SSE (EventSource) streams pass
// through a plain http-proxy unbuffered, so this also covers the two
// long-lived event streams the dashboard depends on.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api/agent': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/agent/, ''),
      },
      '/api/gateway': {
        target: 'http://127.0.0.1:8002',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/gateway/, ''),
      },
      '/api/executor': {
        target: 'http://127.0.0.1:8003',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/executor/, ''),
      },
    },
  },
})
