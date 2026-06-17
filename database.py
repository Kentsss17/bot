import aiosqlite
from config import DB_PATH
from datetime import datetime


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS workers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                full_name TEXT NOT NULL,
                phone TEXT,
                age INTEGER,
                specialization TEXT,
                status TEXT DEFAULT 'pending',
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_type TEXT NOT NULL,
                job_sub TEXT,
                car_brand TEXT,
                car_model TEXT,
                vin_code TEXT NOT NULL,
                note TEXT,
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS job_workers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                worker_id INTEGER NOT NULL,
                status TEXT DEFAULT 'Yangi',
                reject_reason TEXT,
                updated_at TEXT,
                FOREIGN KEY (job_id) REFERENCES jobs(id),
                FOREIGN KEY (worker_id) REFERENCES workers(id)
            )
        """)
        await db.commit()


# ── WORKERS ──────────────────────────────────────────

async def add_worker(telegram_id, full_name, phone, age=None, specialization=None, status='pending'):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO workers (telegram_id, full_name, phone, age, specialization, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (telegram_id, full_name, phone, age, specialization, status))
        await db.commit()


async def get_worker_by_tg(telegram_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM workers WHERE telegram_id=?", (telegram_id,)) as cur:
            return await cur.fetchone()


async def get_worker_by_id(worker_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM workers WHERE id=?", (worker_id,)) as cur:
            return await cur.fetchone()


async def get_all_workers(only_active=True):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        q = "SELECT * FROM workers WHERE is_active=1" if only_active else "SELECT * FROM workers"
        async with db.execute(q) as cur:
            return await cur.fetchall()


async def get_approved_workers():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM workers WHERE status='approved' AND is_active=1") as cur:
            return await cur.fetchall()


async def get_pending_workers():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM workers WHERE status='pending'") as cur:
            return await cur.fetchall()


async def update_worker_status(worker_id, status):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE workers SET status=? WHERE id=?", (status, worker_id))
        await db.commit()


async def update_worker_field(worker_id, field, value):
    allowed = ['full_name', 'phone', 'age', 'specialization', 'telegram_id']
    if field not in allowed:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE workers SET {field}=? WHERE id=?", (value, worker_id))
        await db.commit()


async def deactivate_worker(worker_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE workers SET is_active=0 WHERE id=?", (worker_id,))
        await db.commit()


async def count_done_jobs_for_worker(worker_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM job_workers WHERE worker_id=? AND status='Bajarildi'", (worker_id,)
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else 0


async def count_active_jobs_for_worker(worker_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM job_workers WHERE worker_id=? AND status='Yangi'", (worker_id,)
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else 0


# ── JOBS ─────────────────────────────────────────────

async def create_job(job_type, job_sub, car_brand, car_model, vin_code, note, created_by):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
            INSERT INTO jobs (job_type, job_sub, car_brand, car_model, vin_code, note, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (job_type, job_sub, car_brand, car_model, vin_code, note, created_by))
        await db.commit()
        return cur.lastrowid


async def assign_workers_to_job(job_id, worker_ids):
    async with aiosqlite.connect(DB_PATH) as db:
        for wid in worker_ids:
            await db.execute(
                "INSERT INTO job_workers (job_id, worker_id) VALUES (?, ?)", (job_id, wid)
            )
        await db.commit()


async def get_job_by_id(job_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)) as cur:
            return await cur.fetchone()


async def get_jobs_for_worker(worker_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT j.*, jw.id as jw_id, jw.status as jw_status
            FROM jobs j
            JOIN job_workers jw ON j.id = jw.job_id
            WHERE jw.worker_id=? AND jw.status='Yangi'
            ORDER BY j.created_at DESC
        """, (worker_id,)) as cur:
            return await cur.fetchall()


async def get_jw_by_id(jw_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM job_workers WHERE id=?", (jw_id,)) as cur:
            return await cur.fetchone()


async def update_jw_status(jw_id, status, reject_reason=None):
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE job_workers SET status=?, reject_reason=?, updated_at=? WHERE id=?",
            (status, reject_reason, now, jw_id)
        )
        await db.commit()


# ── STATISTICS ───────────────────────────────────────

async def get_statistics():
    async with aiosqlite.connect(DB_PATH) as db:
        today = datetime.now().strftime("%Y-%m-%d")
        month = datetime.now().strftime("%Y-%m")

        async with db.execute(
            "SELECT COUNT(*) FROM jobs WHERE DATE(created_at)=?", (today,)
        ) as cur:
            today_created = (await cur.fetchone())[0]

        async with db.execute(
            "SELECT COUNT(*) FROM job_workers WHERE status='Bajarildi' AND DATE(updated_at)=?",
            (today,)
        ) as cur:
            today_done = (await cur.fetchone())[0]

        async with db.execute(
            "SELECT COUNT(*) FROM job_workers WHERE status='Bajarildi' AND updated_at LIKE ?",
            (f"{month}%",)
        ) as cur:
            month_done = (await cur.fetchone())[0]

        async with db.execute(
            "SELECT COUNT(*) FROM job_workers WHERE status='Bajarildi'"
        ) as cur:
            total_done = (await cur.fetchone())[0]

        async with db.execute(
            "SELECT COUNT(*) FROM job_workers WHERE status='Yangi'"
        ) as cur:
            active_jobs = (await cur.fetchone())[0]

        async with db.execute(
            "SELECT COUNT(*) FROM workers WHERE status='pending'"
        ) as cur:
            pending_count = (await cur.fetchone())[0]

        # Top-5 ishchilar
        async with db.execute("""
            SELECT w.full_name, w.specialization,
                   SUM(CASE WHEN jw.status='Bajarildi' THEN 1 ELSE 0 END) as done,
                   SUM(CASE WHEN jw.status='Yangi' THEN 1 ELSE 0 END) as active
            FROM workers w
            LEFT JOIN job_workers jw ON w.id = jw.worker_id
            WHERE w.is_active=1 AND w.status='approved'
            GROUP BY w.id
            ORDER BY done DESC
            LIMIT 5
        """) as cur:
            top5 = await cur.fetchall()

        return {
            "today_created": today_created,
            "today_done": today_done,
            "month_done": month_done,
            "total_done": total_done,
            "active_jobs": active_jobs,
            "pending_count": pending_count,
            "top5": top5,
        }
