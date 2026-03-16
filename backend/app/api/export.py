from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.services.export_service import export_agences, export_insights, export_offres

router = APIRouter(prefix="/api/export", tags=["export"])


def _make_response(data, fmt: str, filename: str):
    if fmt == "excel":
        media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        return StreamingResponse(data, media_type=media, headers={"Content-Disposition": f"attachment; filename={filename}.xlsx"})
    else:
        media = "text/csv"
        return StreamingResponse(iter([data.getvalue()]), media_type=media, headers={"Content-Disposition": f"attachment; filename={filename}.csv"})


@router.get("/agences/{fmt}")
def export_agences_route(fmt: str, db: Session = Depends(get_db)):
    if fmt not in ("csv", "excel"):
        raise HTTPException(status_code=400, detail="Format must be 'csv' or 'excel'")
    data = export_agences(db, fmt)
    return _make_response(data, fmt, "agences")


@router.get("/offres/{fmt}")
def export_offres_route(fmt: str, db: Session = Depends(get_db)):
    if fmt not in ("csv", "excel"):
        raise HTTPException(status_code=400, detail="Format must be 'csv' or 'excel'")
    data = export_offres(db, fmt)
    return _make_response(data, fmt, "offres")


@router.get("/insights/{fmt}")
def export_insights_route(fmt: str, db: Session = Depends(get_db)):
    if fmt not in ("csv", "excel"):
        raise HTTPException(status_code=400, detail="Format must be 'csv' or 'excel'")
    data = export_insights(db, fmt)
    return _make_response(data, fmt, "insights")
