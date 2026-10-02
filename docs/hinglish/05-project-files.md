# Part 5 - Hamara Project: Har File Line by Line

Poora code Appendix mein hai. Yahan har file ka **matlab** samjhaya gaya hai: kya hai, kyun hai, aur kaise kaam karta hai.

## Folder structure

```
k8s-flask-monitoring/
  app/                      Flask application
    app.py                  routes + Prometheus metrics
    config.py               saari settings ek jagah (DRY)
    gunicorn.conf.py        production server settings
    requirements.txt        libraries + versions
  k8s/                      app ke Kubernetes files
    configmap.yaml
    deployment.yaml         replicas, probes, resources
    service.yaml            NodePort 30080
  monitoring/               Prometheus + Grafana (number = order)
    00-namespace.yaml
    10-prometheus.yaml
    20-grafana.yaml
    dashboards/flask-app.json
  scripts/                  automation
    deploy.sh  load.sh  teardown.sh  build_pdf.py
  tests/                    automated tests
  docs/                     guides, diagram, PDF, screenshots
  Dockerfile  .dockerignore  .gitignore  .gitattributes
  requirements-dev.txt  pytest.ini  README.md
```

## DRY principle: project mein kahan-kahan

**DRY = Don't Repeat Yourself.** Har jaankari **sirf ek jagah** likho. Do jagah likhoge to ek din ek jagah badloge aur doosri bhool jaaoge, aur bug aayega.

| Jaankari | Sirf yahan likhi hai | Kaun-kaun use karta hai |
|---|---|---|
| Port, app name, version ke defaults | `app/config.py` | `app.py`, `gunicorn.conf.py` |
| Image tag `1.0.0` | `k8s/deployment.yaml` ki `image:` line | `deploy.sh` wahi se padhta hai aur `docker build` ko deta hai |
| Port number 5000 | `containerPort` jiska naam `http` hai | Probes, Service `targetPort`, Prometheus sab `http` naam use karte hain |
| Health check | YAML anchor `&health-check` | Readiness aur liveness dono |
| Grafana dashboard | `monitoring/dashboards/flask-app.json` | `deploy.sh` usse ConfigMap banata hai, copy nahi karta |
| Datasource uid `prometheus` | `20-grafana.yaml` | Dashboard JSON; test check karta hai ki dono match hon |
| Documentation | `docs/*.md` | README links deta hai, PDF unhi se banta hai |

**DRY ki limit bhi samjho:** Kubernetes mein label `app: flask-app` Deployment ke selector aur template dono mein likhna **zaroori** hai, kyunki Kubernetes aisa hi maangta hai. Aisi jagah humne **test** likh diya jo check karta hai ki dono match karein. Jahan repeat karna pade, wahan test se safety lo.

## app/config.py

```python
@dataclass(frozen=True)
class Settings:
    app_name: str = field(default_factory=lambda: _env("APP_NAME", "flask-app"))
    app_version: str = field(default_factory=lambda: _env("APP_VERSION", "dev"))
    app_env: str = field(default_factory=lambda: _env("APP_ENV", "local"))
    port: int = field(default_factory=lambda: int(_env("PORT", "5000")))
    hostname: str = field(default_factory=lambda: _env("HOSTNAME", "localhost"))

settings = Settings()
```

| Line | Matlab |
|---|---|
| `@dataclass(frozen=True)` | Ek simple class jiske fields baad mein **badle nahi** ja sakte (frozen) |
| `_env("APP_NAME", "flask-app")` | Environment variable `APP_NAME` ho to woh, warna `"flask-app"` |
| `int(...)` | Env variables hamesha text hote hain, port number chahiye |
| `HOSTNAME` | Kubernetes mein har pod ka HOSTNAME = pod ka naam. Isse pata chalta hai **kis pod** ne jawab diya |
| `settings = Settings()` | Ek object banao, aur baaki files `from config import settings` karti hain |

**Kahan se kya value aati hai:**

| Setting | Laptop pe | Kubernetes mein |
|---|---|---|
| `APP_VERSION` | `dev` (default) | `1.0.0` (Dockerfile ka `ENV`, jo build-arg se aaya) |
| `APP_ENV` | `local` (default) | `minikube` (ConfigMap se) |
| `HOSTNAME` | `localhost` | Pod ka naam (Kubernetes set karta hai) |

