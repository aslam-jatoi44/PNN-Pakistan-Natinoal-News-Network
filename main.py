import os
from fastapi import Depends, FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings
from app.database import init_db
from app.middleware.csrf import get_csrf_token, verify_csrf

# Ensure backwards-compatibility for TemplateResponse(name, context) with Starlette 0.38+
_original_template_response = Jinja2Templates.TemplateResponse

def _patched_template_response(self, *args, **kwargs):
    if args and isinstance(args[0], str):
        name = args[0]
        context = args[1] if len(args) > 1 else kwargs.pop("context", {})
        request = context.get("request") if isinstance(context, dict) else kwargs.pop("request", None)
        if isinstance(context, dict) and request is not None and "csrf_token" not in context:
            context["csrf_token"] = get_csrf_token(request)
        return _original_template_response(self, request=request, name=name, context=context, **kwargs)
    context = kwargs.get("context")
    request = kwargs.get("request") or (context.get("request") if isinstance(context, dict) else None)
    if isinstance(context, dict) and request is not None and "csrf_token" not in context:
        context["csrf_token"] = get_csrf_token(request)
    return _original_template_response(self, *args, **kwargs)

Jinja2Templates.TemplateResponse = _patched_template_response

# Import routers
from app.routers import auth, admin, director, bureau, reporter, news, geography, publication, public
from app.middleware.rate_limit import rate_limit_middleware

app = FastAPI(
    title="PNN — Pakistan National News Network",
    description="Complete News Network Management System",
    version="1.0.0",
    dependencies=[Depends(verify_csrf)],
)

# Middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    https_only=settings.COOKIE_SECURE,
    same_site="lax",
)
app.add_middleware(BaseHTTPMiddleware, dispatch=rate_limit_middleware)

# Directories
os.makedirs("app/static/css", exist_ok=True)
os.makedirs("app/static/js", exist_ok=True)
os.makedirs("app/static/img", exist_ok=True)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(auth.router, tags=["auth"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(director.router, prefix="/director", tags=["director"])
app.include_router(bureau.router, prefix="/bureau", tags=["bureau"])
app.include_router(reporter.router, prefix="/reporter", tags=["reporter"])
app.include_router(news.router, prefix="/news", tags=["news"])
app.include_router(geography.router, prefix="/geography", tags=["geography"])
app.include_router(publication.router, prefix="/publish", tags=["publication"])
app.include_router(public.router, prefix="", tags=["public"])

# Urdu RTL homepage preview (/ur) - read-only, does not replace /home
from app.routers import public_ur
app.include_router(public_ur.router, prefix="", tags=["public-preview"])


@app.on_event("startup")
async def startup_event():
    if settings.AUTO_INIT_DB:
        init_db()
        print("[OK] PNN Database initialized (AUTO_INIT_DB=true)")
    else:
        print("[OK] PNN Database auto-init skipped (AUTO_INIT_DB=false)")
    print("[RUNNING] PNN News Network is running")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return RedirectResponse(url="/home")


@app.get("/dashboard")
async def dashboard(request: Request):
    from app.middleware.auth_middleware import get_current_user_from_cookie
    user = get_current_user_from_cookie(request)
    if not user:
        return RedirectResponse(url="/login")
    role_redirects = {
        "super_admin": "/admin/dashboard",
        "director_news": "/director/dashboard",
        "bureau_chief": "/bureau/dashboard",
        "reporter": "/reporter/dashboard",
    }
    return RedirectResponse(url=role_redirects.get(user.role.value, "/login"))


@app.get("/health")
async def health():
    return {"status": "ok", "service": "PNN News Network"}
