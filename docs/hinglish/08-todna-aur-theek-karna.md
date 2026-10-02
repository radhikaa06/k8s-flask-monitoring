# Part 8 - Todna aur Theek Karna: Experiments aur Troubleshooting

**Asli seekh yahin hai.** Project chalana aasaan hai. Interview mein farq is baat se padta hai ki aapne cheezein **todi** hain, **dekha** kya hota hai, aur **theek** kiya hai.

Har experiment ke time Grafana dashboard aur terminal **saath-saath** khula rakho.

## Test 1 - Self-healing: pod delete karo

**Terminal 1** (watch mode):
```bash
kubectl get pods -l app=flask-app -w
```
`-l app=flask-app` = sirf is label wale pods. `-w` = watch, yaani badlav live dikhao.

**Terminal 2:**
```bash
kubectl delete pod <koi-ek-flask-app-pod-ka-naam>
```

**Kya dikhega:**
```
flask-app-xxx-abcde   1/1   Terminating
flask-app-xxx-zzzzz   0/1   Pending
flask-app-xxx-zzzzz   0/1   ContainerCreating
flask-app-xxx-zzzzz   0/1   Running        <- container chal gaya, readiness abhi pass nahi
flask-app-xxx-zzzzz   1/1   Running        <- ready, ab traffic milega
```

**Kyun hua?** ReplicaSet controller ne dekha: chahiye 3, hain 2, to naya banao. Naye pod ka **naam alag** hai. Pods **disposable** hain ("cattle, not pets").

**Grafana mein:** "Healthy pods" thodi der ke liye 2 (orange), phir 3 (green).

**Aur aage:** `kubectl delete pods -l app=flask-app` se teeno ek saath delete karo, aur teeno wapas aa jaayenge.

## Test 2 - Liveness probe: app ko "beemar" karo

**Terminal 1:**
```bash
kubectl port-forward deployment/flask-app 8080:5000
```
`port-forward` laptop ke port 8080 ko **ek** pod ke 5000 se jodta hai. Service ko bypass karta hai, taaki pata ho kaunsa pod beemar kiya.

**Terminal 2:**
```bash
curl -X POST localhost:8080/fail
kubectl get pods -l app=flask-app -w
```

**Kya dikhega:**
- ~15 sec: woh pod `0/1` ho jaata hai. **Readiness fail** hua, to Service ne traffic bhejna band kiya. Restart nahi hua.
- ~30 sec: `RESTARTS` 0 se 1 hota hai. **Liveness fail** hua, to kubelet ne container restart kiya.
- Restart ke baad naya process healthy hai, to `1/1` wapas.

**Saboot dekho:**
```bash
kubectl describe pod <us-pod-ka-naam>
```
Neeche **Events** mein:
```
Warning  Unhealthy  Readiness probe failed: HTTP probe failed with statuscode: 503
Warning  Unhealthy  Liveness probe failed: HTTP probe failed with statuscode: 503
Normal   Killing    Container flask-app failed liveness probe, will be restarted
```

**Seekh:** Readiness **users ko bachata hai** (kharab pod pe traffic nahi jaata). Liveness pod ko **theek karta hai** (restart).

**Note:** port-forward restart ke baad toot sakta hai ("lost connection to pod"). Yeh normal hai, dobara chalao.

## Test 3 - Kharab release: galat image

```bash
kubectl set image deployment/flask-app flask-app=flask-app:9.9.9
kubectl get pods -l app=flask-app
kubectl rollout status deployment/flask-app --timeout=30s
```

`set image` = Deployment ki image badlo (container `flask-app` ki image `flask-app:9.9.9` karo). Yeh version exist nahi karta.

**Kya dikhega:**
```
flask-app-NEW-xxxxx   0/1   ErrImagePull       <- naya pod, image nahi mili
flask-app-OLD-aaaaa   1/1   Running            <- purane 3 abhi bhi chal rahe!
flask-app-OLD-bbbbb   1/1   Running
flask-app-OLD-ccccc   1/1   Running
```
`rollout status` timeout ho jaayega.

**Site down kyun nahi hui?** `maxUnavailable: 0`. Naya pod ready nahi hua, isliye Kubernetes ne purana ek bhi nahi hataya. **Rolling update ki safety yahi hai.**

**Theek karo:**
```bash
kubectl rollout undo deployment/flask-app
```
**Expected:** `deployment.apps/flask-app rolled back`. Kharab pod gayab.

**History dekho:** `kubectl rollout history deployment/flask-app`

## Test 4 - Memory limit: OOMKilled

```bash
kubectl set resources deployment flask-app --requests=memory=16Mi --limits=memory=16Mi
kubectl get pods -l app=flask-app -w
```

Request bhi 16Mi isliye kiya kyunki **request kabhi limit se zyada nahi ho sakti**. Sirf limit kam karte to Kubernetes reject kar deta.

**Kya dikhega:** naye pods `OOMKilled`, phir `CrashLoopBackOff`.

```bash
kubectl describe pod <naya-pod>
```
```
Last State:  Terminated
  Reason:    OOMKilled
  Exit Code: 137
```
**137 = 128 + 9 (SIGKILL).** Linux kernel ne memory limit cross hone pe process maar diya.

**CrashLoopBackOff kya hai?** Container baar-baar crash ho raha hai, isliye Kubernetes har baar restart se pehle zyada der rukta hai: 10s, 20s, 40s... max 5 minute.

Purane pods phir se chal rahe hain (Test 3 jaisa).

