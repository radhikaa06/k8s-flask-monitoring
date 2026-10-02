# Part 2 - Zero se Basics: Networking, Linux, Git, Python

Is part mein woh basic cheezein hain jinke bina aage ka kuch samajh nahi aayega. Agar pehle se aata hai to jaldi se padh lo, revision ho jaayega.

## Networking basics

### Server aur client

- **Client:** jo request bhejta hai, jaise aapka browser ya `curl` command.
- **Server:** jo request sunta hai aur jawab deta hai, jaise hamara Flask app.

Ek hi laptop pe dono ho sakte hain. Jab aap `localhost:5000` kholte ho, to browser (client) aur Flask (server) dono aapke laptop pe hote hain.

### IP address aur port

- **IP address:** computer ka address, jaise ghar ka address. Example: `192.168.1.5`, `10.244.0.12`.
- **Port:** us computer ke andar kaun sa program, jaise building ke andar flat number. Example: `5000`, `80`, `9090`.

Poora address = IP + port, jaise `10.244.0.12:5000`.

**localhost / 127.0.0.1** ka matlab hai "yahi computer".

**0.0.0.0 pe bind karna** ka matlab hai "har network interface pe suno". Container ke andar app ko `0.0.0.0` pe sunna padta hai, warna container ke bahar se koi connect nahi kar paayega. Isliye `gunicorn.conf.py` mein `bind = "0.0.0.0:5000"` likha hai.

### Project mein use hue ports

| Port | Kaun | Kahan |
|---|---|---|
| 5000 | Flask app | Container ke andar |
| 80 | flask-app-service | Cluster ke andar |
| 30080 | flask-app-service (NodePort) | Minikube node pe |
| 9090 / 30090 | Prometheus | Cluster ke andar / node pe |
| 3000 / 30030 | Grafana | Cluster ke andar / node pe |

### HTTP request aur response

Browser jab koi page kholta hai, to ek **HTTP request** bhejta hai:

```
GET /health HTTP/1.1
Host: localhost:5000
```

Server **HTTP response** wapas bhejta hai:

```
HTTP/1.1 200 OK
Content-Type: application/json

{"status": "ok", "pod": "flask-app-7d9f-abc12"}
```

**HTTP methods:**

| Method | Matlab | Project mein |
|---|---|---|
| GET | Data lao | `/`, `/health`, `/metrics`, `/work` |
| POST | Kuch karo / data bhejo | `/fail` |

**Status codes:** (yeh interview mein bhi poochte hain)

| Code | Matlab | Project mein kab |
|---|---|---|
| 200 | OK, sab theek | `/health` jab app healthy hai |
| 404 | Page nahi mila | Galat URL |
| 500 | Server mein error | Code mein bug |
| 503 | Service unavailable (abhi kaam nahi kar sakta) | `/health` jab `/fail` call ho chuka ho |

Kubernetes ke probes ke liye **200-399 = pass**, aur baaki sab **fail**.

### JSON

JSON data likhne ka format hai, jaise Python dictionary:

```json
{"status": "ok", "pod": "flask-app-abc"}
```

APIs aksar JSON mein jawab dete hain. Hamara `/health` bhi JSON deta hai.

### DNS

DNS naam ko IP mein badalta hai, jaise phone ki contact list. `google.com` se `142.250.x.x` milta hai.

Kubernetes ke andar bhi DNS hota hai: `flask-app-service` naam likhne se Service ka IP mil jaata hai. Isliye Grafana ki config mein `http://prometheus:9090` likha hai, IP nahi.

## Linux basics

### Terminal aur shell

**Terminal** woh window hai jahan commands likhte ho. **Shell** woh program hai jo commands samajhta hai: bash, PowerShell, zsh.

Windows pe hum **Git Bash** use karte hain, jo Git ke saath aata hai aur Linux jaisi bash commands chalata hai. Isse hamari `.sh` scripts Windows pe bhi chal jaati hain.

### Kuch zaroori commands

| Command | Kya karti hai |
|---|---|
| `pwd` | Abhi kis folder mein ho |
| `ls` | Folder mein kya hai |
| `cd folder` | Folder mein jao |
| `mkdir -p a/b` | Folder banao (`-p` = parent bhi bana do) |
| `cat file` | File ka content dikhao |
| `grep word file` | File mein word dhoondho |
| `curl url` | URL pe request bhejo, jawab dikhao |
| `echo $VAR` | Variable ki value dikhao |
| `cmd1 \| cmd2` | Pipe: cmd1 ka output cmd2 ko do |
| `chmod +x file` | File ko executable banao |

### Process

Jo program chal raha hai, use **process** kehte hain. Har process ka ek number hota hai (**PID**). Container ke andar main process ka PID 1 hota hai. Hamare case mein woh gunicorn hai.

### Environment variables

Ye process ko di gayi **settings** hain, `NAAM=value` format mein:

```bash
export PORT=5050
echo $PORT          # 5050
```

Hamara app `config.py` mein `os.getenv("PORT", "5000")` se padhta hai: "PORT variable ho to woh lo, warna 5000."

**Kyun?** Code badle bina behaviour badal sakte ho. Kubernetes isi tarah ConfigMap se settings deta hai.

### Signals aur exit codes

**Signal** ek process ko bheja gaya message hota hai:

