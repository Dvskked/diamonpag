const DIAS = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];
const DIAS_CORTO = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
const MESES = [
  'enero',
  'febrero',
  'marzo',
  'abril',
  'mayo',
  'junio',
  'julio',
  'agosto',
  'septiembre',
  'octubre',
  'noviembre',
  'diciembre'
];
const MESES_CORTO = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];

const toDate = (iso) => {
  if (!iso) return null;
  const [y, m, d] = String(iso).split('-').map(Number);
  if (!y || !m || !d) return null;
  const date = new Date(Date.UTC(y, m - 1, d));
  return Number.isNaN(date.getTime()) ? null : date;
};

export const esc = (value) =>
  String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');

export const attr = esc;

export function longDate(iso) {
  const date = toDate(iso);
  if (!date) return 'Fecha por confirmar';
  return `${DIAS[date.getUTCDay()]} ${String(date.getUTCDate()).padStart(2, '0')} de ${
    MESES[date.getUTCMonth()]
  } de ${date.getUTCFullYear()}`;
}

export function dayLabel(iso) {
  const date = toDate(iso);
  if (!date) return '—';
  return `${DIAS_CORTO[date.getUTCDay()]} ${String(date.getUTCDate()).padStart(2, '0')}/${
    MESES_CORTO[date.getUTCMonth()]
  }`;
}

export function shortDate(iso) {
  const date = toDate(iso);
  if (!date) return 'Por definir';
  return `${String(date.getUTCDate()).padStart(2, '0')}/${MESES_CORTO[date.getUTCMonth()]} ${date.getUTCFullYear()}`;
}

export function timeLabel(value) {
  if (!value) return '—';
  const [h, m] = String(value).split(':');
  const hour = Number(h);
  if (!Number.isFinite(hour)) return '—';
  const suffix = hour >= 12 ? 'PM' : 'AM';
  const display = hour % 12 === 0 ? 12 : hour % 12;
  return `${display}:${m} ${suffix}`;
}

export const statusLabel = {
  programado: 'Programado',
  'en-vivo': 'En vivo',
  finalizado: 'Finalizado',
  wo: 'W.O.',
  pospuesto: 'Pospuesto',
  'por-definir': 'Por definir'
};

export const stageLabel = { liga: 'Liga regular', playoffs: 'Playoffs' };

export const json = (value) =>
  JSON.stringify(value, null, 2).replace(/</g, '\\u003c');

export const slug = (value) =>
  String(value ?? '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 80);

export const plural = (n, one, many) => `${n} ${n === 1 ? one : many}`;

export const list = (items) =>
  items
    .map((item) => `<li>${esc(typeof item === 'string' ? item : item.text)}</li>`)
    .join('');
