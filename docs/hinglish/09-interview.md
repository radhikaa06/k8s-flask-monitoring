# Part 9 - Interview Preparation

Interview **English** mein hoga, isliye har sawaal ke do hisse hain:

- **Samjho:** Hinglish mein concept
- **Bolo:** interview mein bolne layak English answer

Ratna mat. Samajh ke **apne shabdon** mein bolo. Upar wale experiments khud kiye honge to answers apne aap natural lagenge.

## 60-second project pitch

**Bolo:**

"I built a small Flask web application and focused on the DevOps around it. I containerised it with a slim, non-root Docker image and deployed it to a local Kubernetes cluster using Minikube. The Deployment runs three replicas with readiness and liveness probes and CPU and memory limits, and a NodePort Service load-balances traffic across them. For monitoring, I set up Prometheus and Grafana using plain YAML. Prometheus discovers pods through the Kubernetes API and scrapes container CPU and memory from cAdvisor, plus request metrics from the app's /metrics endpoint. Grafana shows them on a dashboard that is provisioned from code. Then I tested failures: I deleted pods, made the health check fail, deployed a broken image and set the memory limit too low. I diagnosed each with kubectl describe, logs and events, and recovered using rollbacks."

## Q1. Why is Kubernetes used?

**Samjho:** Ek container chalana easy hai, lekin bahut saare containers ko reliably chalana mushkil hai: restart, scaling, load balancing, bina downtime update. Kubernetes yeh sab automatic karta hai. Aap "kya chahiye" likhte ho, aur woh lagatar wahi banaye rakhta hai.

**Bolo:** "Kubernetes is a container orchestrator. Running one container with docker run is easy, but running many containers reliably is hard. With Kubernetes I declare the desired state, for example three replicas of this image with these resource limits, and its controllers continuously make the actual state match it. It restarts failed containers, replaces lost pods, schedules pods on nodes with free capacity, load-balances through Services, and does rolling updates and rollbacks without downtime."

## Q2. Difference between Pod, Deployment and Service?

**Samjho:** Pod = ek waiter (temporary). Deployment = manager jo 3 waiter hamesha rakhta hai. Service = restaurant ka fixed phone number.

**Bolo:** "A Pod is the smallest deployable unit, one or more containers sharing an IP address. Pods are ephemeral: if one dies, it is replaced by a new pod with a new name and IP. A Deployment manages pods through a ReplicaSet. It keeps the desired number of replicas and handles rolling updates and rollbacks. A Service gives a stable IP and DNS name, and load-balances traffic to all ready pods that match its label selector. In my project the Deployment creates three pods labelled app equals flask-app, and the Service selects that label."

## Q3. How do replicas work?

**Samjho:** `replicas: 3` = desired state. ReplicaSet controller ginti karta rehta hai aur kam ho to banata hai, zyada ho to hatata hai. Isko **reconciliation loop** kehte hain.

**Bolo:** "Replicas is the desired number of identical pods. The Deployment creates a ReplicaSet, and its controller runs a reconciliation loop: it counts the pods matching its selector and creates or deletes pods until the count matches. Replicas give high availability, because one pod can fail without an outage, and capacity, because the Service spreads requests across them. I could see this in Grafana in my requests-per-pod panel."

## Q4. How does Kubernetes handle pod failure?

**Samjho:** Do level: (1) container crash ho ya liveness fail ho, to kubelet **wahi pod** mein container restart karta hai. (2) Pod hi delete ho jaaye ya node mar jaaye, to ReplicaSet **naya pod** banata hai. Saath mein readiness kharab pod ko traffic se hata deta hai.

**Bolo:** "At two levels. If a container crashes or fails its liveness probe, the kubelet restarts that container inside the same pod, and the restart count goes up. Repeated crashes lead to CrashLoopBackOff with increasing delays. If a pod is deleted or its node is lost, the ReplicaSet notices fewer pods than desired and creates a replacement pod. Meanwhile, the readiness probe removes unhealthy pods from the Service, so users are not sent to them. I tested this by deleting a pod and watching a new one become ready within seconds."

