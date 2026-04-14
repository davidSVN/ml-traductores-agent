/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  basePath: "/agente-cotizaciones",
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
