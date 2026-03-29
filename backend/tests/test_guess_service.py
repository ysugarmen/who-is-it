import pytest
from app.services.guess import is_correct_guess, calculate_points

def test_exact_match():
    assert is_correct_guess("Dwayne Johnson", "Dwayne Johnson", []) is True

def test_case_insensitive():
    assert is_correct_guess("dwayne johnson", "Dwayne Johnson", []) is True

def test_alias_match():
    assert is_correct_guess("The Rock", "Dwayne Johnson", ["The Rock"]) is True

def test_fuzzy_match():
    assert is_correct_guess("Dwayn Johnson", "Dwayne Johnson", []) is True

def test_wrong_guess():
    assert is_correct_guess("Brad Pitt", "Dwayne Johnson", ["The Rock"]) is False

def test_points_first_guess():
    assert calculate_points(1) == 7

def test_points_last_guess():
    assert calculate_points(7) == 1

def test_points_failed():
    assert calculate_points(0) == 0
