import asyncio
import uuid
from sqlalchemy import select
from app.core.database import AsyncSessionFactory
from app.models.models import Role, User, Section, UserSection, PermissionLevelEnum, Location, Item, ItemStatusEnum
from app.core.security import hash_password

async def seed_data():
    async with AsyncSessionFactory() as db:
        print("Fetching Roles...")
        roles = (await db.execute(select(Role))).scalars().all()
        role_map = {r.name: r for r in roles}
        
        required_roles = ["ADMIN", "MANAGER", "EMPLOYEE", "VIEWER"]
        for rr in required_roles:
            if rr not in role_map:
                new_role = Role(name=rr, description=f"{rr} role")
                db.add(new_role)
                role_map[rr] = new_role
        await db.flush()
        admin_user = (await db.execute(select(User).where(User.username == "admin"))).scalars().first()
        if not admin_user:
            print("Admin user not found. Cannot proceed.")
            return

        print("Adding Sections...")
        section_names = ["Quality Center", "Labs", "Production", "Warehouse"]
        sections = {}
        for sname in section_names:
            s = (await db.execute(select(Section).where(Section.name == sname))).scalars().first()
            if not s:
                s = Section(name=sname, description=f"{sname} Department")
                db.add(s)
            sections[sname] = s
        await db.flush()
        
        print("Adding Users...")
        users_to_create = [
            {"username": "qc_manager", "email": "qc@example.com", "password": "Password@123", "role": "MANAGER", "section": "Quality Center", "permission": PermissionLevelEnum.WRITE},
            {"username": "lab_tech", "email": "lab@example.com", "password": "Password@123", "role": "EMPLOYEE", "section": "Labs", "permission": PermissionLevelEnum.WRITE},
            {"username": "prod_worker", "email": "prod@example.com", "password": "Password@123", "role": "EMPLOYEE", "section": "Production", "permission": PermissionLevelEnum.READ},
            {"username": "wh_manager", "email": "wh@example.com", "password": "Password@123", "role": "MANAGER", "section": "Warehouse", "permission": PermissionLevelEnum.ADMIN},
            {"username": "viewer", "email": "viewer@example.com", "password": "Password@123", "role": "VIEWER", "section": "Production", "permission": PermissionLevelEnum.READ},
        ]
        
        created_users = []
        for u in users_to_create:
            user = (await db.execute(select(User).where(User.username == u["username"]))).scalars().first()
            if not user:
                user = User(
                    username=u["username"],
                    email=u["email"],
                    password_hash=hash_password(u["password"]),
                    full_name=u["username"].replace("_", " ").title(),
                    role_id=role_map[u["role"]].id,
                    is_active=True
                )
                db.add(user)
                await db.flush()
                
                # Assign section
                sec = sections[u["section"]]
                us = UserSection(
                    user_id=user.id,
                    section_id=sec.id,
                    permission_level=u["permission"]
                )
                db.add(us)
            created_users.append(user)
            
        print("Adding Warehouse Locations...")
        locations = []
        loc_data = [
            ("Main WH", "A", "1", "1", "WH-A-1-1"),
            ("Main WH", "A", "1", "2", "WH-A-1-2"),
            ("Cold Storage", "C", "1", "1", "CS-C-1-1")
        ]
        for wh_name, rack, shelf, pos, code in loc_data:
            loc = (await db.execute(select(Location).where(Location.location_code == code))).scalars().first()
            if not loc:
                loc = Location(warehouse_name=wh_name, rack=rack, shelf=shelf, position=pos, location_code=code)
                db.add(loc)
            locations.append(loc)
        await db.flush()

        print("Adding Warehouse Items...")
        items_data = [
            ("RM-000101", "Sodium Chloride", 500.0, "KG", locations[0].id),
            ("RM-000102", "Potassium Sorbate", 250.5, "KG", locations[1].id),
            ("PM-000201", "Glass Vials 10ml", 10000, "PCS", locations[0].id),
            ("RM-000301", "Active Pharma Ingredient A", 50.0, "KG", locations[2].id)
        ]
        
        for code, name, qty, unit, loc_id in items_data:
            item = (await db.execute(select(Item).where(Item.item_code == code))).scalars().first()
            if not item:
                item = Item(
                    item_code=code,
                    material_name=name,
                    quantity=qty,
                    unit=unit,
                    location_id=loc_id,
                    created_by=admin_user.id,
                    status=ItemStatusEnum.AVAILABLE
                )
                db.add(item)

        await db.commit()
        print("Done!")

if __name__ == "__main__":
    asyncio.run(seed_data())
