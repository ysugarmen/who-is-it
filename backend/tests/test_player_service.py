import pytest
from unittest.mock import MagicMock, patch

from app.services.player import create_player, get_player_stats

def test_create_player_valid_nickname():
    mock_supabase = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
        {"id": "uuid-1", "token": "token-1", "nickname": "test_user"}
    ]
    with patch("app.services.player.supabase", mock_supabase):
        result = create_player("test_user")
    assert result["nickname"] == "test_user"
    assert "token" in result

def test_create_player_duplicate_nickname():
    mock_supabase = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"id": "existing", "nickname": "taken"}
    ]
    with patch("app.services.player.supabase", mock_supabase):
        with pytest.raises(ValueError, match="already taken"):
            create_player("taken")