## app/app.py

### Metrics define karna

```python
REQUESTS = Counter("flask_http_requests_total", "Total HTTP requests",
                   ["method", "endpoint", "status"])
LATENCY = Histogram("flask_http_request_duration_seconds", "HTTP request latency in seconds",
                    ["endpoint"])
```

- **Counter** har request pe +1 hota hai, aur method/endpoint/status ke labels ke saath.
- **Histogram** response time ko buckets mein daalta hai (0.005s, 0.01s ... 10s), taaki p95 nikal sakein.
- Naam ke end mein `_total` aur `_seconds` Prometheus ka **naming convention** hai.

### Har request ko measure karna

```python
@app.before_request
def _start_timer():
    g.start = time.perf_counter()          # request shuru hone ka time

@app.after_request
def _record_metrics(response):
    endpoint = request.url_rule.rule if request.url_rule else "unmatched"
    if endpoint != "/metrics":
        REQUESTS.labels(request.method, endpoint, response.status_code).inc()
        LATENCY.labels(endpoint).observe(time.perf_counter() - g.start)
    return response
```

| Cheez | Matlab |
|---|---|
| `before_request` / `after_request` | Har request se pehle / baad mein yeh function chalo (hooks) |
| `g` | Flask ka per-request storage |
| `request.url_rule.rule` | Route pattern (`/work`), poora URL nahi. Yeh **cardinality** se bachata hai |
| `"unmatched"` | 404 wali requests ke liye ek hi label, taaki random URLs se lakhon series na banein |
| `!= "/metrics"` | Prometheus ke apne scrape ko count nahi karte, warna data mein noise aata |

### Routes

```python
@app.get("/health")
def health():
    if _state["healthy"]:
        return jsonify(status="ok", pod=settings.hostname)
    return jsonify(status="unhealthy", pod=settings.hostname), 503
```

Normal mein 200 deta hai. `/fail` call hone ke baad `_state["healthy"] = False` ho jaata hai aur 503 aata hai. Yeh probes ka demo dikhane ke liye hai.

```python
@app.get("/work")
def work():
    ms = min(request.args.get("ms", default=100, type=int), MAX_WORK_MS)
    deadline = time.perf_counter() + ms / 1000
    while time.perf_counter() < deadline:
        count += 1
```

Diye gaye milliseconds tak loop chala ke **CPU jalata hai**, taaki Grafana graph hile. `MAX_WORK_MS = 1000` ek safety cap hai, taaki koi `?ms=99999999` bhej ke server na atka de.

**`_state` dictionary kyun, simple variable kyun nahi?** Dictionary ko function ke andar `global` likhe bina badal sakte hain. Yeh state **har process ka alag** hai, isliye ek pod pe `/fail` karne se sirf woh pod unhealthy hota hai.

## app/gunicorn.conf.py

```python
from config import settings
bind = f"0.0.0.0:{settings.port}"   # port config.py se (DRY)
workers = 1                         # scale = pods badhao, workers nahi
threads = 4                         # ek process mein 4 requests ek saath
accesslog = "-"                     # "-" = stdout, taaki kubectl logs mein dikhe
```

**Logs stdout pe kyun?** Containers mein logs file mein nahi likhte. Stdout pe likho, aur Kubernetes/Docker unhe collect karta hai. `kubectl logs` yahi dikhata hai.

**Ek worker kyun?** (1) Kubernetes mein scaling pods se hoti hai. (2) `prometheus_client` ke counters ek process mein rehte hain. Kai workers hote to har scrape alag worker ka data deta aur graph galat aata.

## Dockerfile

```dockerfile
FROM python:3.12-slim
```
Official Python image, "slim" variant (Debian, bina extra tools). Size chhota hai, aur attack surface bhi kam.

