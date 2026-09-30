import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
export const rootDir = path.resolve(here, '..');

async function loadDotEnv() {
  const file = path.join(rootDir, '.env');
  let raw;
  try {
    raw = await readFile(file, 'utf8');
  } catch {
    return;
  }
  for (const line of raw.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const eq = trimmed.indexOf('=');
    if (eq === -1) continue;
    const key = trimmed.slice(0, eq).trim();
    let value = trimmed.slice(eq + 1).trim();
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }
    if (!(key in process.env)) process.env[key] = value;
  }
}

await loadDotEnv();

const bool = (value, fallback = false) => {
  if (value === undefined) return fallback;
  return /^(1|true|yes|on)$/i.test(value);
};

export const config = {
  port: Number(process.env.PORT || 3000),
  env: process.env.NODE_ENV || 'development',
  siteUrl: (process.env.SITE_URL || 'http://localhost:3000').replace(/\/+$/, ''),
  dataFile: process.env.DATA_FILE || path.join(rootDir, 'data', 'db.json'),
  admin: {
    user: process.env.ADMIN_USER || 'admin',
    password: process.env.ADMIN_PASSWORD || 'adminmascapito',
    sessionSecret: process.env.SESSION_SECRET || 'diamonds-league-dev-secret-change-me',
    cookieSecure: bool(process.env.COOKIE_SECURE, false),
    sessionTtlMs: 1000 * 60 * 60 * 8
  }
};

if (config.env === 'production' && config.admin.sessionSecret.startsWith('diamonds-league-dev')) {
  console.warn('[aviso] SESSION_SECRET por defecto en produccion. Define uno propio en .env.');
}
