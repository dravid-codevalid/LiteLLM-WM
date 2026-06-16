import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:8000/api/:path*",
      },
    ];
  },
  async redirects() {
    return [
      {
        source: "/dashboard",
        destination: "/workspaces",
        permanent: false,
      },
    ];
  },
};

export default nextConfig;
