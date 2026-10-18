from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- The four layers, lowest to highest priority ----
DEFAULTS = {"port": 8000, "workers": 1, "debug": False, "log_level": "info", "api_key": "default-secret-000"}

YAML_LAYER = {"debug": False, "log_level": "info", "api_key": "key-rumnblaa9q"}   # config.development.yaml

DOTENV_TEXT = """
APP_PORT=8555
NUM_WORKERS=12
APP_DEBUG=true
APP_API_KEY=key-drb9ou0r91
"""

OS_ENV = {"APP_PORT": "8567", "APP_WORKERS": "4", "APP_LOG_LEVEL": "debug", "APP_API_KEY": "key-5khsfkolll"}

ALIASES = {"NUM_WORKERS": "workers"}   # .env alias


def parse_dotenv(text):
    out = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        if name in ALIASES:
            out[ALIASES[name]] = value.strip()
        elif name.startswith("APP_"):
            out[name[4:].lower()] = value.strip()
    return out


def parse_os_env(env):
    return {n[4:].lower(): v for n, v in env.items() if n.startswith("APP_")}


def to_bool(value):
    return str(value).strip().lower() in ("true", "1", "yes", "on")


def coerce(key, value):
    if key in ("port", "workers"):
        return int(str(value).strip())
    if key == "debug":
        return to_bool(value)
    return str(value)


def build_config(set_params):
    merged = {}
    for layer in (DEFAULTS, YAML_LAYER, parse_dotenv(DOTENV_TEXT), parse_os_env(OS_ENV)):
        merged.update(layer)
    for item in set_params:                      # CLI overrides: highest priority
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        merged[key.strip()] = value
    result = {k: coerce(k, v) for k, v in merged.items()}
    result["api_key"] = "****"                   # never reveal the real key
    return result


@app.get("/effective-config")
@app.get("/api/effective-config")
@app.get("/api/index/effective-config")
def effective_config(request: Request):
    return build_config(request.query_params.getlist("set"))


# Safety net: Vercel may hand the app a different path than the one typed in the browser
# (for example /api/index), which FastAPI would answer with {"detail":"Not Found"}.
# This catch-all (it must stay LAST) returns the config for any other GET path.
@app.get("/{full_path:path}")
def anything_else(full_path: str, request: Request):
    return build_config(request.query_params.getlist("set"))
