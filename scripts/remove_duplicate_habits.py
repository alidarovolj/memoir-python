"""Remove duplicate habits (task_groups) for a user by email.
Keeps one group per name (oldest by created_at), deletes the rest and their tasks.
Usage: python scripts/remove_duplicate_habits.py
"""
import sys
from pathlib import Path
from collections import defaultdict

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text, bindparam
from sqlalchemy.pool import NullPool
from app.core.config import settings

TARGET_EMAIL = "alidarovolzhas@gmail.com"


def remove_duplicate_habits():
    engine = create_engine(
        settings.DATABASE_URL_SYNC,
        poolclass=NullPool,
        echo=False,
    )

    with engine.begin() as conn:
        # 1. Get user id by email
        user_row = conn.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": TARGET_EMAIL},
        ).fetchone()
        if not user_row:
            print(f"User with email {TARGET_EMAIL} not found.")
            return
        user_id = str(user_row[0])
        print(f"User id: {user_id}")

        # 2. Get all task_groups for this user
        groups = conn.execute(
            text("""
                SELECT id, name, created_at
                FROM task_groups
                WHERE user_id = :user_id
                ORDER BY name, created_at
            """),
            {"user_id": user_id},
        ).fetchall()

        if not groups:
            print("No habits (task_groups) found for this user.")
            return

        # 3. Find duplicates by name (keep first by created_at)
        by_name = defaultdict(list)
        for gid, name, created_at in groups:
            by_name[name].append((str(gid), name, created_at))

        to_delete_ids = []
        for name, items in by_name.items():
            if len(items) > 1:
                # Keep first (oldest), delete the rest
                for gid, _, _ in items[1:]:
                    to_delete_ids.append(gid)
                print(f"  Duplicates for '{name}': keeping 1, removing {len(items) - 1}")

        if not to_delete_ids:
            print("No duplicate habits found.")
            return

        print(f"Removing {len(to_delete_ids)} duplicate group(s) and their tasks...")

        # 4. Delete tasks that belong to these groups, then delete the task_groups
        delete_tasks = text(
            "DELETE FROM tasks WHERE task_group_id IN :ids"
        ).bindparams(bindparam("ids", expanding=True))
        delete_groups = text(
            "DELETE FROM task_groups WHERE id IN :ids"
        ).bindparams(bindparam("ids", expanding=True))
        conn.execute(delete_tasks, {"ids": to_delete_ids})
        conn.execute(delete_groups, {"ids": to_delete_ids})
        print("Done. Duplicate habits and their tasks have been removed.")


if __name__ == "__main__":
    remove_duplicate_habits()
