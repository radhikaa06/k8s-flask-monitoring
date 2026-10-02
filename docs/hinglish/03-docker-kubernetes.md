# Part 3 - Docker aur Kubernetes Basics

## Docker basics

### Problem kya thi?

Aapne laptop pe app banaya, jisme Python 3.12 aur Flask 3.1 tha. Server pe Python 3.8 hai aur Flask hai hi nahi, to app nahi chala. Yahi hai **"It works on my machine"** problem.

**Docker ka solution:** app ke saath uska **poora environment** (OS files, Python, libraries, code) ek package mein band kar do. Yeh package har jagah same chalega.

### Virtual Machine vs Container

| | Virtual Machine (VM) | Container |
|---|---|---|
| Kya hai | Poora alag computer (apna OS kernel) | Ek isolated process (host ka kernel share karta hai) |
| Size | GBs | MBs |
| Start time | Minutes | Seconds |
| Isolation | Bahut strong | Achha (namespaces + cgroups) |
| Example | VirtualBox, Hyper-V | Docker |

### Image vs Container

| Image | Container |
|---|---|
| Blueprint / recipe / class | Running cheez / dish / object |
| Read-only | Running process |
| `docker build` se banti hai | `docker run` se chalta hai |
| Ek image | Uske kai containers ban sakte hain |

**Analogy:** Image = cake ki recipe, container = bana hua cake. Ek recipe se 10 cake ban sakte hain.

### Layers

Dockerfile ki har instruction ek **layer** banati hai. Layers ek ke upar ek rakhi jaati hain.

**Caching:** Agar kisi layer ke inputs nahi badle, to Docker purani layer reuse karta hai. Isliye hum `requirements.txt` pehle copy karte hain aur code baad mein. Code badalne pe `pip install` wali layer cache se aa jaati hai, aur build seconds mein ho jaata hai.

### Registry

Images store karne ki jagah, jaise GitHub code ke liye hota hai. Example: **Docker Hub** (`python:3.12-slim` wahan se aata hai), GitHub Container Registry, AWS ECR.

Is project mein hum image **registry pe push nahi karte**. Seedha Minikube mein load karte hain (`minikube image load`), jo local learning ke liye simple hai.

### Image naam ka format

```
flask-app:1.0.0
   |        |
  naam     tag (version)
```

Tag na do to `latest` maan liya jaata hai. **`latest` avoid karo**, kyunki pata nahi chalta kaun sa version chal raha hai. Humne `1.0.0` rakha.

### Zaroori Docker commands

| Command | Kya karti hai |
|---|---|
| `docker build -t naam:tag .` | Current folder ke Dockerfile se image banao |
| `docker images` | Saari images dikhao |
| `docker run -d -p 5000:5000 --name x image` | Container chalao (background, port map) |
| `docker ps` | Chal rahe containers |
| `docker logs x` | Container ke logs |
| `docker exec -it x sh` | Container ke andar shell kholo |
| `docker rm -f x` | Container band karke hatao |

**Port mapping `-p 5000:5000`:** `laptop_port:container_port`. Container ka apna network hai, aur bina mapping ke laptop se andar nahi pahunch sakte.

### Docker Desktop aur WSL2

Windows pe Docker Desktop ek chhota Linux environment (WSL2) chalata hai aur containers wahan chalte hain. Isliye Windows pe pehle **WSL2** chahiye.

## Kubernetes basics

### Kubernetes kyun?

Ek container chalana easy hai: `docker run`. Lekin production mein sawaal aate hain:

- Container crash ho gaya to **restart** kaun karega?
- Traffic badh gaya to 10 copies kaise chalayein, aur unme **traffic kaise baantein**?
- Naya version **bina downtime** kaise daalein? Kharab nikla to **wapas** kaise jaayein?
- 50 servers hain to container **kis server pe** chalega?

Kubernetes (K8s) yeh sab **automatic** karta hai. Isko **container orchestrator** kehte hain, jaise orchestra ka conductor saare musicians ko sambhalta hai.

### Declarative vs Imperative

| Imperative ("kaise karo") | Declarative ("kya chahiye") |
|---|---|
| "Container 1 chalao, phir 2, phir 3" | "Mujhe 3 containers chahiye" |
| Aap har step batate ho | Aap final state batate ho, K8s khud karta hai |
| `docker run` x 3 | `replicas: 3` in YAML |

Kubernetes **declarative** hai. Aap YAML mein **desired state** likhte ho, aur Kubernetes lagatar **actual state** ko desired state jaisa banata rehta hai. Isko **reconciliation loop** kehte hain, aur yahi Kubernetes ka dil hai.

### Cluster architecture

**Cluster** = machines (nodes) ka group jo milkar Kubernetes chalate hain.

**Control plane (dimaag):**

| Component | Kaam |
|---|---|
| **API server** | Sab ka entry gate. `kubectl` isi se baat karta hai |
| **etcd** | Database jahan cluster ki saari state store hoti hai |
| **Scheduler** | Naya pod kis node pe chalega, yeh decide karta hai |
| **Controller manager** | Reconciliation loops chalata hai (ReplicaSet controller etc.) |