## Q5. Liveness vs readiness probe?

**Samjho:** Readiness = "traffic de sakte hain?", fail hone pe Service se hatao. Liveness = "zinda hai?", fail hone pe restart. Liveness mein database check **kabhi mat** dalo.

**Bolo:** "A readiness probe answers: can this pod receive traffic right now? If it fails, the pod is removed from the Service endpoints but not restarted. That is useful during startup or temporary overload. A liveness probe answers: is this container broken beyond recovery? If it fails, the kubelet restarts the container, which is useful for deadlocks. In my project both call the /health endpoint, but liveness is slower and more tolerant, because a restart is the more disruptive action. A common mistake is checking a database in the liveness probe: if the database goes down, every pod restarts in a loop."

## Q6. How does Prometheus collect metrics?

**Samjho:** Pull model, har 15 second. Targets Kubernetes API se discover hote hain (RBAC chahiye). Time series = naam + labels + value + time.

**Bolo:** "Prometheus uses a pull model. Every fifteen seconds it sends an HTTP request to each target's metrics endpoint and stores the values as time series, identified by a metric name and labels. It finds targets through Kubernetes service discovery by asking the API server for pods and nodes, which is why it needs RBAC permissions. Relabeling rules decide which targets to keep. I scrape cAdvisor in the kubelet for container CPU and memory, and my app's /metrics endpoint, where I use the prometheus_client library to expose a request counter and a latency histogram."

## Q7. How does Grafana visualise data?

**Samjho:** Grafana data store nahi karta. Prometheus se PromQL query karke graph banata hai. Humne provisioning se data source aur dashboard files se banaye.

**Bolo:** "Grafana does not store metrics itself. It connects to Prometheus as a data source, sends PromQL queries for the selected time range, and renders the results as panels like time-series graphs and stat panels. In my project the data source and the dashboard are provisioned from files in ConfigMaps, so they are version-controlled in Git and come back automatically if Grafana restarts."

## Q8. How do you troubleshoot a failed deployment?

**Samjho:** get, describe (events), logs (--previous), endpoints, theek karo ya rollout undo.

**Bolo:** "I follow the same order every time. First, kubectl get pods to see the status, such as ImagePullBackOff, CrashLoopBackOff, Pending, or zero of one ready. Second, kubectl describe pod, because the events at the bottom usually say exactly what failed. Third, kubectl logs with --previous if the container crashed. If the app runs but cannot be reached, I check the Service endpoints, because empty endpoints mean a label mismatch or no ready pods. To recover quickly I use kubectl rollout undo, then I investigate. For example, I deployed an image tag that did not exist. The new pod went into ImagePullBackOff, but because maxUnavailable was zero the old pods kept serving traffic, and a rollback fixed it in seconds."

## Follow-up sawaal (chhote answers)

