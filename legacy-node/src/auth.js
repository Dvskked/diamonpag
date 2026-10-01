import crypto from 'node:crypto';
import { config } from './config.js';

const COOKIE_NAME = 'tld_session';
const MAX_ATTEMPTS = 8;
const WINDOW_MS = 10 * 60 * 1000;

const attempts = new Map();

function digest(value) {
  return crypto.createHash('sha256').update(String(value)).digest();
}

export function safeEqual(a, b) {
  return crypto.timingSafeEqual(digest(a), digest(b));
}

function base64url(input) {
  return Buffer.from(input).toString('base64url');
}

function sign(payload) {
  return crypto.createHmac('sha256', config.admin.sessionSecret).update(payload).digest('base64url');
}

export function createToken(user) {
  const payload = base64url(
    JSON.stringify({ u: user, exp: Date.now() + config.admin.sessionTtlMs })
  );
  return `${payload}.${sign(payload)}`;
}

export function readToken(token) {
  if (typeof token !== 'string' || !token.includes('.')) return null;
  const [payload, signature] = token.split('.');
  if (!payload || !signature) return null;
  if (!safeEqual(sign(payload), signature)) return null;
  try {
    const data = JSON.parse(Buffer.from(payload, 'base64url').toString('utf8'));
    if (typeof data.exp !== 'number' || data.exp < Date.now()) return null;
    return data;
  } catch {
    return null;
  }
}

export function parseCookies(header = '') {
  const out = {};
  for (const part of String(header).split(';')) {
    const eq = part.indexOf('=');
    if (eq === -1) continue;
    const key = part.slice(0, eq).trim();
    if (!key) continue;
    out[key] = decodeURIComponent(part.slice(eq + 1).trim());
  }
  return out;
}

export function sessionCookie(token) {
  const maxAge = Math.floor(config.admin.sessionTtlMs / 1000);
  return [
    `${COOKIE_NAME}=${token}`,
    'Path=/',
    'HttpOnly',
    'SameSite=Lax',
    `Max-Age=${maxAge}`,
    config.admin.cookieSecure ? 'Secure' : ''
  ]
    .filter(Boolean)
    .join('; ');
}

export function clearCookie() {
  return `${COOKIE_NAME}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0${
    config.admin.cookieSecure ? '; Secure' : ''
  }`;
}

export function getSession(req) {
  const token = parseCookies(req.headers.cookie || '')[COOKIE_NAME];
  return readToken(token);
}

export function checkRateLimit(key) {
  const now = Date.now();
  const entry = attempts.get(key);
  if (!entry || entry.resetAt <= now) {
    attempts.set(key, { count: 1, resetAt: now + WINDOW_MS });
    return { allowed: true, retryAfter: 0 };
  }
  entry.count += 1;
  if (entry.count > MAX_ATTEMPTS) {
    return { allowed: false, retryAfter: Math.ceil((entry.resetAt - now) / 1000) };
  }
  return { allowed: true, retryAfter: 0 };
}

export function clearRateLimit(key) {
  attempts.delete(key);
}

export function verifyCredentials(username, password) {
  const okUser = safeEqual(username ?? '', config.admin.user);
  const okPass = safeEqual(password ?? '', config.admin.password);
  return okUser && okPass;
}

export function requireAdmin(req, res, next) {
  const session = getSession(req);
  if (!session) {
    // req.path es relativo al router, por eso se usa originalUrl.
    if ((req.originalUrl || req.url).startsWith('/api/')) {
      return res.status(401).json({ error: 'Sesion no valida o expirada.' });
    }
    return res.redirect(303, '/entrar');
  }
  req.admin = session;
  next();
}
