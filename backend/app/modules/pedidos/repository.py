from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.pedidos.models import Pedido


async def insert(s: AsyncSession, p: Pedido) -> Pedido:
    s.add(p); await s.flush(); await s.refresh(p, ["items"]); return p


async def get(s: AsyncSession, id_: UUID) -> Pedido | None:
    return (await s.execute(
        select(Pedido).options(selectinload(Pedido.items)).where(Pedido.id == id_)
    )).scalar_one_or_none()


async def list_by_atencion(s: AsyncSession, atencion_id: UUID) -> list[Pedido]:
    return list((await s.execute(
        select(Pedido).options(selectinload(Pedido.items))
        .where(Pedido.atencion_id == atencion_id)
        .order_by(Pedido.created_at.desc())
    )).scalars())
