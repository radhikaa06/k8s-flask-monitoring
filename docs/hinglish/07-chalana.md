# Part 7 - Project Chalana: Step by Step

**Terminals:**

| Naam | Kaise kholein | Kis liye |
|---|---|---|
| PowerShell (Admin) | Start, "PowerShell" type karo, right-click, "Run as administrator" | Sirf WSL install |
| PowerShell | Normal | Docker install |
| Git Bash | Project folder mein right-click, "Open Git Bash here" | **Baaki sab kuch** |

## Step 1 - WSL2 install

```powershell
wsl --install
```

- **Kya:** Windows Subsystem for Linux 2 aur Ubuntu install karta hai.
- **Kyun:** Containers Linux kernel ka feature hain. Docker Desktop WSL2 ke andar chalta hai.
- **Kahan:** PowerShell **as Administrator**.
- **Expected:** `The requested operation is successful. Changes will not be effective until the system is rebooted.` Phir **restart** karo. Ubuntu window khulegi aur username/password maangegi, jo kuch bhi rakh lo.
- **Error aaye to:**
  - `0x80370102`: BIOS mein virtualization off hai. BIOS mein **Intel VT-x** ya **AMD-V/SVM** enable karo. Task Manager, Performance, CPU mein "Virtualization: Enabled" dikhna chahiye.
  - "requires elevation": PowerShell Admin se nahi khola.
  - 0% pe atka: `wsl --install --web-download` chalao.

Check karo:
```powershell
wsl --status
```
**Expected:** `Default Version: 2`.

## Step 2 - Docker Desktop install

```powershell
winget install -e --id Docker.DockerDesktop
```

- **Kya:** Windows ke package manager se Docker Desktop install karta hai.
- **Kahan:** Normal PowerShell.
- **Iske baad:** Docker Desktop kholo, terms accept karo, aur neeche-left mein **"Engine running"** (hara) aane tak ruko.

Check karo (**naye** Git Bash mein):
```bash
docker run hello-world
```
- **Expected:** `Hello from Docker!`
- **Error:** `error during connect` matlab Docker Desktop chalu nahi hai. `docker: command not found` matlab terminal purana hai, naya kholo.

## Step 3 - Project laptop pe hai na?

Project pehle se `C:\Users\sunil\projects\k8s-flask-monitoring` mein hai. Kisi aur laptop pe ho to:

```bash
git clone https://github.com/radhikaa06/k8s-flask-monitoring.git
cd k8s-flask-monitoring
```

## Step 4 - Tests chalao (optional, bina cluster ke)

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements-dev.txt
python -m pytest
```

- **Expected:** `10 passed`.
- **Error:** `ModuleNotFoundError` matlab venv activate nahi hai. Prompt ke aage `(.venv)` dikhna chahiye.

## Step 5 - Ek command mein sab deploy

```bash
./scripts/deploy.sh
```

- **Kya karta hai (andar):**
  1. Minikube start (2 CPU, 4 GB RAM), agar pehle se nahi chal raha
  2. metrics-server addon on
  3. `docker build`, jo image `flask-app:1.0.0` banata hai
  4. `minikube image load`, jo image Minikube mein bhejta hai
  5. `kubectl apply -f k8s/`, jo app deploy karta hai
  6. `kubectl apply -f monitoring/`, jo Prometheus aur Grafana deploy karta hai
  7. Dashboard ConfigMap banata hai
  8. Sab ready hone ka wait karta hai
- **Kahan:** Git Bash, project folder. Docker Desktop chalu hona chahiye.
- **Time:** pehli baar 5-10 minute (Kubernetes aur images download hote hain).
- **Expected:** end mein `Done.` aur teen `minikube service` commands dikhenge.
- **Error aaye to:**

| Error | Matlab | Solution |
|---|---|---|
| `PROVIDER_DOCKER_NOT_RUNNING` | Docker band hai | Docker Desktop kholo |
| Memory ka error | Docker ke paas kam RAM | Docker Settings, Resources mein RAM badhao, ya `deploy.sh` mein `--memory=3072` karo |
| `Permission denied` | Script executable nahi | `bash scripts/deploy.sh` chalao |
| `$'\r': command not found` | Windows line endings | `git add --renormalize .` |
| `rollout status` timeout | Pods ready nahi hue | `kubectl get pods -A` dekho, phir Part 8 |

## Step 6 - Sab chal raha hai? Check karo

```bash
kubectl get pods -A
```

- **Kya:** saare namespaces (`-A`) ke pods dikhao.
- **Expected:**

```
NAMESPACE     NAME                          READY   STATUS    RESTARTS
default       flask-app-6b7c9d8f4-abcde     1/1     Running   0
default       flask-app-6b7c9d8f4-fghij     1/1     Running   0
default       flask-app-6b7c9d8f4-klmno     1/1     Running   0
monitoring    grafana-5f6d7c8b9-pqrst       1/1     Running   0
monitoring    prometheus-7a8b9c0d1-uvwxy    1/1     Running   0
kube-system   ...                           ...     Running   ...
```

`READY 1/1` ka matlab hai pod mein 1 container hai aur woh ready hai.

```bash
kubectl get deployment,service,endpoints
```

- **Expected:** `flask-app 3/3`, `flask-app-service NodePort 80:30080/TCP`, aur endpoints mein 3 IPs.

## Step 7 - App kholo

```bash
minikube service flask-app-service --url
```

- **Kya:** tunnel bana ke URL deta hai.
- **Kahan:** Git Bash. **Yeh terminal khula rakho**, band kiya to tunnel band.
- **Expected:** `http://127.0.0.1:54321` jaisa URL. Browser mein kholo, aur "Hello from flask-app" ke saath pod ka naam dikhega.

