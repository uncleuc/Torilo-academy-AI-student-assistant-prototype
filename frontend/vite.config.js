import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";
import { loadEnv } from "vite";

const frontendDirectory = fileURLToPath(new URL(".", import.meta.url));
const repositoryRoot = resolve(frontendDirectory, "..");

export default defineConfig(({ mode }) => {
	const env = loadEnv(mode, repositoryRoot, [
		"VITE_",
		"API_PROXY_TARGET",
		"FRONTEND_PORT",
		"FRONTEND_PREVIEW_PORT",
	]);
	const allowedHosts = (env.VITE_ALLOWED_HOSTS || "ai.softshell-diminished.ts.net,torilo.net,www.torilo.net")
		.split(",")
		.map((host) => host.trim())
		.filter(Boolean);
	const proxy = {
		"/api": {
			target: env.API_PROXY_TARGET || "http://127.0.0.1:8000",
			changeOrigin: true,
		},
	};
	const port = Number.parseInt(env.FRONTEND_PORT || "5173", 10);

	return {
		envDir: repositoryRoot,
		plugins: [react()],
		server: {
			host: "0.0.0.0",
			port,
			strictPort: true,
			allowedHosts,
			proxy,
		},
		preview: {
			host: "0.0.0.0",
			port: Number.parseInt(env.FRONTEND_PREVIEW_PORT || "4173", 10),
			strictPort: true,
			allowedHosts,
			proxy,
		},
		test: {
			environment: "jsdom",
			clearMocks: true,
			restoreMocks: true,
		},
	};
});