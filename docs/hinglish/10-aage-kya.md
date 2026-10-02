# Part 10 - Aage Kya Seekhein, Glossary aur Cheat Sheet

## Is project ko aage kaise badhayein (ek-ek karke)

Har step pichle pe bana hai. Ek baar mein ek hi karo, aur har ek ko GitHub pe alag commit mein daalo.

| # | Kya add karein | Kya seekhoge | Mushkil |
|---|---|---|---|
| 1 | **GitHub Actions CI**: har push pe tests + `docker build` | CI/CD, YAML pipelines | Aasaan |
| 2 | Image ko **GitHub Container Registry** pe push | Registries, image tags, auth | Aasaan |
| 3 | **HorizontalPodAutoscaler (HPA)**: CPU zyada to pods apne aap badhein | Autoscaling, metrics-server | Aasaan |
| 4 | **Ingress**: NodePort ki jagah ek proper URL (`flask.local`) | Ingress controller, routing | Medium |
| 5 | **Alertmanager**: "pod down" ya "CPU 80%+" pe alert | Alerting rules, notifications | Medium |
| 6 | **kube-state-metrics**: pod restarts, replicas ka data | Kubernetes object metrics | Medium |
| 7 | **Kustomize** ya **Helm**: dev/prod ke liye alag config | Packaging, templating | Medium |
| 8 | **PersistentVolume** for Prometheus/Grafana | Storage, PVC | Medium |
| 9 | **Loki**: logs bhi Grafana mein | Log aggregation | Medium |
| 10 | Cloud pe (AWS EKS / Azure AKS free tier) + **Terraform** | Cloud, Infrastructure as Code | Mushkil |

## DevOps roadmap (internship ke liye)

1. **Linux:** permissions, processes, systemd, networking commands (`ss`, `ip`, `dig`), shell scripting
2. **Networking:** TCP/IP, DNS, HTTP/HTTPS, load balancers, firewalls
3. **Git:** branching, merge vs rebase, pull requests, conflicts
4. **Docker:** multi-stage builds, Docker Compose, image security scanning
5. **CI/CD:** GitHub Actions ya Jenkins
6. **Kubernetes:** yeh project, phir StatefulSet, DaemonSet, Jobs, Ingress, HPA, RBAC
7. **Monitoring:** Prometheus, Grafana, alerting, logs (Loki/ELK)
8. **Cloud:** ek cloud achhe se (AWS sabse common): EC2, VPC, IAM, S3, EKS
9. **IaC:** Terraform, Ansible
10. **Certification (optional):** CKA / CKAD (Kubernetes), AWS Cloud Practitioner

## Glossary (A to Z)

| Term | Matlab |
|---|---|
| Addon (Minikube) | Ek command se on hone wala extra feature (metrics-server) |
| Annotation | Object pe extra jaankari, tools ke liye (selection nahi hota) |
| API server | Kubernetes ka entry gate. kubectl isi se baat karta hai |
| Build context | `docker build` ko bheja gaya folder |
| cAdvisor | kubelet ke andar, containers ka CPU/memory naapta hai |
| Cardinality | Ek metric ki kitni unique time series hain |
| cgroups | Linux feature jo process ke resources limit karta hai |
| ClusterIP | Default Service type, sirf cluster ke andar |
| ClusterRole | Poore cluster ke liye permissions ki list |
| ConfigMap | Non-secret config, environment variables ya files ke roop mein |
| Container | Isolated process (namespaces + cgroups) |
| Counter | Sirf badhne wala metric |
| CrashLoopBackOff | Container baar-baar crash, restarts ke beech badhti der |
| DaemonSet | Har node pe ek pod (is project mein nahi) |
| Declarative | "Kya chahiye" likho, "kaise" system khud karega |
| Deployment | ReplicaSet ka manager: replicas, rolling update, rollback |
| DNS | Naam ko IP mein badalna |
| DRY | Don't Repeat Yourself: har jaankari ek jagah |
| emptyDir | Pod ke saath bana aur mita temporary volume |
| Endpoints | Service ke peeche abhi ke ready pod IPs |
| etcd | Kubernetes ka database |
| Exit code 137 | SIGKILL (128+9), aksar OOMKilled |
| Gauge | Upar-neeche hone wala metric |
| Grafana | Visualization tool, dashboards |
| Gunicorn | Python ka production web server |
| Helm | Kubernetes ka package manager (is project mein nahi) |
| Histogram | Values ko buckets mein ginne wala metric (percentiles) |
| HPA | Horizontal Pod Autoscaler: load pe pods badhana/ghatana |
| Idempotent | Kitni baar bhi chalao, result same |
| Image | Container ka read-only blueprint |
| imagePullPolicy | Image kab download karni hai (IfNotPresent/Always/Never) |
| Ingress | HTTP routing cluster ke andar (is project mein nahi) |
| kubectl | Kubernetes CLI |
| kubelet | Har node pe agent jo pods chalata aur probes check karta hai |
| Label | Key-value tag jisse selection hota hai |
| Layer | Image ka ek hissa, Dockerfile instruction se bana |
| Limit | Resource ka maximum |
| Liveness probe | Fail ho to container restart |
| Minikube | Laptop pe single-node Kubernetes |
| Namespace (Kubernetes) | Cluster ke andar logical kamra |
| Namespace (Linux) | Process isolation ka kernel feature |
| Node | Cluster ki ek machine |
| NodePort | Service jo har node pe port 30000-32767 kholti hai |
| OOMKilled | Memory limit cross, kernel ne maara |
| p95 | 95% requests isse tez thi |
| Pod | Kubernetes ki sabse chhoti unit, ek ya zyada containers |
| Port-forward | Laptop ka port seedha ek pod se jodna |
| Probe | kubelet ka health check |
| PromQL | Prometheus query language |
| Prometheus | Metrics collect aur store karne wala tool (pull model) |
| Provisioning (Grafana) | Data source/dashboard files se apne aap banana |
| QoS class | Guaranteed / Burstable / BestEffort |
| rate() | Counter ka per-second badhaav |
| RBAC | Role-based access control: kaun kya kar sakta hai |
| Readiness probe | Fail ho to Service se hatao |
| Reconciliation | Actual state ko desired state jaisa banana, lagatar |
| Registry | Images store karne ki jagah (Docker Hub) |
| Relabeling | Prometheus mein discovered targets ko filter/rename karna |
| ReplicaSet | N pods maintain karta hai |
| Request | Resource ki guaranteed minimum (scheduling ke liye) |
| Rolling update | Pods ko dheere-dheere naye version se badalna |
| Rollback | Pichle version pe wapas (`rollout undo`) |
| Scrape | Prometheus ka `/metrics` se data lena |
| Secret | Sensitive config (base64, encryption nahi) |
| Selector | Labels se objects chunna |
| Service | Pods ke aage stable IP/DNS + load balancing |
| ServiceAccount | Pod ki identity |
| Service discovery | Targets ko automatically dhoondhna |
| SIGTERM / SIGKILL | "Band ho jao" / "Turant maro" |
| Throttling | CPU limit pe process slow karna |
| Time series | Naam + labels ki values, time ke saath |
| venv | Python ka alag environment |
| WSL2 | Windows mein asli Linux kernel |
| YAML anchor/alias | `&naam` se define, `*naam` se reuse |