**Worker node (haath-pair):**

| Component | Kaam |
|---|---|
| **kubelet** | Node pe pods chalata hai, probes check karta hai, container restart karta hai |
| **Container runtime** | Asli mein containers chalata hai (containerd / Docker) |
| **kube-proxy** | Service ka networking (traffic sahi pod tak pahunchana) |
| **cAdvisor** | kubelet ke andar. Har container ka CPU/memory naapta hai, aur Prometheus yahin se data leta hai |

**Minikube** mein yeh sab ek hi node pe hai: control plane bhi wahi, worker bhi wahi.

### kubectl

Kubernetes se baat karne ka command-line tool:

```bash
kubectl get pods                  # list
kubectl describe pod <naam>       # detail + events
kubectl logs <naam>               # logs
kubectl apply -f file.yaml        # YAML lagao (create ya update)
kubectl delete -f file.yaml       # YAML wali cheezein hatao
```

`kubectl` ko kaise pata ki kis cluster se baat karni hai? `~/.kube/config` file se, jise **kubeconfig** kehte hain. `minikube start` yeh apne aap set kar deta hai.

### YAML ka structure

Har Kubernetes object ke 4 hisse hote hain:

```yaml
apiVersion: apps/v1        # kaun sa API group/version
kind: Deployment           # kya cheez hai
metadata:                  # naam, labels, namespace
  name: flask-app
spec:                      # DESIRED STATE - kya chahiye
  replicas: 3
```

**YAML rules:** indentation **spaces** se hoti hai (tab nahi), `key: value` likhte hain, list ke liye `- item`. Ek file mein kai objects `---` se alag hote hain.

### Labels aur selectors

**Label** = object pe chipka hua tag, jaise `app: flask-app`.
**Selector** = "jin objects pe yeh label hai, woh sab".

Kubernetes mein cheezein **naam se nahi, labels se** judti hain:

- Deployment apne pods ko label se pehchanta hai
- Service apne pods ko label se dhoondhta hai
- Hamari Prometheus config bhi pods ko annotation/label se dhoondhti hai

**Sabse common galti:** selector aur label match nahi kar rahe. Tab Service ke peeche koi pod nahi hota. Hamare `test_manifests.py` tests yahi check karte hain.

### Namespace

Cluster ke andar alag-alag "kamre". Same naam ki cheez alag namespaces mein ho sakti hai. Humne app ko `default` mein rakha aur monitoring ko `monitoring` namespace mein.

### Pod

- Kubernetes ki **sabse chhoti unit**
- Ek ya zyada containers, jo **ek IP** share karte hain
- **Temporary hai.** Pod mara to wahi pod wapas nahi aata, **naya pod** (naye naam aur naye IP ke saath) banta hai
- Hum seedha pod nahi banate, Deployment banata hai

### ReplicaSet

"Is label wale exactly N pods hone chahiye." Kam hue to banao, zyada hue to hatao. Deployment isko khud banata hai, aap seedha use nahi karte.

### Deployment

ReplicaSet ke upar ek manager:

- Replicas maintain karta hai (ReplicaSet ke through)
- **Rolling update:** naya version dheere-dheere laata hai, purana dheere-dheere hatata hai
- **Rollback:** `kubectl rollout undo` se pichla version wapas laata hai
- History rakhta hai (revisions)

**Rolling update ke andar kya hota hai?** Image badalne pe Deployment ek **naya ReplicaSet** banata hai. Naya wala 0 se 3 tak jaata hai aur purana 3 se 0 tak, ek-ek karke. Hamari settings:

- `maxSurge: 1`: update ke time max 1 extra pod (yaani 4 tak)
- `maxUnavailable: 0`: kabhi bhi 3 se kam **ready** pods nahi

Isliye agar naya version kharab nikle, to purane pods chalte rehte hain. Site down nahi hoti.

### Service

**Problem:** pods aate-jaate rehte hain aur unke IP badalte rehte hain. Client kis IP pe jaaye?

**Solution:** Service. Ek **fixed IP + DNS naam**, jo label se pods dhoondhta hai aur **sirf ready pods** ko traffic bhejta hai (load balancing).

| Service type | Kahan se access | Kab use karein |
|---|---|---|
| **ClusterIP** (default) | Sirf cluster ke andar se | Internal services (database etc.) |
| **NodePort** | Node ke IP + port 30000-32767 se | Local testing, Minikube |
| **LoadBalancer** | Cloud ka load balancer, public IP | Cloud (AWS, GCP, Azure) |

Humne **NodePort** liya, kyunki Minikube pe bahar se access karne ka yeh sabse simple tareeka hai.

**Endpoints:** Service ke peeche abhi kaun-kaun se pod IPs hain. `kubectl get endpoints flask-app-service` chalao. Khaali (`<none>`) aaye to selector galat hai ya koi pod ready nahi hai.

