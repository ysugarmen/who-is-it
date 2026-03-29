from unittest.mock import MagicMock, patch
from datetime import date
from app.services.leaderboard import get_leaderboard

def test_get_daily_leaderboard():
    mock_supabase = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = [
        {"player_id": "p1", "guesses_used": 2, "players": {"nickname": "ace"}},
        {"player_id": "p2", "guesses_used": 4, "players": {"nickname": "bob"}},
    ]
    with patch("app.services.leaderboard.supabase", mock_supabase):
        result = get_leaderboard("daily")
    assert len(result["entries"]) == 2
    assert result["entries"][0]["nickname"] == "ace"