| Signal | Number | Matlab |
|---|---|---|
| SIGTERM | 15 | "Please band ho jao" (process saaf-safai karke band hota hai) |
| SIGKILL | 9 | "Turant maro" (process kuch nahi kar sakta) |

**Exit code** process band hone pe deta hai: `0` = success, aur baaki sab = koi problem.

Signal se mare process ka exit code **128 + signal number** hota hai. Isliye **OOMKilled = 137** (128 + 9). Yeh interview mein bahut poocha jaata hai.

### Kernel, namespaces, cgroups

Yeh container ki neev hain.

- **Kernel:** Linux ka core. Hardware, memory aur processes sambhalta hai.
- **Namespaces:** process ko lagta hai woh akela hai, uska apna hostname, network aur process list hai. Isse **isolation** milta hai.
- **cgroups (control groups):** process kitna CPU/memory use kar sakta hai, uski **limit**. Kubernetes ke resource limits isi se lagte hain.

**Container = normal Linux process + namespaces (alag duniya) + cgroups (limits).** Yeh koi alag VM nahi hai.

Windows pe kernel Linux ka nahi hai, isliye **WSL2** chahiye. Woh Windows ke andar ek asli Linux kernel chalata hai.

## Git aur GitHub basics

| Term | Matlab |
|---|---|
| Repository (repo) | Project folder jiski history Git rakhta hai (`.git` folder) |
| Commit | Ek snapshot / save point, message ke saath |
| Branch | Kaam ki alag line. Humari main branch `main` hai |
| Remote | GitHub pe repo ki copy (`origin`) |
| Push | Local commits GitHub pe bhejna |
| Pull | GitHub se naye commits laana |
| `.gitignore` | Kaun si files Git mein nahi jaani chahiye (`.venv`, cache) |
| `.gitattributes` | Files ko kaise treat karna hai (line endings) |

### Basic workflow

```bash
git status                      # kya badla hai
git add file                    # commit ke liye select karo
git commit -m "message"         # save point banao
git push                        # GitHub pe bhejo
git log --oneline               # history dekho
```

### Author identity

Har commit pe likha hota hai ki kisne kiya: `user.name` aur `user.email`. GitHub **email** se pehchanta hai ki commit kis account ka hai. Is project mein repo-level config set kiya gaya:

```bash
git config user.name "Radhika Agarwal"
git config user.email "theradhika2410@gmail.com"
```

`--global` ke bina yeh setting sirf **isi repo** pe lagti hai.

### Line endings (CRLF vs LF)

Windows har line ke end mein `\r\n` (CRLF) lagata hai, aur Linux sirf `\n` (LF). Agar shell script CRLF ke saath Linux container mein chale, to error aata hai: `$'\r': command not found`.

Isliye `.gitattributes` mein `* text=auto eol=lf` likha hai, jisse Git hamesha LF rakhta hai.

### Achha commit message

```
Add readiness probe to flask-app deployment     <- chhoti summary, command ki tarah

Pods were receiving traffic before Flask had started.   <- kyun kiya
```

## Python basics (jo is project mein chahiye)

### Virtual environment (venv)

Har project ki libraries alag rakhne ka tareeka:

```bash
python -m venv .venv               # .venv folder banao
source .venv/Scripts/activate      # activate (Linux/Mac: .venv/bin/activate)
pip install -r requirements.txt    # libraries install
```

**Kyun?** Ek project ko Flask 3 chahiye aur doosre ko Flask 2, to dono ek saath chal sakte hain.

### pip aur requirements.txt

`pip` Python ka package installer hai. `requirements.txt` mein libraries **exact version** ke saath likhi hain:

```
Flask==3.1.0
prometheus-client==0.21.1
gunicorn==23.0.0
```

**Version pin kyun?** Aaj aur 6 mahine baad bhi same version install ho. Isse "kal tak chal raha tha" wali problem nahi aati.

### Flask kaise kaam karta hai

```python
from flask import Flask
app = Flask(__name__)

@app.get("/health")          # decorator: "GET /health aaye to neeche wala function chalao"
def health():
    return {"status": "ok"}
```

- `@app.get(...)` ko **decorator** kehte hain. Yeh URL ko function se jodta hai.
- Function jo return karta hai, woh response ban jaata hai.

### Flask dev server vs gunicorn

| | Flask dev server (`app.run()`) | Gunicorn |
|---|---|---|
| Kis liye | Development, debugging | Production |
| Speed / stability | Kam | Zyada |
| Auto-reload | Haan | Nahi |
| Windows pe | Chalta hai | Nahi chalta (sirf Linux/Mac) |

Isliye laptop pe testing `python app/app.py` se hoti hai, aur container mein gunicorn chalta hai.

**Workers aur threads:** Worker ek alag process hai, aur thread ek process ke andar kaam karne wali line. Humne `workers = 1, threads = 4` rakha. Kubernetes mein scale **pods badha ke** karte hain, workers badha ke nahi.

### pytest

Python ka testing tool hai. `test_` se shuru hone wale functions apne aap chalaata hai:

```python
def test_health_is_ok(client):
    response = client.get("/health")
    assert response.status_code == 200     # agar galat hua to test FAIL
```

`assert` ka matlab hai "yeh sach hona chahiye, warna fail".
