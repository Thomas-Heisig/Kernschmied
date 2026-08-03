import asyncio
from sqlalchemy import select, func
from app.database.models.hierarchy_node import HierarchyNodeModel
from app.storage.database import init_database
from app.storage.models.chat import Chat as ChatModel
from app.storage.models.chat import Message as MessageModel

async def main():
    sf = await init_database(create_schema=False)
    async with sf() as s:
        for name in ("Public","Intern"):
            q = select(HierarchyNodeModel).where(HierarchyNodeModel.name==name)
            rows = (await s.execute(q)).scalars().all()
            print(f"Nodes named {name}: {len(rows)}")
            for n in rows:
                sys_prompt_len = len(n.system_prompt) if n.system_prompt else 0
                print(f"- id={n.id} type={n.type} parent_id={n.parent_id} position={n.position} is_system={n.is_system} is_active={n.is_active} is_movable={n.is_movable} is_deletable={n.is_deletable} prompt_enabled={n.prompt_enabled} prompt_priority={n.prompt_priority} prompt_mode={n.prompt_mode} system_prompt_len={sys_prompt_len} metadata={n.node_metadata}")
                qc = select(func.count()).select_from(HierarchyNodeModel).where(HierarchyNodeModel.parent_id==n.id)
                cnt = (await s.execute(qc)).scalar_one()
                print(f"  children_count={cnt}")
                qch = select(ChatModel).where(ChatModel.node_id==n.id)
                chats = (await s.execute(qch)).scalars().all()
                print(f"  linked_chats={len(chats)}")
                for c in chats:
                    mq = select(func.count()).select_from(MessageModel).where(MessageModel.conversation_id==c.id)
                    mcnt = (await s.execute(mq)).scalar_one()
                    print(f"    chat id={c.id} title={c.title} messages={int(mcnt)}")

if __name__ == '__main__':
    asyncio.run(main())
