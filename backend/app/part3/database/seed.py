from sqlalchemy.orm import Session
from app.part3.models.agent import Agent, Permission

INITIAL_AGENTS = [
    {
        "agent_id": "support_agent",
        "name": "Customer Support Agent",
        "description": "Handles support queries, customer CRM status, ticketing, and emails",
        "is_active": True,
        "permissions": [
            ("crm", "read"),
            ("crm", "update"),
            ("ticketing", "read"),
            ("ticketing", "update"),
            ("email", "send"),
        ]
    },
    {
        "agent_id": "sales_agent",
        "name": "Sales Representative Agent",
        "description": "Engages leads, reads/updates CRM, and sends outbound emails",
        "is_active": True,
        "permissions": [
            ("crm", "read"),
            ("crm", "update"),
            ("email", "send"),
            ("ticketing", "read"),
        ]
    },
    {
        "agent_id": "admin_agent",
        "name": "System Administrator Agent",
        "description": "Performs system operations across database, CRM, ticketing, and emails",
        "is_active": True,
        "permissions": [
            ("crm", "read"),
            ("crm", "update"),
            ("database", "read"),
            ("database", "write"),
            ("database", "update"),
            ("ticketing", "read"),
            ("ticketing", "update"),
            ("email", "send"),
        ]
    }
]


def seed_agents(db: Session):
    for agent_data in INITIAL_AGENTS:
        existing = db.query(Agent).filter(Agent.agent_id == agent_data["agent_id"]).first()
        if not existing:
            agent = Agent(
                agent_id=agent_data["agent_id"],
                name=agent_data["name"],
                description=agent_data["description"],
                is_active=agent_data["is_active"]
            )
            db.add(agent)
            db.flush()

            for tool, op in agent_data["permissions"]:
                perm = Permission(
                    agent_id=agent_data["agent_id"],
                    tool_name=tool,
                    operation=op
                )
                db.add(perm)

    db.commit()
