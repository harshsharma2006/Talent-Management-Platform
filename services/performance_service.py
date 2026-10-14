import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "talentsphere_healthy.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_reviews():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS performance_reviews (
                review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                achievements TEXT NOT NULL,
                improvement_areas TEXT NOT NULL,
                reviewer TEXT NOT NULL,
                review_date TEXT NOT NULL
            )
        """)


def add_review(employee_id, rating, achievements, improvement_areas, reviewer):
    employee_id = str(employee_id).strip()
    achievements = str(achievements).strip()
    improvement_areas = str(improvement_areas).strip()
    reviewer = str(reviewer).strip()

    if not employee_id or not reviewer or not achievements:
        return False, "Employee ID, reviewer and achievements are required."

    try:
        rating = int(rating)
    except (TypeError, ValueError):
        return False, "Rating must be a whole number from 1 to 5."

    if rating < 1 or rating > 5:
        return False, "Rating must be between 1 and 5."

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO performance_reviews
            (employee_id, rating, achievements, improvement_areas, reviewer, review_date)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                employee_id,
                rating,
                achievements,
                improvement_areas,
                reviewer,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )

    return True, "Performance review saved successfully."


def list_reviews(employee_id=None):
    with get_connection() as connection:
        if employee_id:
            rows = connection.execute(
                """
                SELECT * FROM performance_reviews
                WHERE employee_id = ?
                ORDER BY review_date DESC
                """,
                (str(employee_id).strip(),)
            ).fetchall()
        else:
            rows = connection.execute(
                "SELECT * FROM performance_reviews ORDER BY review_date DESC"
            ).fetchall()

    return [dict(row) for row in rows]


def employee_average_rating(employee_id):
    with get_connection() as connection:
        result = connection.execute(
            """
            SELECT ROUND(AVG(rating), 2) AS average_rating,
                   COUNT(*) AS review_count
            FROM performance_reviews
            WHERE employee_id = ?
            """,
            (str(employee_id).strip(),)
        ).fetchone()

    return {
        "average_rating": result["average_rating"],
        "review_count": result["review_count"]
    }