```dockerfile
ARG APP_VERSION=dev
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 APP_VERSION=${APP_VERSION}
```
- `ARG` sirf **build ke time** ka variable hai. `deploy.sh` isme `--build-arg APP_VERSION=1.0.0` bhejta hai.
- `ENV` container ke **run time** ka environment variable hai. ARG ki value ENV mein daal di, taaki app padh sake.
- `PYTHONDONTWRITEBYTECODE=1`: `.pyc` files mat banao (container mein bekaar hain).
- `PYTHONUNBUFFERED=1`: print turant dikhe, buffer mein na ruke. Iske bina `kubectl logs` mein logs der se aate.

```dockerfile
WORKDIR /app
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ .
```
- `WORKDIR`: aage ke saare commands `/app` folder mein chalenge.
- **Pehle requirements, phir code.** Yeh **layer caching** ki trick hai (Part 3).
- `--no-cache-dir`: pip ka download cache image mein na rahe, jisse image chhoti rehti hai.

```dockerfile
RUN useradd --uid 10001 --no-create-home appuser
USER 10001
```
Root ki jagah normal user. Agar app mein security hole ho, to attacker ko root nahi milega. Kubernetes mein `runAsNonRoot: true` isko enforce karta hai: root se chalne ki koshish ki to pod start hi nahi hoga.

```dockerfile
EXPOSE 5000
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
```
- `EXPOSE` sirf **documentation** hai, koi port nahi kholta.
- `CMD` container start hone pe yahi chalega. `app:app` ka matlab hai `app.py` file ka `app` object.
- **JSON format `["..."]` kyun?** Isse gunicorn seedha PID 1 banta hai aur Kubernetes ke SIGTERM ko sahi se receive karta hai (graceful shutdown).

## .dockerignore

Build ke time Docker poora folder (**build context**) leta hai. `.dockerignore` batata hai kya **mat** bhejo: `.git`, `.venv`, tests, docs. Isse build tez hota hai, image chhoti banti hai, aur secrets galti se image mein nahi jaate.

## .gitignore aur .gitattributes

- `.gitignore`: `.venv/`, `__pycache__/` aur cache Git mein na jaayein.
- `.gitattributes`: `* text=auto eol=lf`. Windows pe bhi files LF line endings ke saath save hon, taaki shell scripts Linux mein chalein.

## k8s/configmap.yaml

```yaml
kind: ConfigMap
metadata:
  name: flask-app-config
data:
  APP_ENV: minikube
```

Deployment mein `envFrom: configMapRef: flask-app-config` likha hai. Iska matlab hai ConfigMap ki **har key** container mein environment variable ban jaati hai.

## k8s/deployment.yaml (sabse important file)

```yaml
spec:
  replicas: 3
  selector:
    matchLabels:
      app: flask-app
```
"3 pods chahiye, aur mere pods woh hain jinpe `app: flask-app` label hai."

```yaml
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 1
```
Update ke time kabhi bhi 3 se kam ready pods nahi, aur max 1 extra pod. Isse **zero downtime** milta hai.

```yaml
  template:
    metadata:
      labels:
        app: flask-app              # selector se match hona ZAROORI
      annotations:
        prometheus.io/scrape: "true"
```
**Template** = har pod ka blueprint. Label selector se match karna chahiye, warna Kubernetes error dega. Annotation Prometheus ko batata hai "mujhe scrape karo".

**Label vs annotation:** label pe selection hota hai (selectors). Annotation sirf extra jaankari hai, tools ke liye.

```yaml
      securityContext:
        runAsNonRoot: true
```
Container root se chalne ki koshish kare to Kubernetes rok dega.

```yaml
      containers:
        - name: flask-app
          image: flask-app:1.0.0
          imagePullPolicy: IfNotPresent
```
`IfNotPresent` ka matlab hai image pehle se node pe hai to download mat karo. Hamari image Docker Hub pe hai hi nahi, isliye yeh zaroori hai. (`Always` hota to har baar download ki koshish karta aur fail hota.)

```yaml
          ports:
            - name: http
              containerPort: 5000
```
Port ko **naam** diya: `http`. Aage sab jagah naam use hota hai, number nahi (DRY).

```yaml
          envFrom:
            - configMapRef:
                name: flask-app-config
```
ConfigMap ki saari keys environment variables ban jaati hain.

