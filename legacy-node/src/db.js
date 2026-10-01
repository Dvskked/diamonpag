/* ============================================================================
 * The Diamonds League · marca de agua de autoría
 * neptun / andres / Dvskked — github.com/Dvskked
 * Copyright (c) The Diamonds League. Conserva este aviso de autoría.
 * ========================================================================== */
import { readFile, writeFile, rename, mkdir, access } from 'node:fs/promises';
import path from 'node:path';
import { config } from './config.js';
import { buildSeed } from './seed.js';

let cache = null;
let writeQueue = Promise.resolve();

async function persist(data) {
  const file = config.dataFile;
  const tmp = `${file}.${process.pid}.tmp`;
  await mkdir(path.dirname(file), { recursive: true });
  await writeFile(tmp, JSON.stringify(data, null, 2), 'utf8');
  await rename(tmp, file);
}

async function load() {
  try {
    await access(config.dataFile);
    const raw = await readFile(config.dataFile, 'utf8');
    const parsed = JSON.parse(raw);
    cache = { ...buildSeed(), ...parsed, settings: { ...buildSeed().settings, ...(parsed.settings || {}) } };
  } catch {
    cache = buildSeed();
    await persist(cache);
  }
  return cache;
}

export async function getData() {
  if (!cache) await load();
  return cache;
}

export function getDataSync() {
  if (!cache) throw new Error('La base de datos aun no esta cargada. Usa getData() primero.');
  return cache;
}

/**
 * Aplica una mutacion sobre una copia del documento y la persiste de forma atomica.
 * Las escrituras se serializan para evitar condiciones de carrera.
 */
export function update(mutator) {
  const run = async () => {
    const current = await getData();
    const draft = structuredClone(current);
    const result = await mutator(draft);
    draft.updatedAt = new Date().toISOString();
    await persist(draft);
    cache = draft;
    return result;
  };
  writeQueue = writeQueue.then(run, run);
  return writeQueue;
}

export function makeId(prefix) {
  return `${prefix}-${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`;
}

export const isValidId = (value) => typeof value === 'string' && /^[A-Za-z0-9_-]{1,64}$/.test(value);