**Service ke 3 ports:**

```yaml
port: 80          # cluster ke andar: http://flask-app-service:80
targetPort: http  # container ka port (naam "http" = 5000)
nodePort: 30080   # node pe bahar se
```

### ConfigMap aur Secret

| ConfigMap | Secret |
|---|---|
| Normal settings (`APP_ENV=minikube`) | Sensitive cheezein (password, API key) |
| Plain text | Base64 encoded (encryption nahi, sirf encoding!) |

**Fayda:** image ek hi rehti hai, settings environment ke hisaab se badalti hain. Dev, test aur prod sab mein same image chalti hai.

### Probes (health checks)

kubelet pod ko baar-baar check karta hai:

| | Readiness probe | Liveness probe | Startup probe |
|---|---|---|---|
| Sawaal | Traffic le sakta hai? | Zinda hai ya atak gaya? | Start ho gaya? |
| Fail hone pe | Service se **hata do** | Container **restart** | Baaki probes rok ke rakho |
| Humne use kiya? | Haan | Haan | Nahi (Flask 1 sec mein start hota hai) |

**Probe ke types:** `httpGet` (URL check, jo humne use kiya), `tcpSocket` (port khula hai ya nahi), `exec` (container ke andar command chalao).

**Probe settings:**

| Setting | Matlab |
|---|---|
| `initialDelaySeconds` | Container start hone ke kitni der baad pehla check |
| `periodSeconds` | Kitni-kitni der mein check |
| `failureThreshold` | Kitni baar lagatar fail hone pe action |
| `timeoutSeconds` | Kitni der mein jawab na aaye to fail (default 1s) |

### Resources: requests aur limits

```yaml
resources:
  requests: {cpu: 100m, memory: 64Mi}
  limits:   {cpu: 250m, memory: 128Mi}
```

- **CPU units:** `1` = 1 core, `100m` = 100 millicores = 0.1 core
- **Memory units:** `Mi` = mebibyte (1024 x 1024 bytes), `Gi` = gibibyte

| | Requests | Limits |
|---|---|---|
| Matlab | Minimum guarantee | Maximum hadd |
| Kaun dekhta hai | Scheduler (kis node pe jagah hai) | kubelet / kernel (cgroups) |
| CPU zyada | - | **Throttling** (slow ho jaata hai, marta nahi) |
| Memory zyada | - | **OOMKilled** (exit code 137) |

**CPU aur memory mein farq kyun?** CPU "compressible" hai, use thoda kam do to process slow chalega. Memory "incompressible" hai, jo le li woh wapas nahi le sakte, to process ko maarna padta hai.

**QoS classes** (memory kam pade to kaun pehle maara jaayega):

| Class | Kab | Priority |
|---|---|---|
| Guaranteed | requests = limits (har container mein) | Sabse safe |
| **Burstable** | requests < limits | Beech mein (hamare pods yahi hain) |
| BestEffort | Koi requests/limits nahi | Sabse pehle maara jaayega |

### RBAC (Role-Based Access Control)

Kaun kya kar sakta hai? Kubernetes mein 4 cheezein hoti hain:

| Object | Kaam |
|---|---|
| **ServiceAccount** | Pod ki identity ("main Prometheus hoon") |
| **Role / ClusterRole** | Permissions ki list ("pods dekh sakte ho") |
| **RoleBinding / ClusterRoleBinding** | Identity ko permission dena |

Role ek namespace ke liye hota hai aur ClusterRole poore cluster ke liye. Prometheus ko poore cluster ke pods aur nodes dekhne hain, isliye **ClusterRole**. Sirf `get, list, watch` diye gaye hain (read-only). Isko **least privilege** kehte hain: jitna zaroori hai, bas utna.

## Minikube

Laptop pe chhota, asli Kubernetes cluster.

| Concept | Matlab |
|---|---|
| **Driver** | Minikube node kahan chalega: `docker` (container), virtualbox (VM), hyperv. Humne `docker` liya |
| **Image store** | Minikube ka apna image store hai, laptop ke Docker se alag. Isliye `minikube image load` karna padta hai |
| **`minikube service`** | Docker driver pe Windows/Mac mein node ka IP seedha nahi khulta, to yeh ek **tunnel** banata hai. Terminal khula rakhna padta hai |
| **Addons** | Extra features ek command se: `metrics-server`, `dashboard`, `ingress` |

**Minikube vs alternatives:** kind (Kubernetes in Docker), k3s (halka Kubernetes), Docker Desktop ka built-in Kubernetes. Sab learning ke liye theek hain. Minikube sabse popular aur beginner-friendly hai.

**Minikube vs production (EKS/GKE/AKS):** production mein kai nodes hote hain, cloud load balancer hota hai, storage cloud ka hota hai, aur control plane cloud provider sambhalta hai. Lekin YAML aur concepts **wahi** rehte hain. Isliye Minikube pe seekha hua seedha kaam aata hai.