```yaml
          resources:
            requests: {cpu: 100m, memory: 64Mi}
            limits:   {cpu: 250m, memory: 128Mi}
```
Flask idle mein ~30-40Mi memory leta hai, isliye 64Mi request aur 128Mi limit mein safe margin hai.

```yaml
          readinessProbe:
            httpGet: &health-check
              path: /health
              port: http
            initialDelaySeconds: 3
            periodSeconds: 5
            failureThreshold: 3
          livenessProbe:
            httpGet: *health-check
            initialDelaySeconds: 10
            periodSeconds: 10
            failureThreshold: 3
```
- `&health-check` ek **YAML anchor** hai: "is block ko yeh naam do".
- `*health-check` ek **alias** hai: "wahi block yahan paste karo". Yeh DRY hai, YAML ka feature.
- **Readiness:** 3 sec baad shuru, har 5 sec, 3 fail, yaani ~15 sec mein traffic se hatega.
- **Liveness:** 10 sec baad shuru, har 10 sec, 3 fail, yaani ~30 sec mein restart.
- **Liveness slow kyun?** Restart bada action hai. Thodi der ki problem pe restart nahi chahiye.

## k8s/service.yaml

```yaml
spec:
  type: NodePort
  selector:
    app: flask-app
  ports:
    - name: http
      port: 80
      targetPort: http
      nodePort: 30080
```

`app: flask-app` label wale **ready** pods ko traffic bhejo. Cluster ke andar port 80, container pe `http` (5000), aur node pe 30080.

## monitoring/00-namespace.yaml

`monitoring` namespace banata hai. **`00-` kyun?** `kubectl apply -f monitoring/` files ko **alphabetical order** mein lagata hai, aur namespace pehle banna chahiye, warna Prometheus wali file fail hogi.

## monitoring/10-prometheus.yaml

Ek file mein 6 objects hain, `---` se alag:

**1. ServiceAccount `prometheus`:** Prometheus pod ki identity.

**2. ClusterRole `prometheus`:**
```yaml
rules:
  - apiGroups: [""]
    resources: [nodes, nodes/proxy, nodes/metrics, services, endpoints, pods]
    verbs: [get, list, watch]
```
Sirf **padhne** ki permission. `nodes/proxy` cAdvisor tak pahunchne ke liye zaroori hai.

**3. ClusterRoleBinding:** ServiceAccount ko ClusterRole se jodta hai.

**4. ConfigMap `prometheus-config`**, jisme `prometheus.yml` hai, yaani **kya scrape karna hai**:

```yaml
global:
  scrape_interval: 15s
```
Har 15 second mein sab targets se data lo.

**Job 1: `prometheus`.** Khud ko scrape karo (`localhost:9090`). Isse test hota hai ki scraping chal rahi hai.

**Job 2: `kubernetes-cadvisor`.** Containers ka CPU/memory:
```yaml
scheme: https
tls_config:
  ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
authorization:
  credentials_file: /var/run/secrets/kubernetes.io/serviceaccount/token
kubernetes_sd_configs:
  - role: node
relabel_configs:
  - target_label: __address__
    replacement: kubernetes.default.svc:443
  - source_labels: [__meta_kubernetes_node_name]
    target_label: __metrics_path__
    replacement: /api/v1/nodes/$1/proxy/metrics/cadvisor
```
| Line | Matlab |
|---|---|
| `ca_file`, `credentials_file` | Kubernetes har pod mein ServiceAccount ka token aur certificate is path pe daal deta hai. Prometheus inse API server ko apni pehchaan batata hai |
| `role: node` | API se saare nodes ki list lo |
| `__address__` = `kubernetes.default.svc:443` | Seedha node pe nahi, **API server** pe jao |
| `__metrics_path__` | API server ka proxy path, jo node ke cAdvisor tak le jaata hai. `$1` = node ka naam |

**API server proxy kyun?** Isse kubelet ke certificates ki jhanjhat nahi hoti, aur yeh har cluster pe same chalta hai.