| Sawaal | Hinglish mein samjho | English mein bolo |
|---|---|---|
| Requests vs limits? | Request = guarantee (scheduler dekhta hai), limit = max | "Requests are reserved and used for scheduling; limits are the maximum. Over the CPU limit the container is throttled; over the memory limit it is OOMKilled." |
| Exit code 137? | 128 + 9 (SIGKILL), yaani memory zyada | "The process was killed with SIGKILL, usually by the OOM killer for exceeding its memory limit." |
| Service types? | ClusterIP andar, NodePort node pe, LoadBalancer cloud | "ClusterIP is internal only, NodePort also opens a port on every node, LoadBalancer adds a cloud load balancer." |
| ConfigMap kyun? | Image badle bina settings badlo | "To change configuration without rebuilding the image, so the same image moves from dev to production." |
| ConfigMap vs Secret? | Secret sensitive data ke liye, base64 (encryption nahi) | "Secrets are for sensitive data. They are only base64-encoded by default, so access must be restricted with RBAC." |
| Rolling update? | Naya ReplicaSet upar, purana neeche, readiness ke hisaab se | "A new ReplicaSet scales up while the old one scales down, controlled by maxSurge and maxUnavailable and gated by readiness." |
| Rollback kaise? | `kubectl rollout undo` | "kubectl rollout undo returns to the previous ReplicaSet revision." |
| `rate()` kyun? | Counter sirf badhta hai | "Counters only increase, so rate gives the per-second change, which is what we want to graph." |
| Helm kyun nahi? | Pehle basics samajhne the | "I wanted to understand every object first. Helm would be my next step to package and version these manifests." |
| Non-root kyun? | Hack hua to kam power | "If the app is compromised, the attacker has fewer privileges inside the container." |
| Ek gunicorn worker kyun? | Pods se scale, metrics ek process mein | "In Kubernetes we scale with pods, not processes. It also keeps the Prometheus counters in one process." |
| Container vs VM? | Container host kernel share karta hai | "A VM virtualises hardware and runs its own kernel; a container is an isolated process sharing the host kernel, using namespaces and cgroups." |
| Docker layer caching? | Pehle requirements, phir code | "Each instruction is a cached layer. I copy requirements first so dependencies are only reinstalled when they change." |
| Kubernetes control plane? | API server, etcd, scheduler, controller manager | "The API server is the entry point, etcd stores state, the scheduler places pods, and controllers run reconciliation loops." |
| Pod Pending kyun hota hai? | Kisi node pe requests jitni jagah nahi | "Usually no node has enough free CPU or memory for its requests. kubectl describe shows the reason." |
| Aage kya add karoge? | CI/CD, HPA, alerts, Ingress, Helm | "A GitHub Actions pipeline to test and build the image, a HorizontalPodAutoscaler, Alertmanager alerts, an Ingress, and Helm packaging." |

## "Kya problem aayi thi?" (yeh zaroor poochenge)

Inme se 2-3 apne shabdon mein bolne layak taiyaar rakho:

1. **CRLF line endings:** "Git warned that LF would be replaced by CRLF on Windows. Shell scripts with CRLF fail in Linux containers, so I added a .gitattributes file to force LF endings."
2. **Load test CPU limit tak nahi pahuncha:** "With one sequential client, only one pod was busy at a time, so I never reached the CPU limit. I added parallel clients to the load script."
3. **OOM test reject hua:** "When I lowered only the memory limit, Kubernetes rejected it, because a request cannot be larger than its limit. I had to lower both."
4. **Namespace order:** "kubectl applies files in a folder alphabetically, so I numbered the monitoring files to create the namespace first."
5. **Deploy karte waqt jo asli error aaye**, woh bhi likh lo. Asli experience sabse achha answer hota hai.

## Resume description (seedha copy karo)

**Kubernetes-Based Application Deployment and Monitoring** | Docker, Kubernetes (Minikube), Prometheus, Grafana, Python Flask, Linux, Git

- Containerised a Python Flask web application with a slim, non-root Docker image using layer caching, and deployed it to Kubernetes (Minikube) with Deployment, Service and ConfigMap manifests.
- Configured 3 replicas with rolling updates (zero unavailable pods), readiness and liveness probes, and CPU/memory requests and limits.
- Set up Prometheus with Kubernetes service discovery and RBAC to scrape container CPU/memory (cAdvisor) and custom application metrics, and visualised them on a provisioned Grafana dashboard.
- Validated self-healing and failure handling by deleting pods, failing health checks, deploying a broken image and triggering OOMKills; diagnosed each with kubectl describe, logs and events and recovered with rollbacks.
- Documented architecture, deployment and troubleshooting steps, and added automated tests that validate the application and the consistency of the Kubernetes manifests.

**Dhyan rakho:** resume pe sirf woh likho jo aapne khud kiya aur samjha hai. Point 4 tabhi likhna jab Part 8 ke experiments khud kar liye hon.

## Interview tips

- **"Mujhe nahi pata"** bolna theek hai, phir yeh add karo: *"but I would check it with kubectl describe"* ya *"I would look it up in the documentation"*. Andaaza lagake galat bolna bura hai.
- Jawab chhota rakho, aur **example apne project se** do.
- Whiteboard pe architecture diagram bana ke samjhao (Part 1 wala).
- Interviewer GitHub kholega, isliye README aur screenshots achhe hone chahiye.
