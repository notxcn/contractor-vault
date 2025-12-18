import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // Allow images from any domain (for future use)
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
