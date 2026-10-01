/* ============================================================================
 * The Diamonds League · marca de agua de autoría
 * neptun / andres / Dvskked — github.com/Dvskked
 * Copyright (c) The Diamonds League. Conserva este aviso de autoría.
 * ========================================================================== */
import { Router } from 'express';
import { getData, update, makeId, isValidId } from '../db.js';
import { buildSeed } from '../seed.js';
import { computeStandings, nextMatch } from '../standings.js';
import {
  createToken,
  clearCookie,
  sessionCookie,
  getSession,
  requireAdmin,
  verifyCredentials,
  checkRateLimit,
  clearRateLimit
} from '../auth.js';
import { config } from '../config.js';

const str = (value, max = 400) => String(value ?? '').trim().slice(0, max);
const num = (value) => {
  if (value === '' || value === null || value === undefined) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
};
const bool = (value) => value === true || value === 'true' || value === 'on' || value === 1;

const oneOf = (value, allowed, fallback) => (allowed.includes(value) ? value : fallback);

const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const TIME_RE = /^([01]\d|2[0-3]):[0-5]\d$/;

/**
 * Cada coleccion expone: prefijo de id, campos permitidos y como sanearlos.
 * El panel de administracion se construye a partir de esta misma tabla,
 * asi que anadir un campo aqui lo hace disponible tambien en la UI.
 */
const collections = {
  teams: {
    prefix: 'team',
    label: 'Equipos',
    fields: {
      name: (v) => str(v, 60),
      division: (v) => oneOf(v, ['d1', 'd2'], 'd1'),
      coach: (v) => str(v, 60),
      note: (v) => str(v, 200)
    },
    required: ['name']
  },
  matches: {
    prefix: 'match',
    label: 'Partidos',
    fields: {
      division: (v) => oneOf(v, ['d1', 'd2'], 'd1'),
      stage: (v) => oneOf(v, ['liga', 'playoffs'], 'liga'),
      journey: (v) => num(v),
      journeyLabel: (v) => str(v, 60),
      date: (v) => {
        const value = str(v, 10);
        return DATE_RE.test(value) ? value : '';
      },
      time: (v) => {
        const value = str(v, 5);
        return TIME_RE.test(value) ? value : '';
      },
      home: (v) => str(v, 60),
      away: (v) => str(v, 60),
      homeGoals: (v) => num(v),
      awayGoals: (v) => num(v),
      status: (v) => oneOf(v, ['programado', 'en-vivo', 'finalizado', 'wo', 'pospuesto', 'por-definir'], 'programado'),
      replay: (v) => str(v, 400),
      notes: (v) => str(v, 400)
    },
    required: ['home', 'away']
  },
  news: {
    prefix: 'news',
    label: 'Noticias',
    fields: {
      title: (v) => str(v, 160),
      category: (v) => str(v, 60),
      excerpt: (v) => str(v, 400),
      body: (v) => str(v, 4000),
      date: (v) => {
        const value = str(v, 10);
        return DATE_RE.test(value) ? value : '';
      },
      author: (v) => str(v, 60),
      image: (v) => str(v, 300),
      pinned: (v) => bool(v)
    },
    required: ['title']
  },
  announcements: {
    prefix: 'ann',
    label: 'Anuncios',
    fields: {
      title: (v) => str(v, 160),
      kicker: (v) => str(v, 60),
      season: (v) => str(v, 40),
      kind: (v) => oneOf(v, ['awards', 'registration', 'general'], 'general'),
      date: (v) => {
        const value = str(v, 10);
        return DATE_RE.test(value) ? value : '';
      },
      day: (v) => str(v, 4),
      month: (v) => str(v, 12),
      year: (v) => str(v, 8),
      text: (v) => str(v, 2000),
      closing: (v) => str(v, 800),
      warning: (v) => str(v, 400)
    },
    required: ['title']
  },
  awards: {
    prefix: 'award',
    label: 'Galería de premios',
    fields: {
      title: (v) => str(v, 160),
      team: (v) => str(v, 80),
      text: (v) => str(v, 300),
      season: (v) => str(v, 40),
      division: (v) => oneOf(v, ['d1', 'd2', 'ambas'], 'ambas'),
      category: (v) => oneOf(v, ['premios', 'rankings', 'campeones'], 'premios'),
      image: (v) => str(v, 300)
    },
    required: ['title']
  },
  pubs: {
    prefix: 'room',
    label: 'Salas públicas',
    fields: {
      label: (v) => str(v, 30),
      name: (v) => str(v, 60),
      url: (v) => {
        const value = str(v, 400);
        return /^https:\/\//i.test(value) ? value : '';
      },
      status: (v) => oneOf(v, ['ABIERTA', 'CERRADA', 'MANTENIMIENTO'], 'ABIERTA'),
      players: (v) => num(v),
      note: (v) => str(v, 200)
    },
    required: ['url']
  },
  important: {
    prefix: 'imp',
    label: 'Importante',
    fields: {
      title: (v) => str(v, 120),
      description: (v) => str(v, 240),
      kind: (v) => oneOf(v, ['link', 'external', 'status'], 'link'),
      href: (v) => str(v, 400),
      cta: (v) => str(v, 40)
    },
    required: ['title']
  },
  staff: {
    prefix: 'staff',
    label: 'Equipo de admins',
    fields: {
      name: (v) => str(v, 60),
      username: (v) => str(v, 60),
      role: (v) => oneOf(v, ['Owner', 'DESARROLLADOR', 'Master', 'Staff', 'Moderador'], 'Staff'),
      bio: (v) => str(v, 300),
      avatar: (v) => str(v, 300),
      banner: (v) => str(v, 300),
      focus: (v) => str(v, 80),
      github: (v) => str(v, 60),
      instagram: (v) => str(v, 60),
      discord: (v) => str(v, 60),
      available: (v) => bool(v)
    },
    required: ['name']
  }
};

