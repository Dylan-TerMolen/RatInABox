"""Cell-response explorer: drag a rat around a place field and see, live, how
each model's tEBC cell types would fire at that position. Pure client-side
demo -- the route only renders the template, all the place-field/response-curve
math is ported to JS in static/js/explorer.js (see that file's header for which
Python source each function mirrors)."""
from __future__ import annotations

from fastapi import APIRouter, Request

from .. import view

router = APIRouter(prefix="/explorer", tags=["explorer"])


@router.get("")
def explorer(request: Request):
    return view.templates.TemplateResponse("explorer.html", {"request": request})
