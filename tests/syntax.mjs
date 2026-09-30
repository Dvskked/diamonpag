/**
 * Comprueba la sintaxis de todos los ficheros JavaScript del proyecto.
 * `node --check` no sigue los imports, asi que se recorren las carpetas a mano.
 */
import { spawnSync } from 'node:child_process';
import { readdirSync, statSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const targets = ['src', 'public', 'tests'];

function walk(dir, out = []) {
  for (const entry of readdirSync(dir)) {
    const full = path.join(dir, entry);
    if (statSync(full).isDirectory()) walk(full, out);
    else if (/\.(m?js)$/.test(entry)) out.push(full);
  }
  return out;
}

const files = targets.flatMap((dir) => walk(path.join(rootDir, dir)));
let failed = 0;

for (const file of files) {
  const result = spawnSync(process.execPath, ['--check', file], { encoding: 'utf8' });
  const name = path.relative(rootDir, file);
  if (result.status === 0) {
    console.log(`  OK    ${name}`);
  } else {
    failed += 1;
    console.log(`  FAIL  ${name}\n${result.stderr.trim()}`);
  }
}

console.log(`\n${files.length} ficheros, ${failed} con errores de sintaxis.`);
process.exit(failed === 0 ? 0 : 1);
