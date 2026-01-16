#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/test_dashboard_filters.sh [PERIODE_ID] [STUDENT_ID]
# Example: ./scripts/test_dashboard_filters.sh 10 123

PERIODE_ID=${1:-10}
STUDENT_ID=${2:-123}
API_BASE=${API_BASE:-http://localhost:5000/api}

MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASS='bac@2021'
MYSQL_DB=exam_timetabling

# Helpers
has_cmd(){ command -v "$1" >/dev/null 2>&1; }

echo "=== Dashboard filter tests ==="
echo "Periode ID: $PERIODE_ID"
echo "Student ID: $STUDENT_ID"
echo "API base: $API_BASE"

# Check dependencies
if ! has_cmd curl; then
  echo "curl is required" >&2
  exit 2
fi

if ! has_cmd mysql; then
  echo "mysql client not found; SQL checks will be skipped" >&2
  MYSQL_OK=false
else
  MYSQL_OK=true
fi

if has_cmd jq; then
  JQ=1
else
  JQ=0
fi

# Fetch KPI from API
echo "\n-- API: KPIs --"
KPI_JSON=$(curl -sSf "$API_BASE/dashboard/kpis?periode_id=$PERIODE_ID" || true)
if [ "$JQ" -eq 1 ]; then
  echo "$KPI_JSON" | jq '.'
  KPIS_TOTAL=$(echo "$KPI_JSON" | jq '.data.total_planned')
  KPIS_MERGED=$(echo "$KPI_JSON" | jq '.data.merged_count')
  KPIS_SPLIT=$(echo "$KPI_JSON" | jq '.data.split_count')
else
  echo "$KPI_JSON"
fi

# Room distribution
echo "\n-- API: Room distribution --"
ROOM_JSON=$(curl -sSf "$API_BASE/dashboard/room_distribution?periode_id=$PERIODE_ID" || true)
if [ "$JQ" -eq 1 ]; then
  echo "$ROOM_JSON" | jq '.'
else
  echo "$ROOM_JSON"
fi

# Top rooms
echo "\n-- API: Top rooms --"
TOPROOM_JSON=$(curl -sSf "$API_BASE/dashboard/top_rooms?periode_id=$PERIODE_ID" || true)
if [ "$JQ" -eq 1 ]; then
  echo "$TOPROOM_JSON" | jq '.'
else
  echo "$TOPROOM_JSON"
fi

# Prof load
echo "\n-- API: Prof load --"
PROF_JSON=$(curl -sSf "$API_BASE/dashboard/prof_load?periode_id=$PERIODE_ID" || true)
if [ "$JQ" -eq 1 ]; then
  echo "$PROF_JSON" | jq '.'
else
  echo "$PROF_JSON"
fi

# Conflicts
echo "\n-- API: Prof conflicts --"
CONF_JSON=$(curl -sSf "$API_BASE/dashboard/prof_conflicts?periode_id=$PERIODE_ID" || true)
if [ "$JQ" -eq 1 ]; then
  echo "$CONF_JSON" | jq '.'
else
  echo "$CONF_JSON"
fi

# Student schedule
echo "\n-- API: Student schedule --"
STU_JSON=$(curl -sSf "$API_BASE/student_schedule?student_id=$STUDENT_ID&periode_id=$PERIODE_ID" || true)
if [ "$JQ" -eq 1 ]; then
  echo "$STU_JSON" | jq '.'
else
  echo "$STU_JSON"
fi

# SQL checks (optional)
if [ "$MYSQL_OK" = true ]; then
  echo "\n-- SQL checks --"
  export MYSQL_PWD="$MYSQL_PASS"

  echo "Total planned (SQL):"
  mysql -h"$MYSQL_HOST" -u"$MYSQL_USER" -D"$MYSQL_DB" -N -e \
    "SELECT COUNT(*) FROM planning_examens pe JOIN creneaux c ON pe.id_creneau = c.id_creneau WHERE c.id_periode = ${PERIODE_ID};"

  echo "Merged count (SQL):"
  mysql -h"$MYSQL_HOST" -u"$MYSQL_USER" -D"$MYSQL_DB" -N -e \
    "SELECT COUNT(DISTINCT pg.id_planning) FROM planning_groupes pg JOIN planning_examens pe ON pg.id_planning = pe.id_planning JOIN creneaux c ON pe.id_creneau = c.id_creneau WHERE pg.merged_groups IS NOT NULL AND c.id_periode = ${PERIODE_ID};"

  echo "Room distribution (SQL):"
  mysql -h"$MYSQL_HOST" -u"$MYSQL_USER" -D"$MYSQL_DB" -N -e \
    "SELECT l.type, COUNT(pe.id_planning) FROM lieux_examen l LEFT JOIN planning_examens pe ON l.id_lieu = pe.id_lieu LEFT JOIN creneaux c ON pe.id_creneau = c.id_creneau WHERE c.id_periode = ${PERIODE_ID} GROUP BY l.type;"

  echo "Student schedule (SQL):"
  mysql -h"$MYSQL_HOST" -u"$MYSQL_USER" -D"$MYSQL_DB" -N -e \
    "SELECT c.date, TIME_FORMAT(c.heure_debut,'%H:%i') AS start, m.nom, le.nom AS room, g.code_groupe, pg.split_part FROM etudiants et JOIN groupes g ON g.id_groupe = et.id_groupe JOIN planning_groupes pg ON pg.id_groupe = g.id_groupe JOIN planning_examens pe ON pe.id_planning = pg.id_planning JOIN examens e ON e.id_examen = pe.id_examen JOIN modules m ON m.id_module = e.id_module JOIN creneaux c ON c.id_creneau = pe.id_creneau JOIN lieux_examen le ON le.id_lieu = pe.id_lieu WHERE et.id_etudiant = ${STUDENT_ID} AND c.id_periode = ${PERIODE_ID} ORDER BY c.date, c.heure_debut;"

  # unset password
  unset MYSQL_PWD
else
  echo "MySQL client not available; skipped SQL checks"
fi

echo "\n=== Done ==="
