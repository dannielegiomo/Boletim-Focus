"""Testes para src/downloader.py."""

import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.downloader import find_focus_date, last_monday


def test_last_monday_on_monday():
    monday = datetime.date(2024, 1, 8)  # segunda-feira
    assert last_monday(monday) == monday


def test_last_monday_on_wednesday():
    wednesday = datetime.date(2024, 1, 10)
    assert last_monday(wednesday) == datetime.date(2024, 1, 8)


def test_last_monday_on_sunday():
    sunday = datetime.date(2024, 1, 14)
    assert last_monday(sunday) == datetime.date(2024, 1, 8)


def test_find_focus_date_success_on_first_try():
    start = datetime.date(2024, 1, 8)
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b"%PDF-fake"

    with patch("src.downloader.requests.get", return_value=mock_resp) as mock_get:
        pub_date, content = find_focus_date(start)

    assert pub_date == start
    assert content == b"%PDF-fake"
    assert mock_get.call_count == 1


def test_find_focus_date_fallback_on_holiday():
    """Simula segunda com 404 (feriado) e terça com 200."""
    start = datetime.date(2024, 1, 8)
    fail = MagicMock(status_code=404)
    success = MagicMock(status_code=200, content=b"%PDF-terca")

    with patch("src.downloader.requests.get", side_effect=[fail, success]):
        pub_date, content = find_focus_date(start)

    assert pub_date == datetime.date(2024, 1, 7)
    assert content == b"%PDF-terca"


def test_find_focus_date_raises_after_max_retries():
    fail = MagicMock(status_code=404)

    with patch("src.downloader.requests.get", return_value=fail):
        with pytest.raises(RuntimeError, match="não encontrado"):
            find_focus_date(datetime.date(2024, 1, 8))
