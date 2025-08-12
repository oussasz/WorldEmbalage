from __future__ import annotations
from sqlalchemy.orm import Session
from loguru import logger
from models.orders import Quotation, ClientOrder, ClientOrderStatus, QuotationLineItem, ClientOrderLineItem
from models.clients import Client
from sqlalchemy import select
from decimal import Decimal
from typing import Sequence, Any, cast


class OrderService:
    def __init__(self, db: Session):
        self.db = db

    def create_quotation(self, client_id: int, reference: str, notes: str | None = None, line_items: Sequence[dict] | None = None, is_initial: bool = False) -> Quotation:
        client = self.db.get(Client, client_id)
        if not client:
            raise ValueError("Client not found")
        q = Quotation(client_id=client_id, reference=reference, notes=notes or '', is_initial=is_initial)
        self.db.add(q)
        self.db.flush()
        total = Decimal('0')
        for idx, item in enumerate(line_items or [], start=1):
            # Calculate total price based on numeric quantity
            import re
            quantity_str = str(item.get('quantity') or '0')
            numbers = re.findall(r'\d+', quantity_str)
            numeric_quantity = int(numbers[-1]) if numbers else 0
            unit_price = Decimal(str(item.get('unit_price') or '0'))
            calculated_total = unit_price * numeric_quantity

            li = QuotationLineItem(
                quotation_id=q.id,
                line_number=idx,
                description=str(item.get('description') or ''),
                quantity=quantity_str,
                unit_price=unit_price,
                total_price=calculated_total, # Use the calculated total
                length_mm=item.get('length_mm'),
                width_mm=item.get('width_mm'),
                height_mm=item.get('height_mm'),
                color=item.get('color'),
                cardboard_type=item.get('cardboard_type'),
                is_cliche=bool(item.get('is_cliche') or False),
                notes=(str(item.get('notes')).strip() if item.get('notes') else None),
            )
            total += calculated_total
            self.db.add(li)
        # Assign using cast to satisfy type checker for Numeric field
        cast(Any, q).total_amount = float(total)
        self.db.commit()
        self.db.refresh(q)
        return q

    def convert_to_order(self, quotation_id: int, reference: str) -> ClientOrder:
        quotation = self.db.get(Quotation, quotation_id)
        if not quotation:
            raise ValueError("Quotation not found")
        if quotation.client_order:
            raise ValueError("Quotation already converted")
        if quotation.is_initial:
            raise ValueError("Cannot convert initial quotation to order. Please specify quantities first.")
        order = ClientOrder(
            client_id=quotation.client_id,
            quotation_id=quotation.id,
            reference=reference,
            total_amount=quotation.total_amount,
        )
        self.db.add(order)
        self.db.flush()
        # create order line items from quotation line items
        for qli in quotation.line_items:
            oli = ClientOrderLineItem(
                client_order_id=order.id,
                quotation_line_item_id=qli.id,
                line_number=qli.line_number,
                description=qli.description,
                quantity=qli.quantity,  # Use original quantity string for order
                unit_price=qli.unit_price,
                total_price=qli.total_price,
                length_mm=qli.length_mm,
                width_mm=qli.width_mm,
                height_mm=qli.height_mm,
                color=qli.color,
                cardboard_type=qli.cardboard_type,
                is_cliche=qli.is_cliche,
                notes=qli.notes,
            )
            self.db.add(oli)
        self.db.commit()
        self.db.refresh(order)
        logger.debug("Quotation {} converted to order {}", quotation.reference, order.reference)
        return order

    def update_order_status(self, order_id: int, status: ClientOrderStatus) -> ClientOrder:
        order = self.db.get(ClientOrder, order_id)
        if not order:
            raise ValueError("Order not found")
        order.status = status
        self.db.commit()
        self.db.refresh(order)
        logger.debug("Order {} status updated to {}", order.reference, status)
        return order

    def list_orders(self) -> list[ClientOrder]:
        return list(self.db.scalars(select(ClientOrder)).all())

    def get_quotation_for_pdf(self, quotation_id: int) -> dict[str, Any]:
        """
        Get complete quotation data formatted for PDF generation.
        
        Args:
            quotation_id: ID of the quotation
            
        Returns:
            Dictionary containing all quotation data for PDF
        """
        quotation = self.db.get(Quotation, quotation_id)
        if not quotation:
            raise ValueError("Quotation not found")
        
        # Get client information
        client = quotation.client
        
        # Prepare line items data
        line_items = []
        total_amount = Decimal('0')
        
        for item in quotation.line_items:
            line_data = {
                'description': item.description,
                'quantity': item.quantity,
                'unit_price': float(Decimal(str(item.unit_price))),
                'total_price': float(Decimal(str(item.total_price))),
            }
            
            # Add dimensions if available
            if item.length_mm and item.width_mm and item.height_mm:
                line_data['dimensions'] = f"{item.length_mm} x {item.width_mm} x {item.height_mm} mm"
            
            # Add other details if available
            if item.color:
                line_data['color'] = item.color.value
            if item.cardboard_type:
                line_data['cardboard_type'] = item.cardboard_type
            if item.is_cliche:
                line_data['is_cliche'] = True
            if item.notes:
                line_data['item_notes'] = item.notes
            
            line_items.append(line_data)
            total_amount += Decimal(str(item.total_price))
        
        # Prepare client address
        client_address_parts = []
        if client.address:
            client_address_parts.append(client.address)
        if client.city:
            client_address_parts.append(client.city)
        # Note: postal_code is not in Client model
        
        client_address = ", ".join(client_address_parts) if client_address_parts else ""
        
        return {
            'reference': quotation.reference,
            'issue_date': str(quotation.issue_date) if quotation.issue_date else '',
            'valid_until': str(quotation.valid_until) if quotation.valid_until else '',
            'is_initial': quotation.is_initial,
            'client_name': client.name,
            'client_address': client_address,
            'client_phone': client.phone or '',
            'client_email': client.email or '',
            'line_items': line_items,
            'total_amount': float(total_amount),
            'notes': quotation.notes or '',
            'currency': quotation.currency
        }

__all__ = ['OrderService']
