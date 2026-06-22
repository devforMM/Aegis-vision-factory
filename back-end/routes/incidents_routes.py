from fastapi import APIRouter, Depends, HTTPException
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from server.server_utils import get_current_admin

templates = Jinja2Templates(directory="../front-end")
incidents_router = APIRouter()


@incidents_router.get("/all", response_class=HTMLResponse)
def get_incidents(request: Request, user=Depends(get_current_admin)):
    """
    Fetches and displays the complete list of incidents.
    """
    try:
        incidents_list = user.incidents
        return templates.TemplateResponse(
            request=request,
            name="AllIncidents_template.html",
            context={"incidents": incidents_list}
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Error: {e}")


@incidents_router.get("/incident_informations/{incident_id}", response_class=HTMLResponse)
def incident_informations(incident_id: int, request: Request, user=Depends(get_current_admin)):
    """
    Retrieves and displays detailed tracking parameters for a specific incident ID.
    """
    target_incident = None
    
    for single_incident in user.incidents:
        if single_incident.id == incident_id:
            target_incident = single_incident

    if not target_incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    return templates.TemplateResponse(
        request=request,
        name="IncidnetDetails_template.html",
        context={"incident": target_incident}
    )