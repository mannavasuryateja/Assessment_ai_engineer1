from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os
import streamlit as st
from datetime import datetime


def send_confirmation_email(to_email: str, booking_id: str, booking_state: dict):
    """
    Send booking confirmation email using SendGrid API.
    Uses professional HTML and plain text versions.
    """
    # Get SendGrid API key from environment or Streamlit secrets
    try:
        api_key = st.secrets.get("SENDGRID_API_KEY") or os.getenv("SENDGRID_API_KEY")
    except:
        api_key = os.getenv("SENDGRID_API_KEY")
    
    from_email = os.getenv("SENDGRID_FROM_EMAIL", "noreply@hotelbook.com")

    if not api_key:
        error_msg = (
            "⚠️  SendGrid API key not configured.\n"
            "To enable email confirmations:\n"
            "1. Create .env file with:\n"
            "   SENDGRID_API_KEY=SG.xxxxxxxxxxxxx\n"
            "   SENDGRID_FROM_EMAIL=noreply@yourdomain.com\n"
            "2. Or set environment variables\n"
            "Learn more: https://docs.sendgrid.com/ui/account-and-settings/api-keys"
        )
        print(error_msg)
        st.warning(error_msg)
        return False

    # Create HTML email content
    check_in = datetime.strptime(booking_state['check_in'], '%Y-%m-%d')
    check_out = datetime.strptime(booking_state['check_out'], '%Y-%m-%d')
    nights = (check_out - check_in).days
    
    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
        <div style="background-color: white; padding: 30px; border-radius: 8px; max-width: 600px; margin: 0 auto;">
          <h2 style="color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px;">Booking Confirmation</h2>
          
          <p style="font-size: 16px; color: #333;">Dear <strong>{booking_state['name']}</strong>,</p>
          
          <p style="color: #555; font-size: 15px;">Thank you for booking with us. Your reservation has been confirmed. Please find the details below:</p>
          
          <div style="background-color: #f8f9fa; padding: 20px; border-left: 4px solid #3498db; margin: 20px 0;">
            <p style="margin: 8px 0;"><strong>Booking ID:</strong> <span style="color: #3498db; font-size: 18px;">{booking_id}</span></p>
            <p style="margin: 8px 0;"><strong>Guest Name:</strong> {booking_state['name']}</p>
            <p style="margin: 8px 0;"><strong>Contact Number:</strong> {booking_state['phone']}</p>
            <p style="margin: 8px 0;"><strong>Room Category:</strong> {booking_state['room_type'].capitalize()}</p>
            <p style="margin: 8px 0;"><strong>Check-in Date:</strong> {booking_state['check_in']}</p>
            <p style="margin: 8px 0;"><strong>Check-out Date:</strong> {booking_state['check_out']}</p>
            <p style="margin: 8px 0;"><strong>Duration:</strong> {nights} night(s)</p>
          </div>
          
          <div style="background-color: #e8f8f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <p style="color: #27ae60; margin: 0;"><strong>✓ Booking Status:</strong> CONFIRMED</p>
          </div>
          
          <p style="color: #555; font-size: 15px; line-height: 1.6;">
            Your reservation is secured. We look forward to welcoming you. If you need to modify or cancel your booking, 
            please contact us as soon as possible referencing your booking ID.
          </p>
          
          <p style="color: #555; font-size: 15px; line-height: 1.6;">
            <strong>Check-in Information:</strong> Please arrive by 3:00 PM. Early check-in may be available upon request.
          </p>
          
          <p style="color: #555; font-size: 14px; margin-top: 20px;">
            Should you have any questions or special requests, please don't hesitate to contact our reservations team.
          </p>
          
          <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
          
          <p style="color: #7f8c8d; font-size: 12px; text-align: center;">
            This is an automated confirmation. Please do not reply directly to this email. 
            For assistance, contact our guest services.
          </p>
          
          <p style="color: #7f8c8d; font-size: 12px; text-align: center;">
            Best regards,<br><strong>The Hotel Management Team</strong>
          </p>
        </div>
      </body>
    </html>
    """
    
    text_body = f"""
Dear {booking_state['name']},

Thank you for booking with us. Your reservation has been confirmed.

BOOKING DETAILS:
Booking ID: {booking_id}
Guest Name: {booking_state['name']}
Contact: {booking_state['phone']}
Room Type: {booking_state['room_type'].capitalize()}
Check-in: {booking_state['check_in']}
Check-out: {booking_state['check_out']}
Duration: {nights} night(s)

BOOKING STATUS: CONFIRMED

We look forward to welcoming you. Please arrive by 3:00 PM.

Should you have any questions, please contact our guest services.

Best regards,
The Hotel Management Team
    """

    try:
        # Initialize SendGrid client
        sg = SendGridAPIClient(api_key)
        
        # Create email
        message = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=f"Booking Confirmation - Booking ID: {booking_id}",
            plain_text_content=text_body,
            html_content=html_body
        )
        
        # Send email
        response = sg.send(message)
        
        # Check response status (202 = accepted for delivery)
        if response.status_code == 202:
            print(f"✅ Email sent successfully to {to_email}")
            st.success(f"✅ Confirmation email sent to {to_email}")
            return True
        else:
            error = f"❌ Email service returned status {response.status_code}"
            print(error)
            st.error(error)
            return False
            
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "Unauthorized" in error_msg:
            detail = (
                "❌ SendGrid API authentication failed.\n"
                "Please verify your API key is correct in .env:\n"
                "SENDGRID_API_KEY=SG.xxxxx...\n"
                "Check: https://app.sendgrid.com/settings/api_keys"
            )
            print(detail)
            st.error(detail)
        else:
            error = f"❌ Failed to send email: {error_msg}"
            print(error)
            st.error(error)
        return False

