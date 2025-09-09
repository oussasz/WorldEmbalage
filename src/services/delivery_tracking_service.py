"""
Service for managing material deliveries and partial delivery tracking
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from models.orders import (
    SupplierOrder, SupplierOrderLineItem, MaterialDelivery, 
    DeliveryStatus, SupplierOrderStatus
)
from config.database import SessionLocal
from datetime import datetime


class DeliveryTrackingService:
    """Service for tracking partial deliveries of raw materials"""
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session or SessionLocal()
        self._own_session = session is None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._own_session:
            self.session.close()
    
    def find_matching_line_items(self, width: int, height: int, rabat: int) -> List[SupplierOrderLineItem]:
        """Find supplier order line items that match the given dimensions"""
        return self.session.query(SupplierOrderLineItem).filter(
            SupplierOrderLineItem.plaque_width_mm == width,
            SupplierOrderLineItem.plaque_length_mm == height,
            SupplierOrderLineItem.plaque_flap_mm == rabat,
            SupplierOrderLineItem.supplier_order.has(
                SupplierOrder.status.in_([
                    SupplierOrderStatus.ORDERED,
                    SupplierOrderStatus.PARTIALLY_DELIVERED
                ])
            )
        ).all()
    
    def calculate_delivery_needs(self, line_item: SupplierOrderLineItem) -> Dict[str, int]:
        """Calculate delivery needs for a line item"""
        ordered_quantity = line_item.quantity
        received_quantity = getattr(line_item, 'total_received_quantity', 0) or 0
        remaining_quantity = max(0, ordered_quantity - received_quantity)
        
        return {
            'ordered': ordered_quantity,
            'received': received_quantity,
            'remaining': remaining_quantity,
            'completion_percentage': int((received_quantity / ordered_quantity) * 100) if ordered_quantity > 0 else 0
        }
    
    def record_delivery(
        self, 
        line_item_id: int, 
        received_quantity: int, 
        batch_reference: Optional[str] = None,
        quality_notes: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Record a new delivery for a line item
        Returns (success, message)
        """
        try:
            line_item = self.session.get(SupplierOrderLineItem, line_item_id)
            if not line_item:
                return False, f"Line item {line_item_id} not found"
            
            # Check if we can receive this quantity
            needs = self.calculate_delivery_needs(line_item)
            if received_quantity > needs['remaining']:
                return False, f"Cannot receive {received_quantity} items. Only {needs['remaining']} remaining."
            
            # Create delivery record if table exists
            try:
                delivery = MaterialDelivery(
                    supplier_order_line_item_id=line_item_id,
                    received_quantity=received_quantity,
                    batch_reference=batch_reference or f"BATCH-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                    quality_notes=quality_notes
                )
                self.session.add(delivery)
            except Exception as e:
                # MaterialDelivery table might not exist yet, continue without it
                print(f"Delivery tracking not available: {e}")
            
            # Update line item quantities
            if not hasattr(line_item, 'total_received_quantity'):
                # Add the attribute if it doesn't exist (for backwards compatibility)
                line_item.total_received_quantity = 0
            
            line_item.total_received_quantity = (line_item.total_received_quantity or 0) + received_quantity
            
            # Update delivery status
            if hasattr(line_item, 'delivery_status'):
                if line_item.total_received_quantity >= line_item.quantity:
                    line_item.delivery_status = DeliveryStatus.COMPLETE
                elif line_item.total_received_quantity > 0:
                    line_item.delivery_status = DeliveryStatus.PARTIAL
                else:
                    line_item.delivery_status = DeliveryStatus.PENDING
            
            # Check if entire supplier order is complete
            self._update_supplier_order_status(line_item.supplier_order_id)
            
            self.session.commit()
            return True, f"Delivery recorded successfully. {line_item.total_received_quantity}/{line_item.quantity} received."
            
        except Exception as e:
            self.session.rollback()
            return False, f"Error recording delivery: {str(e)}"
    
    def _update_supplier_order_status(self, supplier_order_id: int):
        """Update supplier order status based on line item completion"""
        supplier_order = self.session.get(SupplierOrder, supplier_order_id)
        if not supplier_order:
            return
        
        line_items = supplier_order.line_items
        if not line_items:
            return
        
        # Check completion status of all line items
        total_items = len(line_items)
        complete_items = 0
        partial_items = 0
        
        for item in line_items:
            received_qty = getattr(item, 'total_received_quantity', 0) or 0
            ordered_qty = item.quantity
            
            if received_qty >= ordered_qty:
                complete_items += 1
                # Update delivery status if available
                if hasattr(item, 'delivery_status'):
                    item.delivery_status = DeliveryStatus.COMPLETE
            elif received_qty > 0:
                partial_items += 1
                # Update delivery status if available
                if hasattr(item, 'delivery_status'):
                    item.delivery_status = DeliveryStatus.PARTIAL
            else:
                # No delivery yet
                if hasattr(item, 'delivery_status'):
                    item.delivery_status = DeliveryStatus.PENDING
        
        # Update supplier order status based on ALL line items
        if complete_items == total_items:
            # ALL line items are complete - use COMPLETED status
            supplier_order.status = SupplierOrderStatus.COMPLETED
        elif complete_items > 0 or partial_items > 0:
            # Some items complete/partial but not all - use PARTIALLY_DELIVERED
            supplier_order.status = SupplierOrderStatus.PARTIALLY_DELIVERED
        # If no items received, keep current status (usually ORDERED)
    
    def get_delivery_summary(self, supplier_order_id: int) -> Dict[str, Any]:
        """Get delivery summary for a supplier order"""
        supplier_order = self.session.get(SupplierOrder, supplier_order_id)
        if not supplier_order:
            return {}
        
        summary = {
            'order_reference': getattr(supplier_order, 'bon_commande_ref', ''),
            'total_line_items': len(supplier_order.line_items),
            'line_items_status': [],
            'overall_completion': 0
        }
        
        total_ordered = 0
        total_received = 0
        
        for item in supplier_order.line_items:
            needs = self.calculate_delivery_needs(item)
            total_ordered += needs['ordered']
            total_received += needs['received']
            
            summary['line_items_status'].append({
                'id': item.id,
                'code_article': item.code_article,
                'dimensions': f"{item.plaque_width_mm}x{item.plaque_length_mm}x{item.plaque_flap_mm}mm",
                'ordered': needs['ordered'],
                'received': needs['received'],
                'remaining': needs['remaining'],
                'completion': needs['completion_percentage'],
                'status': getattr(item, 'delivery_status', 'pending')
            })
        
        summary['overall_completion'] = int((total_received / total_ordered) * 100) if total_ordered > 0 else 0
        summary['total_ordered'] = total_ordered
        summary['total_received'] = total_received
        
        return summary
    
    def get_pending_deliveries(self) -> List[Dict[str, Any]]:
        """Get all line items that are pending or partially delivered"""
        line_items = self.session.query(SupplierOrderLineItem).filter(
            SupplierOrderLineItem.supplier_order.has(
                SupplierOrder.status.in_([
                    SupplierOrderStatus.ORDERED,
                    SupplierOrderStatus.PARTIALLY_DELIVERED
                ])
            )
        ).all()
        
        pending = []
        for item in line_items:
            needs = self.calculate_delivery_needs(item)
            if needs['remaining'] > 0:
                pending.append({
                    'id': item.id,
                    'supplier_order_id': item.supplier_order_id,
                    'bon_commande_ref': getattr(item.supplier_order, 'bon_commande_ref', ''),
                    'code_article': item.code_article,
                    'dimensions': f"{item.plaque_width_mm}x{item.plaque_length_mm}x{item.plaque_flap_mm}mm",
                    'ordered': needs['ordered'],
                    'received': needs['received'],
                    'remaining': needs['remaining'],
                    'completion': needs['completion_percentage']
                })
        
        return pending
