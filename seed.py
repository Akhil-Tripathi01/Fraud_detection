"""Idempotent demo data for local development."""

from datetime import datetime, timedelta

import models
from auth_utils import hash_password
from database import SessionLocal
from routes.utils import apply_fraud_analysis


def ensure_user(db, username, email, password, full_name, role):
    user = db.query(models.User).filter(models.User.username == username).first()
    if user:
        return user
    user = models.User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        role=role,
    )
    db.add(user)
    db.flush()
    return user


def seed_database():
    db = SessionLocal()
    try:
        admin = ensure_user(db, "admin", "admin@fraud.local", "admin123", "Platform Admin", "admin")
        investigator = ensure_user(
            db,
            "investigator",
            "investigator@fraud.local",
            "password123",
            "Asha Rao",
            "investigator",
        )
        db.commit()

        if db.query(models.Customer).count() > 0:
            for transaction in db.query(models.Transaction).order_by(models.Transaction.timestamp.asc()).all():
                apply_fraud_analysis(transaction, db)
            db.commit()
            return

        customers = [
            models.Customer(id="cust-001", name="Aarav Mehta", email="aarav@example.com", phone="+91 90000 00001", account_number="1002003001", city="Mumbai", balance=245000),
            models.Customer(id="cust-002", name="Isha Nair", email="isha@example.com", phone="+91 90000 00002", account_number="1002003002", city="Bengaluru", balance=189000),
            models.Customer(id="cust-003", name="Kabir Khan", email="kabir@example.com", phone="+91 90000 00003", account_number="1002003003", city="Delhi", balance=56000),
            models.Customer(id="cust-004", name="Mira Shah", email="mira@example.com", phone="+91 90000 00004", account_number="1002003004", city="Pune", balance=94000),
            models.Customer(id="cust-005", name="Rohan Das", email="rohan@example.com", phone="+91 90000 00005", account_number="1002003005", city="Kolkata", balance=132000),
            models.Customer(id="cust-006", name="Tara Singh", email="tara@example.com", phone="+91 90000 00006", account_number="1002003006", city="Jaipur", balance=77000),
            models.Customer(id="cust-007", name="Neel Verma", email="neel@example.com", phone="+91 90000 00007", account_number="1002003007", city="Hyderabad", balance=218000, is_flagged=True, risk_score=72),
            models.Customer(id="cust-008", name="Zoya Ali", email="zoya@example.com", phone="+91 90000 00008", account_number="1002003008", city="Chennai", balance=64000),
        ]
        merchants = [
            models.Merchant(id="mer-001", name="Metro Grocery", category="retail", location="Mumbai", total_transactions=0),
            models.Merchant(id="mer-002", name="Orbit Travel", category="travel", location="Delhi", total_transactions=0),
            models.Merchant(id="mer-003", name="QuickKart", category="ecommerce", location="Bengaluru", total_transactions=0),
            models.Merchant(id="mer-004", name="CoinBridge OTC", category="crypto", location="Dubai", is_flagged=True, risk_level="high", total_transactions=0),
            models.Merchant(id="mer-005", name="NightPay Services", category="wallet", location="Kolkata", is_flagged=True, risk_level="medium", total_transactions=0),
        ]
        devices = [
            models.Device(id="dev-001", device_hash="a1b2c3d4e5f60718293a4b5c6d7e8f90", device_type="mobile", os="Android", browser="Chrome", ip_address="103.21.244.12"),
            models.Device(id="dev-002", device_hash="b2c3d4e5f60718293a4b5c6d7e8f90a1", device_type="desktop", os="Windows", browser="Edge", ip_address="49.36.50.10"),
            models.Device(id="dev-003", device_hash="c3d4e5f60718293a4b5c6d7e8f90a1b2", device_type="mobile", os="iOS", browser="Safari", ip_address="2405:201:abcd::1"),
            models.Device(id="dev-004", device_hash="d4e5f60718293a4b5c6d7e8f90a1b2c3", device_type="atm", os="Embedded", browser="N/A", ip_address="10.40.1.8", is_flagged=True),
            models.Device(id="dev-005", device_hash="e5f60718293a4b5c6d7e8f90a1b2c3d4", device_type="mobile", os="Android", browser="Firefox", ip_address="185.199.108.10", is_flagged=True),
        ]
        db.add_all(customers + merchants + devices)
        db.commit()

        now = datetime.utcnow()
        specs = [
            ("cust-001", "cust-002", None, "dev-001", 3200, "Mumbai", 19.076, 72.8777, models.TransactionType.transfer, now - timedelta(days=8)),
            ("cust-002", None, "mer-001", "dev-002", 1450, "Bengaluru", 12.9716, 77.5946, models.TransactionType.purchase, now - timedelta(days=7)),
            ("cust-003", None, "mer-003", "dev-003", 6800, "Delhi", 28.6139, 77.209, models.TransactionType.payment, now - timedelta(days=6)),
            ("cust-004", "cust-005", None, "dev-001", 12000, "Pune", 18.5204, 73.8567, models.TransactionType.transfer, now - timedelta(days=5)),
            ("cust-005", None, "mer-002", "dev-002", 24500, "Kolkata", 22.5726, 88.3639, models.TransactionType.purchase, now - timedelta(days=4)),
            ("cust-007", None, "mer-004", "dev-005", 225000, "Dubai", 25.2048, 55.2708, models.TransactionType.transfer, now - timedelta(days=3)),
            ("cust-007", "cust-008", None, "dev-005", 88000, "Chennai", 13.0827, 80.2707, models.TransactionType.transfer, now - timedelta(days=2, hours=4)),
            ("cust-008", None, "mer-005", "dev-004", 74000, "Kolkata", 22.5726, 88.3639, models.TransactionType.payment, now - timedelta(days=2, hours=2)),
            ("cust-001", "cust-006", None, "dev-001", 9100, "Mumbai", 19.076, 72.8777, models.TransactionType.transfer, now - timedelta(days=1, hours=6)),
            ("cust-002", None, "mer-003", "dev-002", 4900, "Bengaluru", 12.9716, 77.5946, models.TransactionType.purchase, now - timedelta(days=1, hours=3)),
            ("cust-003", "cust-008", None, "dev-005", 14500, "Delhi", 28.6139, 77.209, models.TransactionType.transfer, now - timedelta(hours=7)),
            ("cust-004", "cust-008", None, "dev-005", 15500, "Pune", 18.5204, 73.8567, models.TransactionType.transfer, now - timedelta(hours=6)),
            ("cust-005", "cust-008", None, "dev-005", 16500, "Kolkata", 22.5726, 88.3639, models.TransactionType.transfer, now - timedelta(hours=5)),
            ("cust-006", "cust-008", None, "dev-005", 17500, "Jaipur", 26.9124, 75.7873, models.TransactionType.transfer, now - timedelta(hours=4)),
            ("cust-001", None, "mer-005", "dev-001", 18000, "Mumbai", 19.076, 72.8777, models.TransactionType.payment, now - timedelta(minutes=52)),
            ("cust-001", None, "mer-005", "dev-001", 19000, "Mumbai", 19.076, 72.8777, models.TransactionType.payment, now - timedelta(minutes=43)),
            ("cust-001", None, "mer-005", "dev-001", 21000, "Mumbai", 19.076, 72.8777, models.TransactionType.payment, now - timedelta(minutes=35)),
            ("cust-001", None, "mer-005", "dev-001", 23000, "Mumbai", 19.076, 72.8777, models.TransactionType.payment, now - timedelta(minutes=27)),
            ("cust-001", None, "mer-005", "dev-001", 26000, "Mumbai", 19.076, 72.8777, models.TransactionType.payment, now - timedelta(minutes=19)),
            ("cust-001", None, "mer-005", "dev-001", 31000, "Mumbai", 19.076, 72.8777, models.TransactionType.payment, now - timedelta(minutes=11)),
        ]

        alerts = []
        for index, spec in enumerate(specs, start=1):
            sender_id, receiver_id, merchant_id, device_id, amount, location, lat, lng, transaction_type, timestamp = spec
            transaction = models.Transaction(
                transaction_id=f"txn-{index:04d}",
                sender_id=sender_id,
                receiver_id=receiver_id,
                merchant_id=merchant_id,
                device_id=device_id,
                amount=amount,
                currency="INR",
                location=location,
                latitude=lat,
                longitude=lng,
                transaction_type=transaction_type,
                status=models.TransactionStatus.pending,
                timestamp=timestamp,
            )
            db.add(transaction)
            db.flush()
            _, alert = apply_fraud_analysis(transaction, db)
            if alert:
                alerts.append(alert)

        db.commit()

        for alert in alerts[:2]:
            db.add(
                models.InvestigationNote(
                    alert_id=alert.id,
                    investigator_id=investigator.id,
                    note_text="Initial review opened from seeded monitoring queue.",
                    action_taken="queued_for_review",
                )
            )
            alert.status = models.AlertStatus.investigating
        db.commit()

    finally:
        db.close()
