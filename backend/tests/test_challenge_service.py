from unittest.mock import MagicMock, patch
from datetime import date
from app.services.challenge import get_todays_challenge

def test_get_todays_challenge():
    mock_supabase = MagicMock()
    today = date.today()
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {
            "date": str(today),
            "person_id": "person-1",
            "people": {
                "name": "Dwayne Johnson",
                "image_url": "https://storage.example.com/dwayne.jpg",
                "category": "actor",
                "aliases": ["The Rock"],
            },
        }
    ]
    with patch("app.services.challenge.supabase", mock_supabase):
        result = get_todays_challenge()
    assert result["image_url"] == "https://storage.example.com/dwayne.jpg"
    assert result["category"] == "actor"

def test_get_todays_challenge_no_challenge():
    mock_supabase = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    with patch("app.services.challenge.supabase", mock_supabase):
        result = get_todays_challenge()
    assert result is None