**Job 3: `app-pods`.** Hamare app ke `/metrics`:
```yaml
kubernetes_sd_configs:
  - role: pod
relabel_configs:
  - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
    action: keep
    regex: "true"
  - source_labels: [__meta_kubernetes_pod_container_port_name]
    action: keep
    regex: http
  - source_labels: [__meta_kubernetes_namespace]
    target_label: namespace
  - source_labels: [__meta_kubernetes_pod_name]
    target_label: pod
```
| Rule | Matlab |
|---|---|
| `role: pod` | Cluster ke saare pods lo (har pod ka har port ek candidate target) |
| `keep` annotation `"true"` | Sirf woh pods jinpe `prometheus.io/scrape: "true"` hai |
| `keep` port name `http` | Sirf `http` naam wala port. Port number yahan dobara nahi likha (DRY) |
| `namespace`, `pod` labels | Discovery ki info ko normal labels banao, taaki graph mein pod ka naam dikhe |

`__meta_...` labels discovery se aate hain aur scrape ke baad gayab ho jaate hain. Isliye kaam ke labels ko copy kar lete hain.

**5. Deployment `prometheus`:**
- `serviceAccountName: prometheus`: upar wali identity use karo
- `image: prom/prometheus:v2.53.0`: fixed version
- `args`: config file kahan hai, data kahan store karna hai, 2 din ka data rakho
- Probes: `/-/ready` aur `/-/healthy` (Prometheus ke built-in endpoints)
- Volumes: config ConfigMap se `/etc/prometheus` pe, aur data `emptyDir` mein

**6. Service `prometheus`:** NodePort 30090. Grafana `http://prometheus:9090` se isi ko call karta hai.

## monitoring/20-grafana.yaml

**ConfigMap `grafana-provisioning`** mein do files hain:

`datasources.yaml`:
```yaml
datasources:
  - name: Prometheus
    uid: prometheus
    type: prometheus
    url: http://prometheus:9090
    isDefault: true
```
Grafana start hote hi Prometheus data source ban jaata hai. URL mein **Service ka naam** hai, IP nahi (Kubernetes DNS). `uid` fixed rakha hai taaki dashboard JSON ise refer kar sake.

`dashboards.yaml`: "`/var/lib/grafana/dashboards` folder mein jo JSON files hain, unhe dashboards bana do."

**Deployment `grafana`:**
- `grafana/grafana:11.1.0`
- `subPath` mounts: ConfigMap ki ek-ek file ko sahi folder mein rakhta hai (datasources alag folder mein, dashboards provider alag mein)
- `grafana-dashboards` ConfigMap ko dashboards folder pe mount kiya. Yeh ConfigMap `deploy.sh` JSON file se banata hai

**Service `grafana`:** NodePort 30030.

## monitoring/dashboards/flask-app.json

8 panels hain:

| Panel | Type | Query ka matlab |
|---|---|---|
| Healthy pods being scraped | Stat | `sum(up{job="app-pods"})`: kitne pods ka `/metrics` mil raha hai. 3 = green, 2 = orange, 0-1 = red |
| Total requests / second | Stat | Saare pods ka total request rate |
| Total CPU used | Stat | Teeno pods ka total CPU (cores) |
| Total memory used | Stat | Teeno pods ki total memory |
| CPU usage per pod | Graph | Har pod ki alag line |
| Memory usage per pod | Graph | Har pod ki alag line |
| Requests per second by pod | Graph | Load balancing dikhta hai |
| 95th percentile response time | Graph | Har endpoint ki p95 latency |

`"refresh": "10s"` ka matlab hai har 10 sec mein update. `"time": now-30m` ka matlab hai pichle 30 minute dikhao.

## scripts/deploy.sh

```bash
set -euo pipefail
```
**Safety line.** `-e` = koi command fail ho to ruk jao. `-u` = undefined variable error hai. `-o pipefail` = pipe mein koi bhi command fail ho to fail maano. Iske bina script galti ke baad bhi chalti rehti.

```bash
IMAGE=$(awk '$1 == "image:" {print $2; exit}' k8s/deployment.yaml)
VERSION=${IMAGE##*:}
```
**DRY ka example.** Image ka naam deployment.yaml se **padha**, dobara likha nahi. `${IMAGE##*:}` ka matlab hai `:` ke baad wala hissa, yaani `1.0.0`.

