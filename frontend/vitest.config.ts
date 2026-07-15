import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    // jsdom: api.ts usa localStorage e window (CR-039)
    environment: "jsdom",
    include: ["src/**/*.test.{ts,tsx}"],
  },
});