Load balancing dekho (naye terminal mein, URL apna daalo):
```bash
for i in 1 2 3 4 5 6; do curl -s http://127.0.0.1:54321/health; echo; done
```
**Expected:** `pod` ki value alag-alag pods ke naam dikhayegi. (Browser ek connection reuse karta hai, isliye wahan aksar same pod dikhta hai.)

## Step 8 - Prometheus kholo

```bash
minikube service prometheus -n monitoring --url
```

URL kholo, phir **Status > Targets**.

**Expected:**
- `prometheus` (1/1 up)
- `kubernetes-cadvisor` (1/1 up)
- `app-pods` (3/3 up)

**Graph** tab mein yeh queries try karo: `up`, `flask_http_requests_total`, `sum by (pod) (rate(flask_http_requests_total[1m]))`.

## Step 9 - Grafana kholo

```bash
minikube service grafana -n monitoring --url
```

- Login: `admin` / `admin`. Grafana naya password maangega, kuch bhi rakh lo (yaad rakhna).
- **Dashboards > Flask App on Kubernetes** kholo.
- **Expected:** "Healthy pods" = 3 (green). Baaki graphs idle mein lagbhag flat honge.

## Step 10 - Load do aur graphs dekho

```bash
./scripts/load.sh 50
```

- 30-60 second mein graphs hilne lagenge: requests/sec badhega, CPU badhega, aur teeno pods ki lines dikhengi.
- `Ctrl+C` se band karo.

## Step 11 - Screenshots lo

`docs/screenshots/` mein **inhi naamon** se save karo (README inhi naamon ke links deta hai):

| File | Kya capture karna hai |
|---|---|
| `grafana-dashboard.png` | Poora dashboard, load ke time |
| `prometheus-targets.png` | Status > Targets, sab up |
| `pods-running.png` | Terminal mein `kubectl get pods -A` |
| `self-healing.png` | Pod delete test (Part 8, Test 1) |

Windows pe screenshot: `Win + Shift + S`.

Phir push karo:
```bash
git add docs/screenshots
git commit -m "Add monitoring screenshots"
git push
```

## Step 12 - Kaam khatam? Band karo

```bash
./scripts/teardown.sh     # app aur monitoring hatao
minikube stop             # cluster pause (data rehta hai)
```

Agli baar `minikube start`, phir `./scripts/deploy.sh`. Cluster poora hatana ho to `minikube delete`.

## Code badla to dobara deploy kaise karein?

1. `k8s/deployment.yaml` mein image tag badlo: `flask-app:1.0.1`
2. `./scripts/deploy.sh` chalao

**Tag kyun badalna?** Same tag pe Minikube ke paas purani image hai aur `IfNotPresent` ki wajah se nayi nahi lega. Naya tag = nayi image = rolling update. Version **sirf ek jagah** (deployment.yaml) badalna hai, script baaki khud padh lega.
