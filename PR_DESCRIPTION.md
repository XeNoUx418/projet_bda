Title: feat: filter dashboards by periode_id + student personal view

Summary

This PR implements session (periode) filtering for the Vice-Dean analytics dashboard and adds a student-personal schedule endpoint and UI improvements.

What changed

Backend (API)
- Add optional `periode_id` query parameter to dashboard endpoints so they can return metrics scoped to a selected exam period (session).
  - Modified endpoints: `GET /api/dashboard/kpis`, `/api/dashboard/room_distribution`, `/api/dashboard/top_rooms`, `/api/dashboard/prof_load`, `/api/dashboard/prof_conflicts`.
  - When `periode_id` is provided, queries join `creneaux` and filter using `c.id_periode = %s`. If not provided, endpoints retain previous global behavior.
- Add new endpoint: `GET /api/student_schedule?student_id=<id>&periode_id=<pid>` returning the schedule rows for a single student (joins `etudiants -> groupes -> planning_groupes -> planning_examens` etc.).

Frontend
- Add `select#periode` and `button#refresh` to the dashboard UI to select a session.
  - File: `frontend/pages/dashboard.html`.
- Update dashboard JS to load periods and pass `periode_id` to dashboard API calls.
  - File: `frontend/assets/js/dashboard.js`.
- Update frontend API helper to accept `periode_id` on dashboard calls.
  - File: `frontend/assets/js/api.js`.
- Student UI improvements: per-group tables rendering; personal view by entering `ID Etudiant`.
  - Files: `frontend/pages/student.html`, `frontend/assets/js/student.js`, `frontend/assets/js/api.js` (added `studentSchedule` call)

Files modified
- api/app_api.py
- frontend/assets/js/api.js
- frontend/pages/student.html
- frontend/assets/js/student.js
- frontend/pages/dashboard.html
- frontend/assets/js/dashboard.js

Commit message

feat(dashboard): add periode_id filter + frontend selector; feat(student): student schedule endpoint and per-group view

How to create branch and PR locally

1) From repo root (where .git is located):

```bash
# create branch and commit current changes
git checkout -b feature/periode-filter-dashboard
git add api/app_api.py frontend/assets/js/api.js frontend/pages/student.html frontend/assets/js/student.js frontend/pages/dashboard.html frontend/assets/js/dashboard.js
git commit -m "feat(dashboard): add periode_id filter + frontend selector; feat(student): student schedule endpoint and per-group view"

# push branch to origin
git push -u origin feature/periode-filter-dashboard

# create a PR using GitHub CLI (install gh and authenticate)
gh pr create --base main --head feature/periode-filter-dashboard --title "feat: filter dashboards by periode_id + student personal view" --body-file PR_DESCRIPTION.md
```

If you don't use `gh`, create a PR using your Git hosting web UI and paste the PR description from `PR_DESCRIPTION.md`.

Suggested PR details
- Base branch: `main` (or `develop` if you use a different workflow)
- Assignee / reviewers: your team lead or the maintainer used in your project
- Labels: `feature`, `dashboard`, `ui`

Testing notes (what to run locally after pulling)

1) Start backend API:
```powershell
python api/app_api.py
```

2) Open dashboard UI (`frontend/pages/dashboard.html`) and select a session in the new selector; click "Actualiser" to reload the filtered view. KPIs, charts and tables should reflect the selected `periode_id`.

3) Test endpoints via curl (replace ids):
```bash
curl "http://localhost:5000/api/dashboard/kpis?periode_id=10"
curl "http://localhost:5000/api/student_schedule?student_id=123&periode_id=10"
```

4) SQL snippets to verify correctness (replace `10` with your periode_id):
```sql
-- total planned for periode
SELECT COUNT(*) as n
FROM planning_examens pe
JOIN creneaux c ON pe.id_creneau = c.id_creneau
WHERE c.id_periode = 10;

-- merged count for periode
SELECT COUNT(DISTINCT pg.id_planning) as n
FROM planning_groupes pg
JOIN planning_examens pe ON pg.id_planning = pe.id_planning
JOIN creneaux c ON pe.id_creneau = c.id_creneau
WHERE pg.merged_groups IS NOT NULL AND c.id_periode = 10;

-- room distribution for periode
SELECT l.type, COUNT(pe.id_planning) as usage_count
FROM lieux_examen l
LEFT JOIN planning_examens pe ON l.id_lieu = pe.id_lieu
LEFT JOIN creneaux c ON pe.id_creneau = c.id_creneau
WHERE c.id_periode = 10
GROUP BY l.type;
```

Notes
- `periode_id` is optional; if missing, endpoints return global data as before.
- I could not create the branch/PR from this environment because the workspace is not a git repository connected to a remote. Please run the commands above in your local repo—I included `PR_DESCRIPTION.md` so you can use it as the PR body.

If you'd like, I can also prepare unit test scripts (pytest) or SQL-based checks to include in the PR.