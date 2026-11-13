
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.exc import IntegrityError

from database import SessionLocal
from models import User, Simulation
from auth import hash_password, verify_password


# =====================================
# 1. CONFIGURATION DE L'APPLICATION
# =====================================

app = FastAPI(title="ProcessLab - Filtration")

# Sessions sécurisées par cookie signé
app.add_middleware(
    SessionMiddleware,
    secret_key="6vr6xFUfxHZFqvSUFI_HIsKJ8HuflSqfJ3fI5nOOdNg",
    same_site="lax",
    https_only=False
)

templates = Jinja2Templates(directory="templates")

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)


# =====================================
# 2. PAGE D'INSCRIPTION
# =====================================

@app.get("/register", response_class=HTMLResponse)
async def page_register(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={"request": request}
    )


@app.post("/register", response_class=HTMLResponse)
async def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):

    db = SessionLocal()

    try:
        # Vérification du mot de passe
        if len(password) < 8:
            return templates.TemplateResponse(
                request=request,
                name="register.html",
                context={
                    "request": request,
                    "erreur": "Le mot de passe doit contenir au moins 8 caractères."
                },
                status_code=400
            )

        # Vérifier si le username existe déjà
        existing_user = db.query(User).filter(
            User.username == username
        ).first()

        if existing_user:
            return templates.TemplateResponse(
                request=request,
                name="register.html",
                context={
                    "request": request,
                    "erreur": "Ce nom d'utilisateur existe déjà."
                },
                status_code=400
            )

        # Créer le nouvel utilisateur
        new_user = User(
            username=username,
            email=email,
            password_hash=hash_password(password)
        )

        db.add(new_user)
        db.commit()

        return RedirectResponse(
            url="/login",
            status_code=303
        )

    except IntegrityError:
        db.rollback()

        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "request": request,
                "erreur": "Cet email ou ce nom d'utilisateur est déjà utilisé."
            },
            status_code=400
        )

    finally:
        db.close()


# =====================================
# 3. PAGE DE CONNEXION
# =====================================

@app.get("/login", response_class=HTMLResponse)
async def page_login(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"request": request}
    )


@app.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):

    db = SessionLocal()

    try:
        user = db.query(User).filter(
            User.username == username
        ).first()

        if not user or not verify_password(
            password,
            user.password_hash
        ):
            return templates.TemplateResponse(
                request=request,
                name="login.html",
                context={
                    "request": request,
                    "erreur": "Username ou mot de passe incorrect."
                },
                status_code=401
            )

        # Création de la session utilisateur
        request.session.clear()
        request.session["user_id"] = user.id
        request.session["username"] = user.username

        return RedirectResponse(
            url="/",
            status_code=303
        )

    finally:
        db.close()


# =====================================
# 4. DECONNEXION
# =====================================

@app.post("/logout")
async def logout(request: Request):

    request.session.clear()

    return RedirectResponse(
        url="/login",
        status_code=303
    )


# =====================================
# 5. DASHBOARD PROTEGE
# =====================================

@app.get("/", response_class=HTMLResponse)
async def accueil(request: Request):

    user_id = request.session.get("user_id")

    if not user_id:
        return RedirectResponse(
            url="/login",
            status_code=303
        )

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request,
            "username": request.session.get("username")
        }
    )


# =====================================
# 6. CALCUL ET ENREGISTREMENT FILTRATION
# =====================================

@app.post("/calculer", response_class=HTMLResponse)
async def calculer(
    request: Request,
    m0: float = Form(...),
    x0: float = Form(...),
    residus: float = Form(...)
):

    user_id = request.session.get("user_id")

    if not user_id:
        return RedirectResponse(
            url="/login",
            status_code=303
        )

    context = {
        "request": request,
        "username": request.session.get("username"),
        "m0": m0,
        "x0": x0,
        "residus": residus
    }

    # Vérification des données
    if m0 <= 0 or residus < 0 or residus >= m0:

        context["erreur"] = "Vérifiez les données saisies."

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context=context
        )

    if x0 < 0 or x0 > 100:

        context["erreur"] = (
            "La concentration doit être entre 0 et 100 %."
        )

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context=context
        )

    # Calcul de filtration
    m1 = m0 - residus

    x1 = (m0 * (x0 / 100)) / m1

    # Vérification du bilan
    bilan = m0 - (m1 + residus)

    # Arrondir les résultats
    m1 = round(m1, 2)
    x1_final = round(x1 * 100, 2)
    bilan = round(bilan, 6)

    # Enregistrer la simulation dans MySQL
    db = SessionLocal()

    try:
        simulation = Simulation(
            user_id=user_id,
            debit_initial=m0,
            concentration_initiale=x0,
            residus=residus,
            debit_filtre=m1,
            concentration_finale=x1_final,
            bilan=bilan
        )

        db.add(simulation)
        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

    # Afficher les résultats
    context.update({
        "m1": m1,
        "x1": x1_final,
        "bilan": bilan
    })

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=context
    )

# =====================================
# 7. HISTORIQUE DES SIMULATIONS
# =====================================

@app.get("/historique", response_class=HTMLResponse)
async def historique(request: Request):

    user_id = request.session.get("user_id")

    if not user_id:
        return RedirectResponse("/login", status_code=303)

    db = SessionLocal()

    try:
        simulations = (
            db.query(Simulation)
            .filter(Simulation.user_id == user_id)
            .order_by(Simulation.created_at.desc())
            .all()
        )

        return templates.TemplateResponse(
            request=request,
            name="historique.html",
            context={
                "request": request,
                "username": request.session.get("username"),
                "simulations": simulations
            }
        )
    finally:
        db.close()

# =====================================
# 8. RAPPORTS ET STATISTIQUES
# =====================================

@app.get("/rapports", response_class=HTMLResponse)
async def rapports(request: Request):

    user_id = request.session.get("user_id")

    if not user_id:
        return RedirectResponse("/login", status_code=303)

    db = SessionLocal()

    try:
        # Récupérer les simulations de l'utilisateur
        simulations = (
            db.query(Simulation)
            .filter(Simulation.user_id == user_id)
            .order_by(Simulation.created_at.asc())
            .all()
        )

        # Nombre total de simulations
        total = len(simulations)

        # Calcul des moyennes
        if total > 0:
            debit_moyen = round(
                sum(s.debit_initial for s in simulations) / total, 2
            )

            debit_filtre_moyen = round(
                sum(s.debit_filtre for s in simulations) / total, 2
            )

            concentration_moyenne = round(
                sum(s.concentration_finale for s in simulations) / total, 2
            )

        else:
            debit_moyen = 0
            debit_filtre_moyen = 0
            concentration_moyenne = 0

        # Données du graphique
        labels = [
            s.created_at.strftime("%d/%m/%Y %H:%M")
            for s in simulations
        ]

        debits = [
            s.debit_filtre
            for s in simulations
        ]

        return templates.TemplateResponse(
            request=request,
            name="rapports.html",
            context={
                "request": request,
                "username": request.session.get("username"),
                "total": total,
                "debit_moyen": debit_moyen,
                "debit_filtre_moyen": debit_filtre_moyen,
                "concentration_moyenne": concentration_moyenne,
                "labels": labels,
                "debits": debits
            }
        )

    finally:
        db.close()

