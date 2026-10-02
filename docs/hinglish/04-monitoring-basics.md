# Part 4 - Monitoring Basics: Prometheus aur Grafana

## Monitoring kyun?

App chal raha hai, lekin:

- Kya woh **slow** ho raha hai?
- Memory **dheere-dheere badh** rahi hai (memory leak)?
- Kitne log use kar rahe hain?
- Raat 3 baje crash hua to **kyun**?

Bina monitoring ke yeh sab andaaza hai. Monitoring se **data** milta hai.

## Observability ke 3 pillars

| Pillar | Kya hai | Example | Tool |
|---|---|---|---|
| **Metrics** | Numbers, time ke saath | CPU = 0.12 cores at 10:05 | Prometheus (**is project mein**) |
| **Logs** | Text events | `GET /health 200` | `kubectl logs`, Loki, ELK |
| **Traces** | Ek request ka poora safar, services ke beech | Request ne 3 services mein 200ms liye | Jaeger, Tempo |

Is project mein focus **metrics** pe hai. Logs `kubectl logs` se dekh lete hain.

## Kya monitor karein? (Golden signals)

Google SRE book ke **4 golden signals**:

| Signal | Matlab | Hamara dashboard panel |
|---|---|---|
| **Latency** | Response kitni der mein aaya | 95th percentile response time |
| **Traffic** | Kitni requests aa rahi hain | Requests per second |
| **Errors** | Kitni requests fail hui | `status` label (5xx count) |
| **Saturation** | Resources kitne bhare hain | CPU aur memory panels |

## Metric types

| Type | Kya hai | Example | Kaise padhein |
|---|---|---|---|
| **Counter** | Sirf badhta hai (restart pe 0) | `flask_http_requests_total` | Hamesha `rate()` ke saath |
| **Gauge** | Upar-neeche ho sakta hai | `container_memory_working_set_bytes` | Seedha value |
| **Histogram** | Values ko buckets mein ginta hai | `flask_http_request_duration_seconds` | `histogram_quantile()` se percentile |
| **Summary** | Histogram jaisa, client pe calculate | (use nahi kiya) | - |

**Counter pe `rate()` kyun?** Counter ki value "kul 50,000 requests" batati hai, jo kaam ki nahi. `rate()` batata hai "abhi 12 requests per second", jo kaam ki hai.

## Time series aur labels

Prometheus mein har data point aisa dikhta hai:

```
flask_http_requests_total{endpoint="/health", method="GET", status="200", pod="flask-app-abc"}  42  @10:05:00
         naam                                  labels                                          value  time
```

**Naam + labels ka har unique combination = ek time series.**

Labels se filter aur group karte hain: "sirf `/work` ki requests", "har pod ka alag".

### Cardinality (zaroori concept)

Agar label mein **unlimited values** aa sakti hain (jaise user ID ya poora URL), to lakhon time series ban jaati hain aur Prometheus ki memory bhar jaati hai. Isko **high cardinality** problem kehte hain.

Isliye hamare app mein `endpoint` label mein **route pattern** (`/work`) jaata hai, poora URL (`/work?ms=123`) nahi.

## Prometheus kaise kaam karta hai

### Pull model

```
     har 15 second
Prometheus  ------ GET /metrics ------>  App pod
            <----- text metrics -------
     (store karo time ke saath)
```

Prometheus **khud jaake** data leta hai, aur app kuch push nahi karti. Isko **scraping** kehte hain.

**Pull ke fayde:**

- Target down hai to Prometheus ko turant pata chalta hai (`up = 0`)
- App ko Prometheus ka address jaanne ki zaroorat nahi
- Browser mein `/metrics` khol ke khud dekh sakte ho ki kya bhej rahe ho

(Push model bhi hota hai, jaise Pushgateway short jobs ke liye. Lekin default pull hai.)

### `/metrics` ka format

```
# HELP flask_http_requests_total Total HTTP requests
# TYPE flask_http_requests_total counter
flask_http_requests_total{endpoint="/health",method="GET",status="200"} 42.0
```

Python ki `prometheus_client` library yeh format apne aap banati hai.

### Targets aur jobs

- **Target:** ek address jahan se scrape karna hai (`10.244.0.5:5000`)
- **Job:** ek jaise targets ka group (`app-pods`)

