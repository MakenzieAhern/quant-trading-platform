const configuredUrl =
  import.meta.env.VITE_API_BASE_URL?.trim() ||
  import.meta.env.VITE_API_URL?.trim();

export const API_BASE_URL = (configuredUrl || "http://localhost:8000").replace(
  /\/$/,
  "",
);
