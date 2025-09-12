"""
Invoice Service for handling invoice creation and data preparation.
"""

from __future__ import annotations
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Any, List
from config.database import SessionLocal
from models.production import ProductionBatch
from models.orders import ClientOrder, Quotation
from models.clients import Client


class InvoiceService:
    """Service for handling invoice operations."""
    
    def __init__(self, session=None):
        self.session = session or SessionLocal()
        self._close_session = session is None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._close_session:
            self.session.close()
    
    def prepare_invoice_data(self, production_ids: List[int]) -> Dict[str, Any]:
        """
        Prepare invoice data from production batch IDs.
        
        Args:
            production_ids: List of production batch IDs
            
        Returns:
            Dictionary containing all invoice data
        """
        try:
            # Get production batches with relationships
            # Get production batches with basic relationships
            productions = self.session.query(ProductionBatch).filter(
                ProductionBatch.id.in_(production_ids)
            ).all()
            
            if not productions:
                raise ValueError("No production batches found")
            
            # Get client information from the first production's client order
            first_production = productions[0]
            if not first_production.client_order:
                raise ValueError("No client order found for production batch")
            
            client = first_production.client_order.client
            if not client:
                raise ValueError("No client found for production batch")
            
            # Check if all productions are for the same client
            for prod in productions:
                if prod.client_order and prod.client_order.client_id != client.id:
                    raise ValueError("All selected productions must be for the same client")
            
            # Generate invoice number
            invoice_number = self._generate_invoice_number()
            
            # Group products by their essential characteristics
            product_groups = {}
            
            for prod in productions:
                # Extract real product information from client order
                unit_price = Decimal('56.5')  # Default fallback
                quantity = prod.quantity or 0
                description = ""
                dimensions = ""
                color = ""
                cardboard_type = ""
                
                # Get detailed information from client order line items
                if prod.client_order and prod.client_order.line_items:
                    client_line_item = prod.client_order.line_items[0]
                    
                    # Use actual unit price from client order if available
                    if client_line_item.unit_price:
                        unit_price = client_line_item.unit_price
                    
                    # Get product description from client order line item
                    if client_line_item.description:
                        description = client_line_item.description
                    
                    # Build dimensions string
                    if client_line_item.length_mm and client_line_item.width_mm and client_line_item.height_mm:
                        dimensions = f"{client_line_item.length_mm}×{client_line_item.width_mm}×{client_line_item.height_mm}"
                    
                    # Get color and cardboard type
                    if client_line_item.color:
                        color = client_line_item.color.value if hasattr(client_line_item.color, 'value') else str(client_line_item.color)
                    
                    if client_line_item.cardboard_type:
                        cardboard_type = client_line_item.cardboard_type
                
                # PRIORITY: Try to get description from quotation (devis) first
                quotation_description = ""
                
                # First, try direct quotation link from client order
                if prod.client_order and prod.client_order.quotation and prod.client_order.quotation.line_items:
                    quotation_line_item = prod.client_order.quotation.line_items[0]
                    if quotation_line_item.description:
                        quotation_description = quotation_line_item.description
                        # Also get unit price from quotation if available
                        if quotation_line_item.unit_price:
                            unit_price = quotation_line_item.unit_price
                
                # Fallback: If no quotation linked, try to find the most recent quotation for this client
                if not quotation_description and prod.client_order and prod.client_order.client:
                    from sqlalchemy import desc
                    latest_quotation = self.session.query(Quotation).filter(
                        Quotation.client_id == prod.client_order.client.id
                    ).order_by(desc(Quotation.issue_date)).first()
                    
                    if latest_quotation and latest_quotation.line_items:
                        quotation_line_item = latest_quotation.line_items[0]
                        if quotation_line_item.description:
                            quotation_description = quotation_line_item.description
                            # Also get unit price from quotation if available
                            if quotation_line_item.unit_price:
                                unit_price = quotation_line_item.unit_price
                
                # Build base designation (prioritize quotation description)
                if quotation_description:
                    base_designation = quotation_description
                elif description:
                    base_designation = description
                elif dimensions:
                    base_designation = f"Caisse carton {dimensions}"
                    if cardboard_type:
                        base_designation += f" - {cardboard_type}"
                    if color and color != "STANDARD":
                        base_designation += f" - {color}"
                    print(f"DEBUG: Using auto-generated designation: '{base_designation}'")
                else:
                    base_designation = "Produit fini"
                    print(f"DEBUG: Using default designation: '{base_designation}'")
                
                # Create grouping key based on product characteristics
                group_key = (base_designation, unit_price, 19)  # Include TVA rate in grouping
                
                # Group products
                if group_key in product_groups:
                    product_groups[group_key]['quantity'] += quantity
                else:
                    product_groups[group_key] = {
                        'designation': base_designation,
                        'quantity': quantity,
                        'unit_price': unit_price,
                        'tva_rate': 19
                    }
            
            # Create line items from grouped products (sorted by designation)
            line_items = []
            total_ht = Decimal('0')
            
            # Sort groups by designation for consistent ordering
            sorted_groups = sorted(product_groups.items(), key=lambda x: x[1]['designation'])
            
            for group_key, product_data in sorted_groups:
                designation = product_data['designation']
                quantity = product_data['quantity']
                unit_price = product_data['unit_price']
                
                # Use clean designation without batch codes
                line_total = unit_price * quantity
                
                line_item_data = {
                    'designation': designation,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'line_total': line_total,
                    'tva_rate': 19  # 19% TVA
                }
                line_items.append(line_item_data)
                total_ht += line_total
            
            # Calculate totals
            discount_rate = Decimal('0')  # 0% discount by default
            total_ht_net = total_ht * (1 - discount_rate)
            tva_amount = total_ht_net * Decimal('0.19')  # 19% TVA
            total_ttc = total_ht_net + tva_amount
            timbre = total_ttc * Decimal('0.01')  # 1% timbre
            total_ttc_net = total_ttc + timbre
            
            # Convert amount to words
            amount_in_words = self._number_to_words_dz(total_ttc_net)
            
            # Prepare invoice data
            invoice_data = {
                'invoice_number': invoice_number,
                'invoice_date': date.today().strftime('%d/%m/%Y'),
                'client_name': client.name or '',
                'client_activity': getattr(client, 'activity', '') or '',
                'client_address': client.address or '',
                'client_rc': getattr(client, 'numero_rc', '') or '',
                'client_nif': getattr(client, 'nif', '') or '',
                'client_nis': getattr(client, 'nis', '') or '',
                'client_ai': getattr(client, 'ai', '') or '',
                'client_phone': client.phone or '',
                'payment_mode': 'Mode de Paiement: …',
                'line_items': line_items,
                'total_ht': total_ht,
                'discount': f"{discount_rate * 100:.0f}%",
                'total_ht_net': total_ht_net,
                'tva_amount': tva_amount,
                'total_ttc': total_ttc,
                'timbre': timbre,
                'total_ttc_net': total_ttc_net,
                'amount_in_words': amount_in_words,
                'signature_date': date.today().strftime('%d/%m/%Y')
            }
            
            return invoice_data
            
        except Exception as e:
            raise ValueError(f"Error preparing invoice data: {str(e)}")
    
    def _generate_invoice_number(self) -> str:
        """Generate a unique invoice number."""
        today = date.today()
        # Format: FACT-YYYYMMDD-NNNN
        date_str = today.strftime('%Y%m%d')
        
        # For simplicity, use timestamp-based numbering
        # In production, you might want to store invoice numbers in database
        time_str = datetime.now().strftime('%H%M%S')
        
        return f"FACT-{date_str}-{time_str}"
    
    def _number_to_words_dz(self, amount: Decimal) -> str:
        """
        Convert a decimal amount to words in French (Algerian Dinar).
        
        Args:
            amount: The decimal amount to convert
            
        Returns:
            String representation of the amount in words
        """
        try:
            # Split into dinars and centimes
            dinars = int(amount)
            centimes = int((amount - dinars) * 100)
            
            # Convert dinars to words
            dinars_words = self._convert_integer_to_words_fr(dinars)
            
            # Build the final string
            result = f"Arrêtée la présente facture à la somme de : {dinars_words} dinars algériens"
            
            if centimes > 0:
                centimes_words = self._convert_integer_to_words_fr(centimes)
                result += f" et {centimes_words} centimes"
            
            result += "."
            
            return result
            
        except Exception:
            # Fallback if conversion fails
            return f"Arrêtée la présente facture à la somme de : {amount:.2f} dinars algériens."
    
    def _convert_integer_to_words_fr(self, number: int) -> str:
        """Convert an integer to French words."""
        if number == 0:
            return "zéro"
        
        # French number words
        ones = ["", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf",
                "dix", "onze", "douze", "treize", "quatorze", "quinze", "seize", 
                "dix-sept", "dix-huit", "dix-neuf"]
        
        tens = ["", "", "vingt", "trente", "quarante", "cinquante", "soixante", 
                "soixante-dix", "quatre-vingt", "quatre-vingt-dix"]
        
        hundreds = ["", "cent", "deux cents", "trois cents", "quatre cents", 
                   "cinq cents", "six cents", "sept cents", "huit cents", "neuf cents"]
        
        def convert_hundreds(n):
            """Convert a number less than 1000 to words."""
            if n == 0:
                return ""
            
            result = ""
            
            # Hundreds
            if n >= 100:
                h = n // 100
                if h == 1:
                    result += "cent"
                else:
                    result += hundreds[h]
                n %= 100
                if n > 0:
                    result += " "
            
            # Tens and ones
            if n >= 20:
                t = n // 10
                result += tens[t]
                n %= 10
                if n > 0:
                    if t == 8 and n == 1:  # quatre-vingt-un
                        result += "-un"
                    else:
                        result += "-" + ones[n]
            elif n > 0:
                result += ones[n]
            
            return result
        
        if number < 1000:
            return convert_hundreds(number)
        
        # Handle thousands
        thousands = number // 1000
        remainder = number % 1000
        
        result = ""
        if thousands == 1:
            result = "mille"
        else:
            result = convert_hundreds(thousands) + " mille"
        
        if remainder > 0:
            result += " " + convert_hundreds(remainder)
        
        return result


__all__ = ['InvoiceService']
