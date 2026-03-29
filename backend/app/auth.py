from fastapi import Header, HTTPException, Depends
from typing import Optional
from app.db import supabase

async def get_player_optional(authorization: Optional[str] = Header(None)):
    """Returns player dict or None if no token provided."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ").strip()
    result = supabase.table("players").select("*").eq("token", token).execute()
    if not result.data:
        return None
    return result.data[0]

async def get_player_required(authorization: str = Header(...)):
    """Returns player dict or raises 401."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    result = supabase.table("players").select("*").eq("token", token).execute()
    if not result.data:
        raise HTTPException(status_code=401, detail="Invalid token")
    return result.data[0]
