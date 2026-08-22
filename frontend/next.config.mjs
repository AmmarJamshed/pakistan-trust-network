/** @type {import('next').NextConfig} */

const apiInternal = (process.env.API_INTERNAL_URL || "").replace(/\/$/, "");

const nextConfig = {
  output: "standalone",
  reactStrictMode: true,
  async rewrites() {
    if (!apiInternal) {
      return [];
    }
    return [
      { source: "/api/:path*", destination: `${apiInternal}/api/:path*` },
      { source: "/health", destination: `${apiInternal}/health` },
    ];
  },
};

export default nextConfig;
