import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from datetime import datetime, timedelta, timezone
from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.appointment import Appointment
from app.models.appointment_event import AppointmentEvent
from app.models.audit_log import AuditLog
from app.models.carrier import Carrier
from app.models.carrier_user import CarrierUser
from app.models.dock import Dock
from app.models.dock_capability import DockCapability
from app.models.dock_unavailability import DockUnavailability
from app.models.user import User
from app.models.warehouse import Warehouse
from app.models.warehouse_user import WarehouseUser


def seed():
    db = SessionLocal()
    print("=== Seeding Dock Appointment Scheduling Demo Data ===")

    try:
        # 1. Users
        users_data = [
            {
                "email": "admin@dockflow.local",
                "full_name": "System Administrator",
                "role": "ADMIN",
                "password": "AdminPass123!",
            },
            {
                "email": "manager.budapest@dockflow.local",
                "full_name": "Eva Kovacs (Manager)",
                "role": "WAREHOUSE_MANAGER",
                "password": "ManagerPass123!",
            },
            {
                "email": "staff.budapest@dockflow.local",
                "full_name": "Tamas Nagy (Staff)",
                "role": "WAREHOUSE_STAFF",
                "password": "StaffPass123!",
            },
            {
                "email": "dispatcher@translog.com",
                "full_name": "David Molnar (TransLog)",
                "role": "CARRIER",
                "password": "CarrierPass123!",
            },
            {
                "email": "operations@speedyfreight.eu",
                "full_name": "Anna Varga (SpeedyFreight)",
                "role": "CARRIER",
                "password": "CarrierPass123!",
            },
            {
                "email": "logistics@danubecargo.com",
                "full_name": "Gabor Toth (Danube Cargo)",
                "role": "CARRIER",
                "password": "CarrierPass123!",
            },
        ]

        users = {}
        for u in users_data:
            existing = db.scalar(select(User).where(User.email == u["email"]))
            if not existing:
                user = User(
                    email=u["email"],
                    hashed_password=hash_password(u["password"]),
                    full_name=u["full_name"],
                    role=u["role"],
                    is_active=True,
                )
                db.add(user)
                db.flush()
                users[u["email"]] = user
                print(f"Created user: {u['email']} [{u['role']}]")
            else:
                users[u["email"]] = existing
                print(f"User already exists: {u['email']}")

        # 2. Warehouses
        warehouses_data = [
            {
                "name": "Central Logistics Hub Budapest",
                "code": "WH-BUD-01",
                "address": "Logisztikai park út 4.",
                "city": "Budapest",
                "postal_code": "1239",
                "country": "Hungary",
                "timezone": "Europe/Budapest",
            },
            {
                "name": "Gyor Regional Distribution Center",
                "code": "WH-GYOR-02",
                "address": "Ipari Park sor 12.",
                "city": "Gyor",
                "postal_code": "9027",
                "country": "Hungary",
                "timezone": "Europe/Budapest",
            },
        ]

        warehouses = {}
        for w in warehouses_data:
            existing = db.scalar(select(Warehouse).where(Warehouse.code == w["code"]))
            if not existing:
                wh = Warehouse(**w, is_active=True)
                db.add(wh)
                db.flush()
                warehouses[w["code"]] = wh
                print(f"Created warehouse: {w['name']} ({w['code']})")
            else:
                warehouses[w["code"]] = existing
                print(f"Warehouse already exists: {w['code']}")

        # 3. Associate Warehouse Users
        mgr = users["manager.budapest@dockflow.local"]
        stf = users["staff.budapest@dockflow.local"]
        for wh in warehouses.values():
            for u in (mgr, stf):
                has_rel = db.scalar(
                    select(WarehouseUser).where(
                        WarehouseUser.user_id == u.id,
                        WarehouseUser.warehouse_id == wh.id,
                    )
                )
                if not has_rel:
                    db.add(WarehouseUser(user_id=u.id, warehouse_id=wh.id))

        db.flush()

        # 4. Docks & Capabilities
        docks_data = [
            # Budapest Hub
            {
                "wh": "WH-BUD-01",
                "dock_code": "BUD-DK-01",
                "name": "Inbound Heavy Ramp #1",
                "description": "Equipped with heavy-duty dock leveller for 40t semi-trailers.",
                "max_vehicle_length": 18.5,
                "max_vehicle_weight": 40000.0,
                "caps": [("RAMP_TYPE", "HYDRAULIC"), ("HANDLING", "FORKLIFT"), ("TEMPERATURE", "AMBIENT")],
            },
            {
                "wh": "WH-BUD-01",
                "dock_code": "BUD-DK-02",
                "name": "Cold Storage Bay #2",
                "description": "Direct insulated seal connection for refrigerated/frozen cargo.",
                "max_vehicle_length": 16.5,
                "max_vehicle_weight": 35000.0,
                "caps": [("TEMPERATURE", "COLD_CHAIN"), ("TEMPERATURE", "FROZEN"), ("HANDLING", "FORKLIFT")],
            },
            {
                "wh": "WH-BUD-01",
                "dock_code": "BUD-DK-03",
                "name": "Express Sprinter Ramp #3",
                "description": "Dedicated ground-level dock for light delivery vans & express couriers.",
                "max_vehicle_length": 8.0,
                "max_vehicle_weight": 7500.0,
                "caps": [("RAMP_TYPE", "LEVEL"), ("HANDLING", "PALLET_JACK")],
            },
            {
                "wh": "WH-BUD-01",
                "dock_code": "BUD-DK-04",
                "name": "Outbound Crossdock Ramp #4",
                "description": "High-throughput rapid dispatch bay with dual roller beds.",
                "max_vehicle_length": 18.5,
                "max_vehicle_weight": 40000.0,
                "caps": [("RAMP_TYPE", "HYDRAULIC"), ("HANDLING", "FORKLIFT")],
            },
            # Gyor Hub
            {
                "wh": "WH-GYOR-02",
                "dock_code": "GYR-DK-01",
                "name": "General Inbound Bay #1",
                "description": "Standard automotive component inbound receiving dock.",
                "max_vehicle_length": 18.0,
                "max_vehicle_weight": 38000.0,
                "caps": [("RAMP_TYPE", "HYDRAULIC"), ("HANDLING", "FORKLIFT")],
            },
            {
                "wh": "WH-GYOR-02",
                "dock_code": "GYR-DK-02",
                "name": "Hazmat & Chemical Ramp #2",
                "description": "Spill containment drainage system certified for ADR hazard classes.",
                "max_vehicle_length": 16.5,
                "max_vehicle_weight": 32000.0,
                "caps": [("SAFETY", "HAZMAT_ADR"), ("SAFETY", "SPILL_CONTAINMENT")],
            },
        ]

        docks = {}
        for d in docks_data:
            wh = warehouses[d["wh"]]
            existing = db.scalar(
                select(Dock).where(
                    Dock.warehouse_id == wh.id,
                    Dock.dock_code == d["dock_code"],
                )
            )
            if not existing:
                dock = Dock(
                    warehouse_id=wh.id,
                    dock_code=d["dock_code"],
                    name=d["name"],
                    description=d["description"],
                    max_vehicle_length=d["max_vehicle_length"],
                    max_vehicle_weight=d["max_vehicle_weight"],
                    is_active=True,
                )
                db.add(dock)
                db.flush()
                docks[d["dock_code"]] = dock
                print(f"Created dock: {d['dock_code']} at {d['wh']}")

                # Add capabilities
                for ctype, cval in d["caps"]:
                    cap = DockCapability(
                        dock_id=dock.id,
                        capability_type=ctype,
                        capability_value=cval,
                        description=f"{ctype} {cval}",
                        is_active=True,
                    )
                    db.add(cap)
            else:
                docks[d["dock_code"]] = existing

        db.flush()

        # 5. Carriers
        carriers_data = [
            {
                "company_name": "TransLogistics International Kft.",
                "registration_number": "HU-TL-902148",
                "contact_email": "dispatcher@translog.com",
                "contact_phone": "+36 1 450 8820",
                "address": "Nagykőrösi út 349.",
                "country": "Hungary",
                "user_email": "dispatcher@translog.com",
            },
            {
                "company_name": "SpeedyFreight Europe Sp. z o.o.",
                "registration_number": "PL-SF-441290",
                "contact_email": "operations@speedyfreight.eu",
                "contact_phone": "+48 22 590 1200",
                "address": "Al. Jerozolimskie 180",
                "country": "Poland",
                "user_email": "operations@speedyfreight.eu",
            },
            {
                "company_name": "Danube Cargo Express GmbH",
                "registration_number": "AT-DC-883100",
                "contact_email": "logistics@danubecargo.com",
                "contact_phone": "+43 1 700 7350",
                "address": "Handelskai 94",
                "country": "Austria",
                "user_email": "logistics@danubecargo.com",
            },
        ]

        carriers = {}
        for c in carriers_data:
            existing = db.scalar(
                select(Carrier).where(Carrier.registration_number == c["registration_number"])
            )
            u_email = c.pop("user_email")
            if not existing:
                carrier = Carrier(**c, is_active=True)
                db.add(carrier)
                db.flush()
                carriers[carrier.registration_number] = carrier
                print(f"Created carrier: {carrier.company_name}")

                # Associate user
                cu = CarrierUser(user_id=users[u_email].id, carrier_id=carrier.id)
                db.add(cu)
            else:
                carriers[existing.registration_number] = existing
                has_cu = db.scalar(
                    select(CarrierUser).where(
                        CarrierUser.user_id == users[u_email].id,
                        CarrierUser.carrier_id == existing.id,
                    )
                )
                if not has_cu:
                    db.add(CarrierUser(user_id=users[u_email].id, carrier_id=existing.id))

        db.flush()

        # 6. Dock Unavailability (Maintenance)
        now = datetime.now(timezone.utc)
        maint_start = now.replace(minute=0, second=0, microsecond=0) + timedelta(days=2, hours=2)
        maint_end = maint_start + timedelta(hours=4)

        bud_dock3 = docks.get("BUD-DK-03")
        if bud_dock3:
            existing_maint = db.scalar(
                select(DockUnavailability).where(DockUnavailability.dock_id == bud_dock3.id)
            )
            if not existing_maint:
                maint = DockUnavailability(
                    dock_id=bud_dock3.id,
                    reason_type="MAINTENANCE",
                    description="Scheduled hydraulic ramp pressure seal calibration and safety test.",
                    start_time=maint_start,
                    end_time=maint_end,
                    reported_by=mgr.id,
                )
                db.add(maint)
                print(f"Registered maintenance for {bud_dock3.dock_code}")

        # 7. Sample Appointments
        tl_carrier = carriers["HU-TL-902148"]
        sf_carrier = carriers["PL-SF-441290"]
        dc_carrier = carriers["AT-DC-883100"]
        bud_wh = warehouses["WH-BUD-01"]
        gyor_wh = warehouses["WH-GYOR-02"]

        today_10 = now.replace(hour=10, minute=0, second=0, microsecond=0)

        appointments_data = [
            {
                "reference_number": "APT-20261012-001",
                "carrier_id": tl_carrier.id,
                "warehouse_id": bud_wh.id,
                "dock_id": docks["BUD-DK-01"].id,
                "created_by": users["dispatcher@translog.com"].id,
                "scheduled_start": today_10 - timedelta(hours=2),
                "scheduled_end": today_10 - timedelta(hours=1),
                "status": "COMPLETED",
                "vehicle_registration": "HU-AB-774",
                "vehicle_type": "Curtainsider Semi-Trailer (40t)",
                "cargo_type": "FMCG / Palletized Goods",
                "cargo_description": "24 Euro-pallets packaged dry grocery products.",
                "cargo_weight_kg": 18200.0,
                "container_number": "TGHU-940214-8",
                "notes": "Unloaded on schedule without damages.",
            },
            {
                "reference_number": "APT-20261012-002",
                "carrier_id": sf_carrier.id,
                "warehouse_id": bud_wh.id,
                "dock_id": docks["BUD-DK-04"].id,
                "created_by": users["operations@speedyfreight.eu"].id,
                "scheduled_start": today_10,
                "scheduled_end": today_10 + timedelta(hours=2),
                "status": "IN_PROGRESS",
                "vehicle_registration": "PL-WN-40212",
                "vehicle_type": "Box Truck (18t)",
                "cargo_type": "Industrial Electronics",
                "cargo_description": "Precision electronic controllers and telecom units.",
                "cargo_weight_kg": 9500.0,
                "container_number": None,
                "notes": "Docked at bay 4, unloading in progress with forklift crew.",
            },
            {
                "reference_number": "APT-20261012-003",
                "carrier_id": dc_carrier.id,
                "warehouse_id": bud_wh.id,
                "dock_id": docks["BUD-DK-02"].id,
                "created_by": users["logistics@danubecargo.com"].id,
                "scheduled_start": today_10 + timedelta(hours=2, minutes=30),
                "scheduled_end": today_10 + timedelta(hours=4),
                "status": "CHECKED_IN",
                "vehicle_registration": "AT-W-88204K",
                "vehicle_type": "Reefer Semi-Trailer (-20°C)",
                "cargo_type": "Deep Frozen Foodstuffs",
                "cargo_description": "Frozen bakery dough and dessert products at -18C verified.",
                "cargo_weight_kg": 14500.0,
                "container_number": "MSKU-821034-1",
                "notes": "Driver checked in at gate. Awaiting temperature probe validation.",
            },
            {
                "reference_number": "APT-20261012-004",
                "carrier_id": tl_carrier.id,
                "warehouse_id": bud_wh.id,
                "dock_id": docks["BUD-DK-01"].id,
                "created_by": users["dispatcher@translog.com"].id,
                "scheduled_start": today_10 + timedelta(days=1, hours=1),
                "scheduled_end": today_10 + timedelta(days=1, hours=2, minutes=30),
                "status": "CONFIRMED",
                "vehicle_registration": "HU-TL-1290",
                "vehicle_type": "Standard Mega Trailer",
                "cargo_type": "Automotive Tier-1 Subassemblies",
                "cargo_description": "Wiring harnesses and cockpit modules for assembly line.",
                "cargo_weight_kg": 16800.0,
                "container_number": None,
                "notes": "Confirmed by warehouse dispatcher for tomorrow.",
            },
            {
                "reference_number": "APT-20261012-005",
                "carrier_id": sf_carrier.id,
                "warehouse_id": bud_wh.id,
                "dock_id": None,
                "created_by": users["operations@speedyfreight.eu"].id,
                "scheduled_start": today_10 + timedelta(days=1, hours=4),
                "scheduled_end": today_10 + timedelta(days=1, hours=5),
                "status": "PENDING",
                "vehicle_registration": "PL-WA-77112",
                "vehicle_type": "Curtainsider Truck",
                "cargo_type": "Consumer Packaged Goods",
                "cargo_description": "Household cleaners and personal care packages.",
                "cargo_weight_kg": 8900.0,
                "container_number": None,
                "notes": "Awaiting warehouse review and bay allocation.",
            },
            {
                "reference_number": "APT-20261012-006",
                "carrier_id": dc_carrier.id,
                "warehouse_id": gyor_wh.id,
                "dock_id": docks["GYR-DK-02"].id,
                "created_by": users["logistics@danubecargo.com"].id,
                "scheduled_start": today_10 + timedelta(days=1, hours=2),
                "scheduled_end": today_10 + timedelta(days=1, hours=3, minutes=30),
                "status": "CONFIRMED",
                "vehicle_registration": "AT-WZ-5510B",
                "vehicle_type": "ADR-Certified Box Semi",
                "cargo_type": "Chemical Adhesives (ADR Class 3)",
                "cargo_description": "Automotive solvent adhesives with safety data sheets attached.",
                "cargo_weight_kg": 11200.0,
                "container_number": "SEGU-309124-7",
                "notes": "Assigned to dedicated Hazmat Bay #2 in Gyor.",
            },
            {
                "reference_number": "APT-20261012-007",
                "carrier_id": tl_carrier.id,
                "warehouse_id": bud_wh.id,
                "dock_id": None,
                "created_by": users["dispatcher@translog.com"].id,
                "scheduled_start": today_10 + timedelta(days=2, hours=3),
                "scheduled_end": today_10 + timedelta(days=2, hours=4),
                "status": "DRAFT",
                "vehicle_registration": "HU-DR-902",
                "vehicle_type": "Standard Trailer",
                "cargo_type": "Packaging Paper & Cartons",
                "cargo_description": "Draft order - pallet counts pending confirmation from plant.",
                "cargo_weight_kg": 6400.0,
                "container_number": None,
                "notes": "Carrier internal draft.",
            },
            {
                "reference_number": "APT-20261012-008",
                "carrier_id": sf_carrier.id,
                "warehouse_id": bud_wh.id,
                "dock_id": None,
                "created_by": users["operations@speedyfreight.eu"].id,
                "scheduled_start": today_10 - timedelta(days=1, hours=3),
                "scheduled_end": today_10 - timedelta(days=1, hours=2),
                "status": "REJECTED",
                "vehicle_registration": "PL-KR-22904",
                "vehicle_type": "Articulated Tanker",
                "cargo_type": "Liquid Bulk Chemicals",
                "cargo_description": "Liquid resins requiring vapor recovery.",
                "cargo_weight_kg": 24000.0,
                "container_number": None,
                "notes": "Request submitted without compatible vapor recovery equipment.",
            },
            {
                "reference_number": "APT-20261012-009",
                "carrier_id": dc_carrier.id,
                "warehouse_id": bud_wh.id,
                "dock_id": docks["BUD-DK-01"].id,
                "created_by": users["logistics@danubecargo.com"].id,
                "scheduled_start": today_10 - timedelta(days=2, hours=5),
                "scheduled_end": today_10 - timedelta(days=2, hours=4),
                "status": "NO_SHOW",
                "vehicle_registration": "AT-S-90112F",
                "vehicle_type": "Standard Trailer",
                "cargo_type": "General Cargo",
                "cargo_description": "Palletized retail display materials.",
                "cargo_weight_kg": 7500.0,
                "container_number": None,
                "notes": "Vehicle failed to arrive within the scheduled 60-minute window.",
            },
            {
                "reference_number": "APT-20261012-010",
                "carrier_id": tl_carrier.id,
                "warehouse_id": bud_wh.id,
                "dock_id": None,
                "created_by": users["dispatcher@translog.com"].id,
                "scheduled_start": today_10 - timedelta(days=1, hours=1),
                "scheduled_end": today_10 - timedelta(days=1),
                "status": "CANCELLED",
                "vehicle_registration": "HU-CN-331",
                "vehicle_type": "Mega Trailer",
                "cargo_type": "Spare Parts",
                "cargo_description": "Cancelled due to supplier shipment production delay.",
                "cargo_weight_kg": 5000.0,
                "container_number": None,
                "notes": "Cancelled by carrier 4 hours in advance.",
            },
        ]

        for appt_dict in appointments_data:
            existing = db.scalar(
                select(Appointment).where(
                    Appointment.reference_number == appt_dict["reference_number"]
                )
            )
            if not existing:
                rejection = None
                if appt_dict["status"] == "REJECTED":
                    rejection = "Budapest facility does not have vapor recovery recovery equipment for bulk chemical tankers."

                appt = Appointment(
                    reference_number=appt_dict["reference_number"],
                    carrier_id=appt_dict["carrier_id"],
                    warehouse_id=appt_dict["warehouse_id"],
                    dock_id=appt_dict["dock_id"],
                    created_by=appt_dict["created_by"],
                    scheduled_start=appt_dict["scheduled_start"],
                    scheduled_end=appt_dict["scheduled_end"],
                    status=appt_dict["status"],
                    vehicle_registration=appt_dict["vehicle_registration"],
                    vehicle_type=appt_dict["vehicle_type"],
                    cargo_type=appt_dict["cargo_type"],
                    cargo_description=appt_dict["cargo_description"],
                    cargo_weight_kg=appt_dict["cargo_weight_kg"],
                    container_number=appt_dict["container_number"],
                    notes=appt_dict["notes"],
                    rejection_reason=rejection,
                )
                db.add(appt)
                db.flush()

                # Event record
                evt = AppointmentEvent(
                    appointment_id=appt.id,
                    changed_by=appt.created_by,
                    previous_status=None if appt.status in ("DRAFT", "PENDING") else "PENDING",
                    new_status=appt.status,
                    reason=rejection or f"Status set to {appt.status}",
                    event_type="STATUS_CHANGED",
                    created_at=appt.created_at,
                )
                db.add(evt)
                print(f"Created appointment: {appt.reference_number} [{appt.status}]")

        # 8. Sample Audit Logs
        db.flush()
        audit_sample = [
            AuditLog(
                user_id=mgr.id,
                action="CONFIRM_APPOINTMENT",
                entity_type="Appointment",
                entity_id=4,
                description="Confirmed appointment APT-20261012-004 on dock BUD-DK-01",
                new_values={"status": "CONFIRMED", "dock_id": docks["BUD-DK-01"].id},
                created_at=now - timedelta(hours=3),
            ),
            AuditLog(
                user_id=mgr.id,
                action="REGISTER_MAINTENANCE",
                entity_type="DockUnavailability",
                entity_id=1,
                description="Registered maintenance window for dock BUD-DK-03",
                created_at=now - timedelta(hours=5),
            ),
            AuditLog(
                user_id=users["admin@dockflow.local"].id,
                action="SYSTEM_INIT",
                entity_type="System",
                entity_id=1,
                description="System initialization and initial seed data applied",
                created_at=now - timedelta(days=1),
            ),
        ]
        for a in audit_sample:
            db.add(a)

        db.commit()
        print("\nSeed completed successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
