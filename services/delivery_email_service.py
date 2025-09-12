# services/delivery_email_service.py
import threading
from flask_mail import Message
from flask import current_app
from extensions import mail

def send_email_async(app, msg):
    """Send email in a separate thread to avoid blocking the main request"""
    try:
        with app.app_context():
            mail.send(msg)
            print(f"✅ Email sent successfully to {msg.recipients[0]}")
    except Exception as e:
        print(f"❌ Email sending error: {str(e)}")

def send_approval_email(delivery_guy_email, delivery_guy_name):
    """Send approval email to delivery personnel"""
    try:
        msg = Message(
            "🎉 Your ZinToo Delivery Application Has Been Approved!",
            recipients=[delivery_guy_email]
        )
        
        msg.body = f"""
Dear {delivery_guy_name},

Congratulations! Your delivery personnel application with ZinToo has been approved.

You are now officially part of our delivery team and can start accepting delivery assignments.

Next Steps:
1. Download the ZinToo Delivery App
2. Log in with your registered credentials
3. Start accepting delivery orders
4. Complete your first delivery to earn rewards

If you have any questions, please contact our support team.

Welcome to the ZinToo family!

Best regards,
ZinToo Team
        """
        
        msg.html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0; font-size: 28px;">🎉 Application Approved!</h1>
                <p style="margin: 10px 0 0 0; font-size: 16px;">Welcome to the ZinToo Delivery Team</p>
            </div>
            
            <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                <h2 style="color: #333; margin-top: 0;">Dear {delivery_guy_name},</h2>
                
                <p style="color: #555; line-height: 1.6; font-size: 16px;">
                    Congratulations! Your delivery personnel application with ZinToo has been <strong>approved</strong>.
                </p>
                
                <div style="background: #e8f5e8; border-left: 4px solid #28a745; padding: 20px; margin: 20px 0; border-radius: 5px;">
                    <h3 style="color: #28a745; margin-top: 0;">✅ You are now officially part of our delivery team!</h3>
                    <p style="color: #155724; margin-bottom: 0;">You can start accepting delivery assignments immediately.</p>
                </div>
                
                <h3 style="color: #333;">🚀 Next Steps:</h3>
                <ol style="color: #555; line-height: 1.8;">
                    <li><strong>Download</strong> the ZinToo Delivery App</li>
                    <li><strong>Log in</strong> with your registered credentials</li>
                    <li><strong>Start accepting</strong> delivery orders</li>
                    <li><strong>Complete</strong> your first delivery to earn rewards</li>
                </ol>
                
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="color: #856404; margin: 0;">
                        💡 <strong>Tip:</strong> Complete more deliveries to increase your earnings and unlock bonus rewards!
                    </p>
                </div>
                
                <p style="color: #555; line-height: 1.6;">
                    If you have any questions or need assistance, please don't hesitate to contact our support team.
                </p>
                
                <p style="color: #555; line-height: 1.6;">
                    Welcome to the ZinToo family! We're excited to have you on board.
                </p>
                
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6;">
                    <p style="color: #6c757d; margin: 0;">
                        Best regards,<br>
                        <strong>ZinToo Team</strong>
                    </p>
                </div>
            </div>
        </div>
        """
        
        # Send email in background thread
        app = current_app._get_current_object()
        email_thread = threading.Thread(target=send_email_async, args=(app, msg,))
        email_thread.daemon = True
        email_thread.start()
        
        return True
        
    except Exception as e:
        print(f"❌ Error sending approval email: {str(e)}")
        return False

def send_rejection_email(delivery_guy_email, delivery_guy_name, rejection_reason):
    """Send rejection email to delivery personnel with reason"""
    try:
        msg = Message(
            "📋 ZinToo Delivery Application Update",
            recipients=[delivery_guy_email]
        )
        
        msg.body = f"""
Dear {delivery_guy_name},

Thank you for your interest in joining the ZinToo delivery team. After careful review of your application, we regret to inform you that your application has not been approved at this time.

Reason for Rejection:
{rejection_reason}

What You Can Do:
1. Review the rejection reason above
2. Address the issues mentioned
3. Re-upload corrected documents
4. Resubmit your application

We encourage you to address the concerns and reapply. Our team is here to help you succeed.

If you have any questions, please contact our support team.

Best regards,
ZinToo Team
        """
        
        msg.html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0; font-size: 28px;">📋 Application Update</h1>
                <p style="margin: 10px 0 0 0; font-size: 16px;">Important information about your delivery application</p>
            </div>
            
            <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                <h2 style="color: #333; margin-top: 0;">Dear {delivery_guy_name},</h2>
                
                <p style="color: #555; line-height: 1.6; font-size: 16px;">
                    Thank you for your interest in joining the ZinToo delivery team. After careful review of your application, we regret to inform you that your application has not been approved at this time.
                </p>
                
                <div style="background: #f8d7da; border-left: 4px solid #dc3545; padding: 20px; margin: 20px 0; border-radius: 5px;">
                    <h3 style="color: #721c24; margin-top: 0;">📋 Reason for Rejection:</h3>
                    <p style="color: #721c24; margin-bottom: 0; white-space: pre-line;">{rejection_reason}</p>
                </div>
                
                <h3 style="color: #333;">🔄 What You Can Do:</h3>
                <ol style="color: #555; line-height: 1.8;">
                    <li><strong>Review</strong> the rejection reason above</li>
                    <li><strong>Address</strong> the issues mentioned</li>
                    <li><strong>Re-upload</strong> corrected documents</li>
                    <li><strong>Resubmit</strong> your application</li>
                </ol>
                
                <div style="background: #d1ecf1; border: 1px solid #bee5eb; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="color: #0c5460; margin: 0;">
                        💡 <strong>Don't give up!</strong> We encourage you to address the concerns and reapply. Our team is here to help you succeed.
                    </p>
                </div>
                
                <p style="color: #555; line-height: 1.6;">
                    If you have any questions or need assistance with the reapplication process, please don't hesitate to contact our support team.
                </p>
                
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6;">
                    <p style="color: #6c757d; margin: 0;">
                        Best regards,<br>
                        <strong>ZinToo Team</strong>
                    </p>
                </div>
            </div>
        </div>
        """
        
        # Send email in background thread
        app = current_app._get_current_object()
        email_thread = threading.Thread(target=send_email_async, args=(app, msg,))
        email_thread.daemon = True
        email_thread.start()
        
        return True
        
    except Exception as e:
        print(f"❌ Error sending rejection email: {str(e)}")
        return False
