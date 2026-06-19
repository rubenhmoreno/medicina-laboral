from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.pedidos import repository as repo
from app.modules.pedidos.models import ItemPedido, Pedido, TipoPedido
from app.modules.pedidos.schemas import PedidoCreate
from app.modules.atenciones import repository as aten_repo
from app.shared.exceptions import NotFoundError


async def create_pedido(s: AsyncSession, payload: PedidoCreate, medico_id: UUID) -> Pedido:
    if not await aten_repo.get(s, payload.atencion_id):
        raise NotFoundError("atencion no encontrada")
    pedido = Pedido(
        atencion_id=payload.atencion_id,
        medico_id=medico_id,
        tipo=TipoPedido(payload.tipo),
        diagnostico=payload.diagnostico,
        indicaciones=payload.indicaciones,
    )
    for idx, item in enumerate(payload.items):
        pedido.items.append(ItemPedido(
            descripcion=item.descripcion,
            codigo=item.codigo,
            orden=idx,
        ))
    return await repo.insert(s, pedido)
