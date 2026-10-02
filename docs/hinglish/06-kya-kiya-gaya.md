# Part 6 - Project Banate Waqt Kya-Kya Kiya Gaya

Yeh part project ki **history** hai: kis order mein kya bana aur kyun. Interview mein "aapne project kaise banaya?" ka jawab yahi hai.

## Step 1 - Laptop check kiya

Sabse pehle dekha ki laptop pe kya installed hai:

| Tool | Mila? |
|---|---|
| Python 3.14 | Haan |
| Git 2.54 | Haan |
| Minikube v1.38 | Haan |
| kubectl v1.36 | Haan |
| Docker | **Nahi** |
| WSL2 | **Nahi** |
| RAM / CPU | 32 GB / 12 threads (kaafi hai) |

**Seekh:** kaam shuru karne se pehle environment check karo. Andaze pe mat chalo.

Git ki global identity bhi check ki, aur repo mein author **Radhika Agarwal <theradhika2410@gmail.com>** set kiya.

## Step 2 - Project folder aur Git repo

- Folder banaya: `C:\Users\sunil\projects\k8s-flask-monitoring`
- `git init -b main`: repo banaya, branch ka naam `main`
- Folders banaye: `app`, `tests`, `k8s`, `monitoring/dashboards`, `docs/screenshots`, `scripts`
- `.venv` banaya aur libraries install ki: Flask, prometheus-client, gunicorn, pytest, pyyaml, reportlab, svglib

## Step 3 - Phase 1: architecture diagram (commit 1)

`docs/architecture.svg` banaya. SVG ek text-based image format hai, jo GitHub pe seedha dikhta hai aur Git mein diff bhi hota hai. Saath mein `.gitignore` bhi banaya.

## Step 4 - Phase 2: Flask app (commit 2)

`config.py`, `app.py`, `gunicorn.conf.py`, `requirements.txt` aur tests likhe.

**Check kaise kiya:**

1. `python -m pytest` chalaya, aur 5 tests pass hue
2. App ko local chalaya (`PORT=5055 python app.py`) aur `curl` se `/health`, `/work`, `/metrics` aur `/` check kiye. Sab sahi jawab de rahe the

**Seekh:** pehle chhote level pe test karo (local), phir bade pe (Docker, Kubernetes).

## Step 5 - Phase 3: Docker (commit 3)

`Dockerfile`, `.dockerignore` aur `.gitattributes` banaye.

**Ek problem aayi:** commit karte waqt Git ne warning di: *"LF will be replaced by CRLF"*. Yeh Windows ki line endings ki problem hai. Agar shell scripts CRLF ke saath jaate to Linux container mein toot jaate. **Solution:** `.gitattributes` mein `eol=lf` likha aur `git add --renormalize .` chalaya.

## Step 6 - Phases 5-6: Kubernetes YAML (commit 4)

`configmap.yaml`, `deployment.yaml` (replicas, probes, limits, rolling update) aur `service.yaml` banaye. Saath mein `test_manifests.py` likha, jo cluster ke bina YAML ki galtiyan pakadta hai.

## Step 7 - Phases 7-8: monitoring (commit 5)

`00-namespace.yaml`, `10-prometheus.yaml`, `20-grafana.yaml` aur `dashboards/flask-app.json` banaye.

**Design decisions:**

| Decision | Kyun |
|---|---|
| Helm nahi, plain YAML | Har line samajh aaye |
| Files pe number (`00-`, `10-`, `20-`) | Apply ka order sahi rahe |
| cAdvisor API server proxy se | Har cluster pe chale, certificate ki jhanjhat nahi |
| Pods ko port **naam** se scrape kiya | Port number do jagah na likhna pade |
| Dashboard alag JSON file mein | Ek hi source; Grafana UI mein import bhi ho sakta hai |
| Dashboard descriptions mein limits ke numbers nahi likhe | Woh deployment.yaml mein hain. Do jagah hote to ek din alag ho jaate |

## Step 8 - Scripts (commit 6)

`deploy.sh`, `load.sh` aur `teardown.sh` likhe. `bash -n` se syntax check kiya. `git update-index --chmod=+x` se Git mein executable mark kiya, taaki Linux/Mac pe seedha `./scripts/deploy.sh` chale.

**Ek sudhaar:** `load.sh` pehle sirf ek client chalata tha. Socha to samajh aaya ki ek client se CPU limit tak kabhi nahi pahunchenge (ek baar mein ek hi request, ek hi pod pe). Isliye **parallel clients** ka option joda: `./scripts/load.sh 500 6`.

**Ek aur sudhaar:** OOM test mein pehle sirf memory limit 20Mi kam ki thi. Lekin request (64Mi) limit se zyada nahi ho sakti, aur Kubernetes woh change reject kar deta. Isliye command mein request aur limit dono 16Mi kiye.

## Step 9 - Phases 9-10: docs aur PDF (commit 7)

- `README.md`: GitHub pe sabse pehle yahi dikhta hai
- `docs/guide.md`: 10 phases, har command ki explanation (English)
- `docs/troubleshooting.md` aur `docs/interview-prep.md`
- `scripts/build_pdf.py` se English PDF banaya

**PDF check kiya:** pages ko image mein render karke dekha. Do problems mili:

1. Diagram ke kuch labels lines ke upar aa rahe the, to SVG mein positions badli
2. Kuch headings page ke end mein akeli reh jaati thi aur content agle page pe chala jaata tha. Headings ko `keepWithNext` diya

## Step 10 - Author theek kiya

Pehle commits galti se doosre naam se ban gaye the. Push se **pehle** saare 7 commits ka author badla:

```bash
git config user.name "Radhika Agarwal"
git config user.email "theradhika2410@gmail.com"
git rebase --root --exec "git commit --amend --no-edit --reset-author"
```

`rebase --root --exec` ka matlab hai pehle commit se shuru karke har commit pe yeh command chalao. `--reset-author` = author ko current config se badlo.

**Zaroori:** history rewrite **sirf push se pehle** karna safe hai. Push ke baad karoge to doosron ki copy se mismatch hoga aur force push karna padega.

## Step 11 - GitHub pe push

```bash
git remote add origin https://github.com/radhikaa06/k8s-flask-monitoring.git
git ls-remote origin       # check: repo khaali hai na?
git push -u origin main
```

7 commits GitHub pe pahunch gaye.

## Step 12 - Hinglish PDF (yeh document)

`docs/hinglish/` mein 10 Markdown files likhi, aur `build_pdf.py` mein "edition" ka option joda taaki same script dono PDF banaye (DRY).

## Abhi kya baaki hai

| Kaam | Status | Kyun |
|---|---|---|
| Code, YAML, scripts, docs | Ho gaya | - |
| Tests (10) | Pass | - |
| GitHub push | Ho gaya | - |
| **Minikube pe asli deploy** | **Baaki** | Laptop pe Docker aur WSL2 nahi hain |
| **Grafana screenshots** | **Baaki** | Deploy ke baad hi milenge |
| GitHub description/topics | Baaki | Website pe 2 minute ka kaam |

**Imaandari se:** abhi tak code ko cluster pe chala ke verify **nahi** kiya gaya hai. Tests sirf app aur YAML ki consistency check karte hain. Asli verification Part 7 follow karke hoga. Usme koi error aaye to Part 8 ka troubleshooting use karo.