**Theek karo:** `kubectl rollout undo deployment/flask-app` ya `kubectl apply -f k8s/` (Git wala version wapas).

## Test 5 - CPU limit: throttling

```bash
./scripts/load.sh 500 6
```
6 parallel clients, aur har request 500ms CPU maangti hai. Itna CPU 3 pods x 0.25 core se nahi milega.

**Grafana mein kya dikhega:**
- "CPU usage per pod" ki har line **0.25 pe flat** ho jaayegi, upar nahi jaayegi
- "95th percentile response time" **badh** jaayega
- **Koi restart nahi**

**Seekh:** CPU limit cross karne pe process **slow** hota hai (throttle), **marta nahi**. Memory pe **marta hai**. Yeh farq interview mein zaroor poocha jaata hai.

## Test 6 - Load mein scale karo

`load.sh` chalte waqt:
```bash
kubectl scale deployment flask-app --replicas=5
```
**Grafana:** "Requests per second by pod" mein 2 nayi lines aayengi, aur har pod ka CPU kam hoga (load baant gaya).

Wapas: `kubectl scale deployment flask-app --replicas=3`.

**Dhyan do:** `kubectl scale` sirf live cluster badalta hai. YAML mein abhi bhi 3 hai. Agla `kubectl apply` 3 kar dega. **Git wali file = sach.** Is soch ko **GitOps** ki neev samjho.

## Troubleshooting ka tareeka (5 steps)

Koi bhi problem ho, **isi order** mein chalo:

| Step | Command | Kya pata chalega |
|---|---|---|
| 1. Get | `kubectl get pods -A` | Kaunsa pod pareshan hai? STATUS? RESTARTS? |
| 2. Describe | `kubectl describe pod <naam>` | **Events** (sabse neeche): image, scheduling, probes, OOM |
| 3. Logs | `kubectl logs <naam>` (crash ke baad `--previous`) | App ne khud kya error print kiya |
| 4. Events | `kubectl get events --sort-by=.lastTimestamp` | Cluster mein abhi kya-kya hua, time ke order mein |
| 5. Exec | `kubectl exec -it <naam> -- sh` | Container ke andar jaake dekho (files, env, network) |

**Network problem ho to 2 aur checks:**

| Check | Command | Sahi jawab |
|---|---|---|
| Service ke peeche pods hain? | `kubectl get endpoints flask-app-service` | 3 IPs |
| Labels match karte hain? | `kubectl get pods --show-labels` | `app=flask-app` |

**`--previous` kyun?** Crash ke baad naya container chal raha hota hai, aur `kubectl logs` naye ke logs dikhata hai. Crash ka error **purane** container mein tha.

## Error catalogue

| STATUS / Problem | Matlab | Kaise confirm karein | Solution |
|---|---|---|---|
| `ErrImagePull` / `ImagePullBackOff` | Image nahi mili | describe: `not found` / `pull access denied` | `minikube image load flask-app:1.0.0`, tag check karo |
| `CrashLoopBackOff` | Container start hote hi band | `kubectl logs <pod> --previous` | Logs ka error theek karo |
| `OOMKilled` (137) | Memory limit cross | describe: `Reason: OOMKilled` | Limit badhao ya memory leak dhoondho |
| `Pending` | Kisi node pe jagah nahi (requests ke hisaab se) | describe: `Insufficient cpu/memory` | Requests kam karo, ya Minikube ko zyada CPU/RAM do |
| `CreateContainerConfigError` | ConfigMap/Secret nahi mila | describe: `configmap not found` | `kubectl apply -f k8s/configmap.yaml` |
| `ContainerCreating` atka | Volume mount nahi ho raha | describe: `FailedMount` | Missing ConfigMap banao (jaise `grafana-dashboards`) |
| `Running` lekin `0/1` | Readiness fail | describe: `Readiness probe failed` | port-forward se `/health` check karo, probe ka path/port dekho |
| RESTARTS badh rahe | Liveness fail ya crash | describe: `failed liveness probe` | `/health` time pe jawab de; slow start ho to `initialDelaySeconds` badhao |
| Browser mein nahi khul raha | Tunnel band ya endpoints khaali | `kubectl get endpoints` | `minikube service` wala terminal khula rakho; selector theek karo |
| `connection refused` (kubectl) | Cluster band / galat context | `kubectl config current-context` | `minikube start` |
| Rollout atka | Naye pods ready nahi | `kubectl rollout status` | `kubectl rollout undo`, phir naye pod ki jaanch |
| Prometheus target DOWN | Pod ready nahi / port galat | Status > Targets ka error | Port ka naam `http` ho, `/metrics` chal raha ho |
| cAdvisor `403 Forbidden` | RBAC permission nahi | Status > Targets | ClusterRole mein `nodes/proxy`; `10-prometheus.yaml` dobara apply |
| Grafana `No data` | Query galat / time range / traffic nahi | Query Prometheus Graph mein chalao | `load.sh` chalao, time range "Last 15 minutes" |
| `namespaces "monitoring" not found` | Order galat | - | `kubectl apply -f monitoring/` dobara chalao |

## Kaam ki commands

```bash
kubectl get all -n monitoring                       # namespace ki saari cheezein
kubectl logs -l app=flask-app --tail=20 --prefix    # teeno pods ke last 20 logs
kubectl top pods -A                                 # abhi ka CPU/memory
kubectl get pod <naam> -o yaml                      # pod ki poori live config
kubectl explain deployment.spec.strategy            # kisi bhi field ki documentation
minikube dashboard                                  # Kubernetes ka web UI
```