## Cheat sheet

### Docker

```bash
docker build -t flask-app:1.0.0 .                 # image banao
docker images                                     # images list
docker run -d -p 5000:5000 --name t flask-app:1.0.0
docker ps                                         # chal rahe containers
docker logs t                                     # logs
docker exec -it t sh                              # andar jao
docker rm -f t                                    # hatao
```

### Minikube

```bash
minikube start --driver=docker --cpus=2 --memory=4096
minikube status
minikube image load flask-app:1.0.0
minikube image ls
minikube service <service> [-n namespace] --url
minikube addons enable metrics-server
minikube dashboard
minikube stop
minikube delete
```

### kubectl: dekhna

```bash
kubectl get pods [-A] [-o wide] [-w] [-l app=flask-app]
kubectl get deployment,replicaset,service,endpoints
kubectl get all -n monitoring
kubectl describe pod <naam>
kubectl logs <naam> [--previous] [-f]
kubectl get events --sort-by=.lastTimestamp
kubectl top pods
kubectl get pods --show-labels
```

### kubectl: badalna

```bash
kubectl apply -f k8s/
kubectl delete -f k8s/
kubectl scale deployment flask-app --replicas=5
kubectl set image deployment/flask-app flask-app=flask-app:1.0.1
kubectl rollout status deployment/flask-app
kubectl rollout history deployment/flask-app
kubectl rollout undo deployment/flask-app
kubectl rollout restart deployment/flask-app
kubectl delete pod <naam>
kubectl exec -it <naam> -- sh
kubectl port-forward deployment/flask-app 8080:5000
```

### Project scripts

```bash
./scripts/deploy.sh          # sab kuch deploy
./scripts/load.sh [ms] [n]   # traffic do
./scripts/teardown.sh        # sab hatao
python -m pytest             # tests
python scripts/build_pdf.py  # PDFs dobara banao
```

### Git

```bash
git status
git add .
git commit -m "Message"
git push
git log --oneline
git pull --rebase
```

### PromQL

```
up
sum(up{job="app-pods"})
sum by (pod) (rate(flask_http_requests_total[1m]))
sum by (pod) (rate(container_cpu_usage_seconds_total{container="flask-app"}[1m]))
sum by (pod) (container_memory_working_set_bytes{container="flask-app"})
histogram_quantile(0.95, sum by (le) (rate(flask_http_request_duration_seconds_bucket[5m])))
```

## Aakhri baat

Yeh project **bada nahi**, lekin **gehra** hai. Interview mein 10 tools ke naam lene se zyada kaam aata hai ek project ko andar se samajhna: kya toota, kyun toota, kaise theek kiya.

**Abhi ke 3 kaam:**

1. WSL2 + Docker install karo, phir `./scripts/deploy.sh` (Part 7)
2. Part 8 ke 6 experiments **khud** karo, aur jo dikha woh note karo
3. Screenshots GitHub pe daalo

All the best!
