// Compatibility entry point. The maintained tests use the local Playwright dependency.
const path = require("node:path");
const { spawnSync } = require("node:child_process");
const cli = path.join(path.dirname(require.resolve("playwright/package.json")), "cli.js");
const result = spawnSync(process.execPath, [cli, "test", "booking.spec.ts", ...process.argv.slice(2)], {
  cwd: path.resolve(__dirname, ".."),
  stdio: "inherit",
  env: process.env,
});
if (result.error) {
  console.error(result.error.message);
  process.exit(1);
}
process.exit(result.status ?? 1);
