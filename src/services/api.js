import axios from "axios";
import { demoAdapter } from "../mocks/demoAdapter";

export const isDemoMode = import.meta.env.VITE_DEMO_MODE === "true";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000/api",
  withCredentials: true,
});

// Keep demo mode isolated at the transport boundary. The normal service
// functions remain unchanged, and demo mode never contacts the real API.
if (isDemoMode) {
  api.defaults.adapter = demoAdapter;
}

export default api;
