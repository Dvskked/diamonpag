/**
 * Calcula la tabla de posiciones de una division a partir de los partidos
 * finalizados. Los nombres de equipo se guardan tal cual aparecen en el
 * calendario, por eso la tabla se agrupa por nombre normalizado.
 */

const normalize = (value) =>
  String(value ?? '')
    .trim()
    .toUpperCase();

export function computeStandings({ teams = [], matches = [], divisionId, settings = {} }) {
  const win = Number(settings.pointsWin ?? 3);
  const draw = Number(settings.pointsDraw ?? 1);

  const rows = new Map();
  const ensure = (name) => {
    const key = normalize(name);
    if (!key) return null;
    if (!rows.has(key)) {
      rows.set(key, {
        key,
        name: String(name).trim(),
        played: 0,
        won: 0,
        drawn: 0,
        lost: 0,
        goalsFor: 0,
        goalsAgainst: 0,
        points: 0
      });
    }
    return rows.get(key);
  };

  for (const team of teams) {
    if (team.division === divisionId) ensure(team.name);
  }

  for (const match of matches) {
    if (match.division !== divisionId) continue;
    if (match.status !== 'finalizado') continue;
    const home = ensure(match.home);
    const away = ensure(match.away);
    const hg = Number(match.homeGoals);
    const ag = Number(match.awayGoals);
    if (!home || !away || !Number.isFinite(hg) || !Number.isFinite(ag)) continue;
    if (home.key === away.key) continue;

    home.played += 1;
    away.played += 1;
    home.goalsFor += hg;
    home.goalsAgainst += ag;
    away.goalsFor += ag;
    away.goalsAgainst += hg;

    if (hg > ag) {
      home.won += 1;
      home.points += win;
      away.lost += 1;
    } else if (hg < ag) {
      away.won += 1;
      away.points += win;
      home.lost += 1;
    } else {
      home.drawn += 1;
      away.drawn += 1;
      home.points += draw;
      away.points += draw;
    }
  }

  return [...rows.values()]
    .map((row) => ({ ...row, goalDiff: row.goalsFor - row.goalsAgainst }))
    .sort(
      (a, b) =>
        b.points - a.points ||
        b.goalDiff - a.goalDiff ||
        b.goalsFor - a.goalsFor ||
        a.name.localeCompare(b.name, 'es')
    )
    .map((row, index) => ({ ...row, position: index + 1 }));
}

export function nextMatch(matches = [], divisions = []) {
  const now = Date.now();
  const candidates = matches
    .filter((m) => m.status === 'programado' && m.date)
    .map((m) => ({ ...m, stamp: new Date(`${m.date}T${(m.time || '00:00')}:00`).getTime() }))
    .filter((m) => !Number.isNaN(m.stamp) && m.stamp >= now - 3 * 60 * 60 * 1000)
    .sort((a, b) => a.stamp - b.stamp);
  const match = candidates[0];
  if (!match) return null;
  const division = divisions.find((d) => d.id === match.division);
  return { ...match, divisionName: division ? division.name : '' };
}
