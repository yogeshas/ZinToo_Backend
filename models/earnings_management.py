from extensions import db
from datetime import datetime, date
from sqlalchemy import func

class EarningsManagement(db.Model):
    __tablename__ = "earnings_management"
    
    id = db.Column(db.Integer, primary_key=True)
    delivery_guy_id = db.Column(db.Integer, db.ForeignKey("delivery_onboarding.id"), nullable=False)
    payment_type = db.Column(db.String(20), nullable=False)  # salary, bonus, payout
    amount = db.Column(db.Float, nullable=False)
    payment_period = db.Column(db.String(20), nullable=False)  # daily, weekly, monthly
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)  # For weekly/monthly periods
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default="pending")  # pending, approved, paid, rejected
    admin_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)
    approved_by = db.Column(db.Integer, db.ForeignKey("admin.id"), nullable=True)
    paid_at = db.Column(db.DateTime, nullable=True)
    
    # Relationship with delivery guy
    delivery_guy = db.relationship("DeliveryOnboarding", backref="earnings")
    
    def as_dict(self):
        # Create full name from first_name and last_name
        delivery_guy_name = None
        delivery_guy_email = None
        if self.delivery_guy:
            full_name = f"{self.delivery_guy.first_name or ''} {self.delivery_guy.last_name or ''}".strip()
            delivery_guy_name = full_name if full_name else 'Unknown'
            delivery_guy_email = self.delivery_guy.email
        
        return {
            'id': self.id,
            'delivery_guy_id': self.delivery_guy_id,
            'delivery_guy_name': delivery_guy_name,
            'delivery_guy_email': delivery_guy_email,
            'payment_type': self.payment_type,
            'amount': self.amount,
            'payment_period': self.payment_period,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'description': self.description,
            'status': self.status,
            'admin_notes': self.admin_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'approved_by': self.approved_by,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None
        }
    
    @staticmethod
    def get_earnings_summary(delivery_guy_id=None, start_date=None, end_date=None, payment_type=None):
        """Get earnings summary for dashboard"""
        query = db.session.query(
            EarningsManagement.payment_type,
            func.sum(EarningsManagement.amount).label('total_amount'),
            func.count(EarningsManagement.id).label('count')
        )
        
        if delivery_guy_id:
            query = query.filter(EarningsManagement.delivery_guy_id == delivery_guy_id)
        
        if start_date:
            query = query.filter(EarningsManagement.start_date >= start_date)
            
        if end_date:
            query = query.filter(EarningsManagement.start_date <= end_date)
            
        if payment_type:
            query = query.filter(EarningsManagement.payment_type == payment_type)
            
        query = query.filter(EarningsManagement.status.in_(['approved', 'paid']))
        
        return query.group_by(EarningsManagement.payment_type).all()
    
    @staticmethod
    def get_weekly_breakdown(delivery_guy_id=None, start_date=None, end_date=None, payment_type=None):
        """Get weekly breakdown of earnings (MySQL compatible)"""
        # MySQL equivalent of date_trunc('week', date) - get Monday of the week
        # Using raw SQL for better MariaDB compatibility
        from sqlalchemy import text
        
        # Build the base query
        base_query = """
        SELECT 
            DATE_SUB(start_date, INTERVAL WEEKDAY(start_date) DAY) as week_start,
            payment_type,
            SUM(amount) as total_amount,
            COUNT(id) as count
        FROM earnings_management
        WHERE status IN ('approved', 'paid')
        """
        
        params = {}
        conditions = []
        
        if delivery_guy_id:
            conditions.append("delivery_guy_id = :delivery_guy_id")
            params['delivery_guy_id'] = delivery_guy_id
        
        if start_date:
            conditions.append("start_date >= :start_date")
            params['start_date'] = start_date
            
        if end_date:
            conditions.append("start_date <= :end_date")
            params['end_date'] = end_date
            
        if payment_type:
            conditions.append("payment_type = :payment_type")
            params['payment_type'] = payment_type
        
        if conditions:
            base_query += " AND " + " AND ".join(conditions)
        
        base_query += """
        GROUP BY DATE_SUB(start_date, INTERVAL WEEKDAY(start_date) DAY), payment_type
        ORDER BY DATE_SUB(start_date, INTERVAL WEEKDAY(start_date) DAY) DESC
        """
        
        result = db.session.execute(text(base_query), params)
        
        # Convert to list of objects with the same structure as before
        weekly_data = []
        for row in result:
            weekly_data.append(type('WeeklyBreakdown', (), {
                'week_start': row.week_start,
                'payment_type': row.payment_type,
                'total_amount': float(row.total_amount),
                'count': row.count
            })())
        
        return weekly_data
    
    @staticmethod
    def get_daily_breakdown(delivery_guy_id=None, start_date=None, end_date=None, payment_type=None):
        """Get daily breakdown of earnings"""
        query = db.session.query(
            EarningsManagement.start_date,
            EarningsManagement.payment_type,
            func.sum(EarningsManagement.amount).label('total_amount'),
            func.count(EarningsManagement.id).label('count')
        )
        
        if delivery_guy_id:
            query = query.filter(EarningsManagement.delivery_guy_id == delivery_guy_id)
        
        if start_date:
            query = query.filter(EarningsManagement.start_date >= start_date)
            
        if end_date:
            query = query.filter(EarningsManagement.start_date <= end_date)
            
        if payment_type:
            query = query.filter(EarningsManagement.payment_type == payment_type)
            
        query = query.filter(EarningsManagement.status.in_(['approved', 'paid']))
        
        return query.group_by(
            EarningsManagement.start_date,
            EarningsManagement.payment_type
        ).order_by(EarningsManagement.start_date.desc()).all()
    
    def __repr__(self):
        return f"<EarningsManagement {self.payment_type} - {self.amount} for delivery_guy_id {self.delivery_guy_id}>"