### Service discovery

Pods ke IP badalte rehte hain, to targets ki list hath se nahi likh sakte. Prometheus **Kubernetes API se poochta hai**: "saare pods ki list do." Naya pod aaya to apne aap target ban jaata hai. Iske liye RBAC permission chahiye (Part 3).

### Relabeling

Discovery se **saare** pods milte hain, aur relabeling rules unhe filter aur rename karte hain:

- `action: keep` + annotation `prometheus.io/scrape: "true"` ka matlab hai sirf woh pods jinpe yeh annotation hai
- Port ka naam `http` hai to sirf woh port rakho
- Pod ka naam `pod` label mein daalo, taaki graph mein dikhe

### cAdvisor

Container Advisor, jo kubelet mein built-in hai. Har container ka CPU, memory, network aur disk naapta hai. Hamare app ko CPU/memory metrics khud nahi dene padte, **cAdvisor deta hai**.

### Prometheus storage

Prometheus ka apna **time-series database (TSDB)** hai, disk pe. Humne `emptyDir` volume diya, jo pod restart pe saaf ho jaata hai. Learning ke liye theek hai, production mein PersistentVolume chahiye.

## PromQL (Prometheus Query Language)

| Query | Matlab |
|---|---|
| `up` | Har target: 1 = theek, 0 = down |
| `flask_http_requests_total` | Raw counter values |
| `rate(flask_http_requests_total[1m])` | Pichle 1 minute mein per-second rate |
| `sum(rate(flask_http_requests_total[1m]))` | Saare pods mila ke total rate |
| `sum by (pod) (rate(...[1m]))` | Har pod ka alag total |
| `container_memory_working_set_bytes{container="flask-app"}` | `{}` se label filter |
| `histogram_quantile(0.95, sum by (le) (rate(..._bucket[5m])))` | 95% requests isse tez the (p95 latency) |

**`[1m]`** = range: pichle 1 minute ka data.
**`sum by (pod)`** = pod ke hisaab se group karke jod do.
**p95 = 0.2s** ka matlab hai 95% requests 0.2 second se kam mein poori hui. Average ki jagah percentile isliye dekhte hain kyunki average slow requests ko chhupa deta hai.

### CPU ka formula samjho

```
rate(container_cpu_usage_seconds_total[1m])
```

`container_cpu_usage_seconds_total` = container ne ab tak kul kitne **CPU-seconds** use kiye. `rate()` = har second mein kitne CPU-seconds, yaani **kitne cores**. Value `0.25` = 0.25 core = 250m. Yeh hamari limit ke barabar hai.

### Memory: working set kyun?

`container_memory_working_set_bytes` = woh memory jo kernel aasani se wapas nahi le sakta. **OOM killer yahi dekhta hai**, isliye limit se compare isi ko karte hain.

## Grafana

### Grafana kya hai?

Visualization tool. **Khud koi data store nahi karta.** Data sources (Prometheus, MySQL, Loki...) se query karke graphs banata hai.

| Term | Matlab |
|---|---|
| **Data source** | Data kahan se aayega (hamara: Prometheus) |
| **Dashboard** | Panels ka collection |
| **Panel** | Ek graph/number. Ek query + visualization type |
| **Visualization** | Time series (line graph), Stat (bada number), Gauge, Table |
| **Provisioning** | Data source aur dashboard **files se** apne aap bana dena |

### Provisioning kyun?

Hath se click karke dashboard banaya, Grafana pod restart hua, aur sab gaya (kyunki storage `emptyDir` hai). **Provisioning** se:

- Data source aur dashboard YAML/JSON files mein hain, **Git mein**
- Grafana start hote hi apne aap load
- Kitni baar bhi reinstall karo, same dashboard

Isi soch ko **"Infrastructure as Code"** kehte hain: config ko code ki tarah rakho.

### `$__rate_interval`

Grafana ka special variable. Scrape interval aur zoom level dekh ke `rate()` ke liye sahi window chunta hai. Window bahut chhoti ho to graph khaali dikhega, isliye yeh safe option hai.

## Prometheus vs Grafana (ek line mein)

**Prometheus collect aur store karta hai. Grafana dikhata hai.**

Prometheus ka apna basic graph UI bhi hai (Graph tab), lekin dashboards ke liye Grafana kahin behtar hai.
