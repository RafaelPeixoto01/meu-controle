const { execSync } = require("child_process");
const path = require("path");

let input = "";

process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => {
  input += chunk;
});

process.stdin.on("end", () => {
  try {
    const data = JSON.parse(input);
    const command = (data.tool_input && data.tool_input.command) || "";

    // Only check on git commit commands
    if (!command.includes("git commit")) {
      process.exit(0);
    }

    // Resolve frontend directory relative to project root.
    // CLAUDE_PROJECT_DIR primeiro: data.cwd pode vir em formato POSIX
    // (Git Bash) ou apontar para subdiretorio, quebrando o path.join
    const projectDir =
      process.env.CLAUDE_PROJECT_DIR || data.cwd || process.cwd();
    const frontendDir = path.join(projectDir, "frontend");

    process.stderr.write("Running TypeScript type check before commit...\n");
    execSync("npx tsc --noEmit -p tsconfig.app.json", {
      cwd: frontendDir,
      stdio: ["ignore", "pipe", "pipe"],
    });
    process.stderr.write("TypeScript check passed.\n");

    // CR-035: ESLint (errors block; warnings pass)
    process.stderr.write("Running ESLint before commit...\n");
    execSync("npx eslint src", {
      cwd: frontendDir,
      stdio: ["ignore", "pipe", "pipe"],
    });
    process.stderr.write("ESLint check passed.\n");

    process.exit(0);
  } catch (err) {
    if (err.stderr) {
      process.stderr.write(err.stderr.toString());
    }
    if (err.stdout) {
      process.stderr.write(err.stdout.toString());
    }
    process.stderr.write(
      "\nFrontend checks failed (tsc/eslint). Fix errors before committing.\n"
    );
    process.exit(2);
  }
});