```bash
minikube status >/dev/null 2>&1 || minikube start --driver=docker --cpus=2 --memory=4096
```
`||` = pehli command fail ho tabhi doosri chalao. Yaani Minikube chal raha hai to dobara start mat karo. `>/dev/null 2>&1` = output chhupao.

```bash
docker build --build-arg APP_VERSION="$VERSION" -t "$IMAGE" .
minikube image load "$IMAGE"
kubectl apply -f k8s/
kubectl apply -f monitoring/
kubectl create configmap grafana-dashboards -n monitoring \
  --from-file=monitoring/dashboards/ --dry-run=client -o yaml | kubectl apply -f -
```
Last command ki trick: `create --dry-run=client -o yaml` **YAML banata hai par lagata nahi**, aur `| kubectl apply -f -` usse lagata hai. Seedha `create` doosri baar "already exists" error deta, `apply` update kar deta hai. Isse script **idempotent** banti hai: kitni baar bhi chalao, result same.

```bash
kubectl rollout status deployment/flask-app --timeout=120s
```
Tab tak ruko jab tak saare pods ready na ho jaayein.

## scripts/load.sh

```bash
kubectl run load-generator --rm -it --restart=Never --image=busybox:1.36 -- /bin/sh -c "..."
```
- Cluster ke **andar** ek temporary busybox pod (chhota Linux toolbox)
- `--rm` = khatam hone pe pod delete. `--restart=Never` = Deployment nahi, sirf ek pod
- Andar `wget` loop `http://flask-app-service/work?ms=50` ko call karta hai, **Service ke naam se** (DNS)
- Parallel clients: `for i in $(seq N); do ... & done; wait`. `&` = background mein chalao
- `winpty`: Git Bash pe interactive commands ke liye zaroori

**Andar se load kyun?** Bahar se tunnel ke through bhejte to tunnel bottleneck banta, aur load balancing bhi saaf nahi dikhta.

## scripts/teardown.sh

`kubectl delete -f k8s/` aur `kubectl delete -f monitoring/` chalata hai. `--ignore-not-found` lagaya hai taaki pehle se delete ho to error na aaye. Namespace delete karne se uske andar sab kuch (grafana-dashboards bhi) delete ho jaata hai.

## scripts/build_pdf.py

Yeh PDF isi script se bani hai. Markdown files (`docs/`) padhta hai, unhe PDF format mein badalta hai, aur end mein asli source files jodta hai. **PDF ka apna koi content nahi hai**, isliye docs badlo aur script chalao to PDF update ho jaati hai (DRY).

```bash
python scripts/build_pdf.py            # dono PDF (English + Hinglish)
python scripts/build_pdf.py hinglish   # sirf yeh wali
```

## tests/

**`test_app.py`** (5 tests):

| Test | Kya check karta hai |
|---|---|
| homepage | `/` 200 deta hai aur app ka naam dikhata hai |
| health ok | `/health` 200 + `"status": "ok"` |
| fail -> 503 | `/fail` ke baad `/health` 503 |
| metrics | Request ke baad counter `/metrics` mein dikhta hai |
| work capped | `?ms=999999` pe bhi max 1000ms |

**`test_manifests.py`** (5 tests, **bina cluster ke**):

| Test | Kya pakadta hai |
|---|---|
| Selector = labels | Deployment apne pods pehchan payega ya nahi |
| Service sahi pods + port | Service ka selector kisi Deployment se match karta hai, aur `targetPort` ka naam container mein hai |
| Probes same | Readiness aur liveness same health check use karte hain, resources set hain |
| Prometheus config valid | `prometheus.yml` sahi YAML hai aur `app-pods` job hai |
| Dashboard datasource | Dashboard ka uid provisioning ke uid se match karta hai |

**`pytest.ini`:** `pythonpath = app` taaki tests `import app` kar sakein.
**`requirements-dev.txt`:** testing aur PDF ke tools. Runtime libraries `-r app/requirements.txt` se aati hain, dobara nahi likhi (DRY).

**Aise tests kyun?** Galti cluster pe deploy karke pakadne mein 5 minute lagte hain, test se 2 second. Yeh **"shift left"** hai: galti jitni jaldi pakdo, utna sasta.
