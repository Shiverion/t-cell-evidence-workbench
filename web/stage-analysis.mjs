import {
  cpSync,
  existsSync,
  mkdirSync,
  rmSync,
} from "node:fs";
import path from "node:path";

const webRoot = process.cwd();
const sourceDirectory = path.resolve(webRoot, "..", "output", "official");
const stagingRoot = path.resolve(webRoot, ".analysis-output");
const targetDirectory = path.join(stagingRoot, "official");
const relativeTarget = path.relative(webRoot, targetDirectory);

if (
  relativeTarget.startsWith("..") ||
  path.isAbsolute(relativeTarget)
) {
  throw new Error(`Refusing to stage analysis outside the web app: ${targetDirectory}`);
}

if (!existsSync(path.join(sourceDirectory, "provenance", "manifest.json"))) {
  throw new Error(
    `Pinned analysis artifacts are missing from ${sourceDirectory}`,
  );
}

rmSync(targetDirectory, { force: true, recursive: true });
mkdirSync(stagingRoot, { recursive: true });
cpSync(sourceDirectory, targetDirectory, { recursive: true });

console.log(`Staged pinned analysis artifacts in ${targetDirectory}`);
