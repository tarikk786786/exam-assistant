"""
Helper endpoint to complete login on the portal form
"""

from fastapi import HTTPException
from pydantic import BaseModel
import backend
from backend import app, engine

class LoginRequest(BaseModel):
    user_id: str
    password: str

@app.post("/api/browser/login")
def submit_login(req: LoginRequest):
    if not engine.page:
        raise HTTPException(status_code=400, detail="Browser is not running.")
    try:
        user_field = engine.page.query_selector("#txtUserId")
        if user_field:
            user_field.fill(req.user_id)
        
        pass_field = engine.page.query_selector("#txtPass")
        if pass_field:
            pass_field.fill(req.password)
            
        submit_btn = engine.page.query_selector("input[type='submit']")
        if submit_btn:
            submit_btn.click()
            engine.page.wait_for_load_state("domcontentloaded")
            
        return {
            "status": "submitted",
            "url": engine.page.url,
            "authenticated": engine.is_authenticated()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