function sanitize(collection, payload, base = {}) {
  const clean = { ...base };
  for (const [key, cleanValue] of Object.entries(collection.fields)) {
    if (payload && Object.prototype.hasOwnProperty.call(payload, key)) {
      clean[key] = cleanValue(payload[key]);
    }
  }
  return clean;
}

function validate(collection, item) {
  const errors = [];
  for (const key of collection.required) {
    const value = item[key];
    if (value === null || value === undefined || String(value).trim() === '') {
      errors.push(`El campo "${key}" es obligatorio.`);
    }
  }
  return errors;
}

export const schema = Object.fromEntries(
  Object.entries(collections).map(([key, value]) => [key, { label: value.label, fields: Object.keys(value.fields) }])
);

export const adminRouter = Router();

adminRouter.post('/login', (req, res) => {
  const key = req.ip || 'desconocido';
  const limit = checkRateLimit(key);
  if (!limit.allowed) {
    return res.status(429).json({
      error: `Demasiados intentos. Intenta de nuevo en ${Math.ceil(limit.retryAfter / 60)} minuto(s).`
    });
  }
  const { username, password } = req.body || {};
  if (!verifyCredentials(username, password)) {
    return res.status(401).json({ error: 'Usuario o contraseña incorrectos.' });
  }
  clearRateLimit(key);
  res.setHeader('Set-Cookie', sessionCookie(createToken(config.admin.user)));
  res.json({ ok: true, user: config.admin.user });
});

adminRouter.post('/logout', (req, res) => {
  res.setHeader('Set-Cookie', clearCookie());
  res.json({ ok: true });
});

adminRouter.get('/session', (req, res) => {
  const session = getSession(req);
  res.set('Cache-Control', 'no-store');
  res.json({ authenticated: Boolean(session), user: session?.u ?? null });
});

adminRouter.use(requireAdmin);

