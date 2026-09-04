import type { NextConfig } from "next";

// Optional API origin for the Admin/Web UI. The project-home status page is
// static and does not start a local server.
const API = process.env.API_ORIGIN || "";

const nextConfig: NextConfig = {
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API}/api/:path*` }];
  },
};

export default nextConfig;
