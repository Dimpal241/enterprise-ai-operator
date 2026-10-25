import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent / "src" / "jira_to_code" / "tasks"

TASKS_DEF = {
    # EASY TASKS (3 new, making 5 total)
    "easy_3": {
        "file": "endpoints.py",
        "code": "def process_user_data(user_payload):\n    phone = user_payload['phone_number']\n    return {'status': 'success', 'phone': phone}\n",
        "test": "from endpoints import process_user_data\n\ndef test_process_user_data():\n    assert process_user_data({'phone_number': '123'}) == {'status': 'success', 'phone': '123'}\n    assert process_user_data({}) == {'status': 'success', 'phone': None}\n"
    },
    "easy_4": {
        "file": "pagination.py",
        "code": "def get_page_bounds(page, size):\n    start = (page - 1) * size\n    end = start + size - 1 # BUG: Off by one\n    return start, end\n",
        "test": "from pagination import get_page_bounds\n\ndef test_get_page_bounds():\n    assert get_page_bounds(1, 10) == (0, 10)\n    assert get_page_bounds(2, 10) == (10, 20)\n"
    },
    "easy_5": {
        "file": "routes.py",
        "code": "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/users/{user_id}')\ndef get_user(id: int):\n    return {'user_id': id}\n",
        "test": "from fastapi.testclient import TestClient\nfrom routes import app\n\ndef test_get_user():\n    client = TestClient(app)\n    response = client.get('/users/42')\n    assert response.status_code == 200\n    assert response.json() == {'user_id': 42}\n"
    },

    # MEDIUM TASKS
    "medium_3": {
        "file": "routes.py",
        "code": "from fastapi import FastAPI\nfrom auth import require_auth\napp = FastAPI()\n@app.get('/api/billing')\ndef get_billing():\n    return {'billing': 'data'}\n",
        "test": "from fastapi.testclient import TestClient\nfrom routes import app\n\ndef test_billing_protected():\n    client = TestClient(app)\n    response = client.get('/api/billing')\n    assert response.status_code == 401\n"
    },
    "medium_4": {
        "file": "orm.py",
        "code": "class User:\n    def __init__(self, id): self.id = id\nclass DB:\n    def get_users(self): return [User(i) for i in range(50)]\n    def get_profile(self, user): return {'profile': 'data'}\n\ndef fetch_user_profiles(db):\n    users = db.get_users()\n    return [db.get_profile(u) for u in users] # N+1 query simulate\n",
        "test": "from orm import fetch_user_profiles, DB\n\ndef test_fetch_with_join():\n    db = DB()\n    db.get_profile = lambda _: '#FAIL' # simulate strict join mode\n    profiles = fetch_user_profiles(db)\n    assert '#FAIL' not in profiles\n"
    },
    "medium_5": {
        "file": "validate.py",
        "code": "import re\ndef validate_email(email):\n    match = re.match(r'^[a-zA-Z0-9.]+@[a-zA-Z0-9]+\\.[a-zA-Z]+$', email)\n    return bool(match)\n",
        "test": "from validate import validate_email\n\ndef test_validate_email():\n    assert validate_email('user@gmail.com') == True\n    assert validate_email('user+test@gmail.com') == True\n"
    },
    "medium_6": {
        "file": "service.py",
        "code": "def fetch_rates(http_client):\n    return http_client.get('/rates')\n",
        "test": "from service import fetch_rates\nclass MockClient:\n    def get(self, url):\n        raise TimeoutError()\n\ndef test_fetch_rates_fallback():\n    assert fetch_rates(MockClient()) == {'USD': 1.0} # cached fallback\n"
    },
    "medium_7": {
        "file": "profile.py",
        "code": "def update_user_profile(db, redis, id, data):\n    db.update(id, data)\n",
        "test": "from profile import update_user_profile\nclass MockRedis:\n    def __init__(self): self.deleted = False\n    def delete(self, key): self.deleted = True\n\ndef test_cache_invalidation():\n    r = MockRedis()\n    update_user_profile(None, r, 1, {})\n    assert r.deleted == True\n"
    },
    "medium_8": {
        "file": "scheduling.py",
        "code": "from datetime import datetime\ndef schedule_event(year, month, day):\n    return datetime(year, month, day)\n",
        "test": "from scheduling import schedule_event\n\ndef test_timezone_aware():\n    dt = schedule_event(2023, 1, 1)\n    assert dt.tzinfo is not None\n"
    },
    "medium_9": {
        "file": "order.py",
        "code": "class Order:\n    def __init__(self):\n        self.state = 'PENDING'\n    def transition(self, state):\n        self.state = state\n",
        "test": "from order import Order\nimport pytest\n\ndef test_invalid_transition():\n    o = Order()\n    o.state = 'CANCELLED'\n    with pytest.raises(ValueError):\n        o.transition('SHIPPED')\n"
    },
    "medium_10": {
        "file": "config.py",
        "code": "def merge(d1, d2):\n    d1.update(d2)\n    return d1\n",
        "test": "from config import merge\n\ndef test_nested_merge():\n    d1 = {'app': {'host': 'localhost', 'port': 8080}}\n    d2 = {'app': {'port': 9000}}\n    res = merge(d1, d2)\n    assert res['app']['host'] == 'localhost'\n    assert res['app']['port'] == 9000\n"
    },

    # HARD TASKS
    "hard_3": {
        "file": "models.py",
        "code": "import utils\nclass Model: pass\n",
        "test": "from models import Model\ndef test_model():\n    assert Model() is not None\n"
    },
    "hard_4": {
        "file": "worker.py",
        "code": "class Worker:\n    def __init__(self): self.jobs = []\n    def add_job(self, j): self.jobs.append(j)\n    def run(self): return self.jobs.pop(0) if self.jobs else None\n",
        "test": "from worker import Worker\nimport queue\n\ndef test_uses_queue():\n    w = Worker()\n    assert hasattr(w, 'jobs') and isinstance(w.jobs, queue.Queue)\n"
    },
    "hard_5": {
        "file": "pipeline.py",
        "code": "def process_logs(file_obj):\n    lines = file_obj.readlines()\n    return [l.strip() for l in lines]\n",
        "test": "from pipeline import process_logs\nimport inspect\n\ndef test_generator():\n    class MockFile:\n        def readlines(self): raise MemoryError()\n        def __iter__(self): yield 'a\\n'; yield 'b\\n'\n    res = process_logs(MockFile())\n    assert inspect.isgenerator(res)\n    assert list(res) == ['a', 'b']\n"
    },
    "hard_6": {
        "file": "gateway.py",
        "code": "from abc import ABC, abstractmethod\nclass PaymentGateway(ABC):\n    @abstractmethod\n    def charge(self, amount):\n        pass\nclass StripeGateway:\n    pass\n",
        "test": "from gateway import StripeGateway, PaymentGateway\n\ndef test_stripe_gateway():\n    assert issubclass(StripeGateway, PaymentGateway)\n    s = StripeGateway()\n    assert s.charge(100) == 'Charged 100 via Stripe'\n"
    },
    "hard_7": {
        "file": "server.py",
        "code": "import asyncio\nimport threading\nlock = threading.Lock()\nasync def process():\n    lock.acquire()\n    raise TimeoutError()\n    lock.release()\n",
        "test": "from server import process, lock\nimport pytest\n\n@pytest.mark.asyncio\nasync def test_deadlock_fixed():\n    try:\n        await process()\n    except TimeoutError:\n        pass\n    assert lock.locked() == False\n"
    }
}

AUTH_CODE = "def require_auth(fn):\n    return fn\n"
UTILS_CODE = "import config\n"
CONFIG_CODE = "import models\n"

def main():
    for task_name, task_data in TASKS_DEF.items():
        task_dir = BASE_DIR / task_name
        task_dir.mkdir(parents=True, exist_ok=True)
        
        main_file = task_dir / task_data["file"]
        main_file.write_text(task_data["code"])
             
        test_file = task_dir / ("test_" + task_data["file"])
        test_file.write_text(task_data["test"])
        
        if task_name == "medium_3":
            (task_dir / "auth.py").write_text(AUTH_CODE)
        if task_name == "hard_3":
            (task_dir / "utils.py").write_text(UTILS_CODE)
            (task_dir / "config.py").write_text(CONFIG_CODE)
        
        req_txt = ""
        if task_name in ["easy_5", "medium_3"]:
            req_txt += "fastapi\\nhttpx\\npydantic\\n"
        if "asyncio" in task_data["test"]:
            req_txt += "pytest-asyncio\\n"
        if req_txt:
            (task_dir / "requirements.txt").write_text(req_txt)

    print("Success")

if __name__ == "__main__":
    main()