adminRouter.get('/data', async (req, res) => {
  const data = await getData();
  res.set('Cache-Control', 'no-store');
  res.json(data);
});

adminRouter.get('/standings', async (req, res) => {
  const data = await getData();
  res.set('Cache-Control', 'no-store');
  res.json({
    d1: computeStandings({ ...data, divisionId: 'd1' }),
    d2: computeStandings({ ...data, divisionId: 'd2' }),
    next: nextMatch(data.matches, data.divisions)
  });
});

for (const [name, collection] of Object.entries(collections)) {
  const path = `/${name}`;

  adminRouter.post(path, async (req, res, next) => {
    try {
      const item = sanitize(collection, req.body, { id: makeId(collection.prefix) });
      const errors = validate(collection, item);
      if (errors.length) return res.status(400).json({ error: errors[0] });
      await update((draft) => {
        draft[name].unshift(item);
      });
      res.status(201).json(item);
    } catch (error) {
      next(error);
    }
  });

  adminRouter.put(`${path}/:id`, async (req, res, next) => {
    try {
      if (!isValidId(req.params.id)) return res.status(400).json({ error: 'Identificador no valido.' });
      let saved = null;
      let found = false;
      await update((draft) => {
        const index = draft[name].findIndex((entry) => entry.id === req.params.id);
        if (index === -1) return;
        found = true;
        const merged = sanitize(collection, req.body, draft[name][index]);
        const errors = validate(collection, merged);
        if (errors.length) throw Object.assign(new Error(errors[0]), { status: 400 });
        draft[name][index] = merged;
        saved = merged;
      });
      if (!found) return res.status(404).json({ error: 'Registro no encontrado.' });
      res.json(saved);
    } catch (error) {
      if (error.status === 400) return res.status(400).json({ error: error.message });
      next(error);
    }
  });

  adminRouter.delete(`${path}/:id`, async (req, res, next) => {
    try {
      if (!isValidId(req.params.id)) return res.status(400).json({ error: 'Identificador no valido.' });
      let removed = false;
      await update((draft) => {
        const index = draft[name].findIndex((entry) => entry.id === req.params.id);
        if (index === -1) return;
        draft[name].splice(index, 1);
        removed = true;
      });
      if (!removed) return res.status(404).json({ error: 'Registro no encontrado.' });
      res.json({ ok: true });
    } catch (error) {
      next(error);
    }
  });
}

adminRouter.put('/settings', async (req, res, next) => {
  try {
    const allowed = {
      leagueName: (v) => str(v, 80),
      shortName: (v) => str(v, 20),
      tagline: (v) => str(v, 120),
      description: (v) => str(v, 500),
      season: (v) => str(v, 40),
      seasonNumber: (v) => num(v),
      modality: (v) => str(v, 40),
      status: (v) => oneOf(v, ['ACTIVA', 'EN PAUSA', 'CERRADA'], 'ACTIVA'),
      statusNote: (v) => str(v, 200),
      server: (v) => str(v, 60),
      map: (v) => str(v, 80),
      matchDuration: (v) => str(v, 120),
      tolerance: (v) => str(v, 60),
      pointsWin: (v) => num(v) ?? 3,
      pointsDraw: (v) => num(v) ?? 1,
      tiktok: (v) => str(v, 300),
      tiktokHandle: (v) => str(v, 60),
      founded: (v) => str(v, 10)
    };
    let saved = null;
    await update((draft) => {
      for (const [key, cleanValue] of Object.entries(allowed)) {
        if (Object.prototype.hasOwnProperty.call(req.body || {}, key)) {
          draft.settings[key] = cleanValue(req.body[key]);
        }
      }
      saved = draft.settings;
    });
    res.json(saved);
  } catch (error) {
    next(error);
  }
});

