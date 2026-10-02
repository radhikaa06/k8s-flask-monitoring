# Part 1 - Shuruaat: Yeh Project Kya Hai

## Yeh guide kiske liye hai

Yeh guide aapke liye hai agar:

- Aapko Linux, Git, Docker aur Kubernetes ka **thoda-bahut** idea hai, lekin sab cheezein ek saath jodna nahi aata
- Aap DevOps internship ki tayyari kar rahe ho
- Aap chahte ho ki interview mein project ke baare mein **apne shabdon mein** confidently bol sako

Yeh guide **zero se** shuru hoti hai. Agar koi topic pehle se aata hai to skip kar do, koi baat nahi.

## Guide kaise padhein

| Part | Kya milega | Kab padhna hai |
|---|---|---|
| Part 1 | Project ka overview | Sabse pehle |
| Part 2 | Networking, Linux, Git, Python ke basics | Agar basics kamzor hain |
| Part 3 | Docker aur Kubernetes ke basics | Zaroor padhna |
| Part 4 | Monitoring, Prometheus, Grafana ke basics | Zaroor padhna |
| Part 5 | Project ki har file, line by line | Code samajhne ke liye |
| Part 6 | Is project ko banate waqt kya-kya kiya gaya | Project ki history samajhne ke liye |
| Part 7 | Project ko laptop pe chalana, step by step | Jab chalana ho |
| Part 8 | Cheezein jaan-bujh ke todna aur theek karna | Chalane ke baad |
| Part 9 | Interview questions aur answers | Interview se pehle |
| Part 10 | Aage kya seekhein, glossary, cheat sheet | Revision ke liye |
| Appendix | Project ka poora source code | Reference ke liye |

**Ek zaroori baat:** Har command ke saath yeh 5 cheezein di gayi hain:

- **Kya:** command kya karti hai
- **Kyun:** iski zaroorat kyun hai
- **Kahan:** kis terminal aur kis folder mein chalani hai
- **Expected:** sahi chalne pe kya dikhega
- **Error aaye to:** common galtiyan aur unka solution

## Project ek line mein

**Ek chhote Python Flask web app ko Docker mein pack karke, Kubernetes (Minikube) pe 3 copies mein chalaya, aur Prometheus aur Grafana se uski CPU, memory aur traffic ki monitoring ki.**

## Project ka flow (badi picture)

![Architecture](../architecture.svg)

Is diagram ko step by step samjho:

1. **Code:** `app/` folder mein ek chhota Flask app hai.
2. **Docker build:** `Dockerfile` padh ke Docker ek **image** banata hai: `flask-app:1.0.0`. Image ek sealed dabba hai jisme Python, libraries aur code sab hai.
3. **Image load:** Yeh image **Minikube** ke andar bheji jaati hai. Minikube aapke laptop pe chalne wala chhota Kubernetes cluster hai.
4. **Deployment:** Kubernetes ko bola "is image ke 3 pods chalao". Pod matlab app ki ek running copy.
5. **Service:** 3 pods ke aage ek fixed address hai: `flask-app-service`. Browser se request aati hai to Service use kisi ek pod ko bhej deta hai.
6. **Prometheus:** Har 15 second mein jaake poochta hai, "CPU kitna use hua? Memory kitni? Kitni requests aayi?" Aur yeh sab numbers store karta hai.
7. **Grafana:** Prometheus se numbers leke graphs banata hai. Aap browser mein dashboard dekhte ho.

## Final result kaisa dikhega

Jab project chal raha hoga:

- Browser mein app ka homepage dikhega, likha hoga "Served by pod flask-app-xxxxx". Refresh karne pe kabhi-kabhi pod ka naam badlega (load balancing).
- `kubectl get pods` chalane pe 3 pods `Running` dikhenge.
- Grafana mein dashboard dikhega: CPU graph, memory graph, requests per second, response time, aur "healthy pods = 3".
- Ek pod delete karoge to kuch second mein naya pod apne aap aa jaayega. Isko **self-healing** kehte hain.

## Is project se kya-kya seekhoge

| Skill | Project mein kahan |
|---|---|
| Containerization | Dockerfile, image, layers |
| Container orchestration | Deployment, ReplicaSet, Service |
| High availability | 3 replicas, self-healing |
| Health checks | Readiness aur liveness probes |
| Resource management | Requests, limits, OOMKilled, throttling |
| Zero-downtime deployment | Rolling update, rollback |
| Configuration management | ConfigMap, environment variables |
| Security basics | Non-root container, RBAC |
| Monitoring | Prometheus, PromQL, service discovery |
| Visualization | Grafana dashboard, provisioning |
| Troubleshooting | describe, logs, events, rollout undo |
| Automation | Bash scripts, automated tests |
| Version control | Git, GitHub, commits |

## Project ke rules (jo humne follow kiye)

1. **Simple rakho.** Helm, Terraform, cloud jaisa kuch nahi. Pehle basics pakke karo.
2. **Har line samajh aani chahiye.** Interview mein koi bhi line pooch sakte hain.
3. **DRY (Don't Repeat Yourself):** har jaankari **sirf ek jagah** likhi ho. Isko Part 5 mein detail mein samjhaya hai.
4. **Dikhawe ke liye koi technology nahi.** Jo zaroori hai, bas wahi.
