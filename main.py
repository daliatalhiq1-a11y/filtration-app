
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Application de Filtration")

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def accueil(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request}
    )


@app.post("/calculer", response_class=HTMLResponse)
async def calculer(
    request: Request,
    m0: float = Form(...),
    x0: float = Form(...),
    residus: float = Form(...)
):

    if m0 <= 0 or residus < 0 or residus >= m0:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "request": request,
                "erreur": "Vérifiez les données saisies."
            }
        )

    if x0 < 0 or x0 > 100:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "request": request,
                "erreur": "La concentration doit être entre 0 et 100 %."
            }
        )

    # Calcul de filtration
    m1 = m0 - residus
    x1 = (m0 * (x0 / 100)) / m1

    # Vérification du bilan
    bilan = m0 - (m1 + residus)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request,
            "m1": round(m1, 2),
            "x1": round(x1 * 100, 2),
            "bilan": round(bilan, 6)
        }
    )