adminRouter.put('/match-config', async (req, res, next) => {
  try {
    const list = Array.isArray(req.body) ? req.body : [];
    const clean = list
      .filter((item) => item && typeof item === 'object')
      .slice(0, 12)
      .map((item) => ({ label: str(item.label, 40), value: str(item.value, 160) }))
      .filter((item) => item.label && item.value);
    await update((draft) => {
      draft.matchConfig = clean;
    });
    res.json(clean);
  } catch (error) {
    next(error);
  }
});

adminRouter.put('/rules', async (req, res, next) => {
  try {
    const list = Array.isArray(req.body) ? req.body : [];
    const clean = list.slice(0, 12).map((group) => ({
      id: str(group?.id, 40) || makeId('rules'),
      title: str(group?.title, 60),
      summary: str(group?.summary, 300),
      items: Array.isArray(group?.items)
        ? group.items.slice(0, 60).map((item) => ({ title: str(item?.title, 120), text: str(item?.text, 600) }))
        : [],
      blocks: Array.isArray(group?.blocks)
        ? group.blocks.slice(0, 20).map((block) => ({
            title: str(block?.title, 120),
            subtitle: str(block?.subtitle, 120),
            text: str(block?.text, 800),
            list: Array.isArray(block?.list) ? block.list.slice(0, 40).map((li) => str(li, 300)) : []
          }))
        : [],
      cards: Array.isArray(group?.cards)
        ? group.cards.slice(0, 12).map((card) => ({
            title: str(card?.title, 80),
            kicker: str(card?.kicker, 40),
            tone: oneOf(card?.tone, ['info', 'warn', 'danger'], 'info'),
            list: Array.isArray(card?.list) ? card.list.slice(0, 20).map((li) => str(li, 200)) : [],
            text: str(card?.text, 400)
          }))
        : []
    }));
    await update((draft) => {
      draft.rules = clean;
    });
    res.json(clean);
  } catch (error) {
    next(error);
  }
});

adminRouter.put('/divisions', async (req, res, next) => {
  try {
    const list = Array.isArray(req.body) ? req.body : [];
    const clean = list.slice(0, 8).map((division) => ({
      id: oneOf(division?.id, ['d1', 'd2'], 'd1'),
      name: str(division?.name, 60),
      code: str(division?.code, 10),
      season: str(division?.season, 40),
      summary: str(division?.summary, 400),
      teams: num(division?.teams) ?? 0,
      journeys: num(division?.journeys) ?? 0,
      playoffs: num(division?.playoffs) ?? 0,
      relegation: str(division?.relegation, 80),
      promotion: str(division?.promotion, 80),
      phases: Array.isArray(division?.phases)
        ? division.phases.slice(0, 8).map((phase) => ({
            label: str(phase?.label, 40),
            title: str(phase?.title, 80),
            text: str(phase?.text, 600),
            note: str(phase?.note, 300)
          }))
        : [],
      movement: {
        title: str(division?.movement?.title, 60),
        items: Array.isArray(division?.movement?.items)
          ? division.movement.items.slice(0, 8).map((item) => ({
              place: str(item?.place, 60),
              label: str(item?.label, 80),
              text: str(item?.text, 300)
            }))
          : []
      },
      rules: Array.isArray(division?.rules)
        ? division.rules.slice(0, 12).map((rule) => ({ title: str(rule?.title, 80), text: str(rule?.text, 500) }))
        : []
    }));
    await update((draft) => {
      draft.divisions = clean;
    });
    res.json(clean);
  } catch (error) {
    next(error);
  }
});

adminRouter.post('/reset', async (req, res, next) => {
  try {
    if (req.body?.confirm !== 'RESTABLECER') {
      return res.status(400).json({ error: 'Debes confirmar con el texto RESTABLECER.' });
    }
    const seed = buildSeed();
    await update((draft) => {
      for (const key of Object.keys(seed)) {
        if (key === 'version') continue;
        draft[key] = seed[key];
      }
    });
    res.json({ ok: true });
  } catch (error) {
    next(error);
  }
});
