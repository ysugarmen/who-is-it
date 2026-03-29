import os

# Set dummy env vars before any app imports so pydantic-settings doesn't fail
os.environ.setdefault("SUPABASE_URL", "https://dummy.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "dummy-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "dummy-service-key")
