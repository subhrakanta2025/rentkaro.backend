import random
import string
import requests
from datetime import datetime, timedelta
from flask import current_app

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(email, otp):
    """Send OTP to user email using ZeptoMail API"""
    try:
        api_url = current_app.config.get('ZEPTOMAIL_API_URL')
        api_key = current_app.config.get('ZEPTOMAIL_API_KEY')
        from_email = current_app.config.get('ZEPTOMAIL_FROM_EMAIL')

        # Trim whitespace/newlines from API key loaded from env
        if api_key:
            api_key = api_key.strip()

        if not api_key:
            current_app.logger.warning('ZeptoMail API key not configured')
            return False
        
        headers = {
            'Authorization': api_key,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'from': {
                'address': from_email,
                'name': 'Ride India Rentals'
            },
            'to': [
                {
                    'email_address': {
                        'address': email
                    }
                }
            ],
            'subject': 'Ride India Rentals - Email Verification',
            'htmlbody': f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #333;">Welcome to Ride India Rentals</h2>
                        
                        <p>Hello,</p>
                        
                        <p>Thank you for registering with us! To activate your account, please use the following OTP:</p>
                        
                        <div style="background-color: #f0f0f0; padding: 20px; text-align: center; margin: 20px 0; border-radius: 5px;">
                            <h1 style="color: #2196F3; letter-spacing: 5px; margin: 0;">{otp}</h1>
                        </div>
                        
                        <p><strong>This OTP is valid for 10 minutes only.</strong></p>
                        
                        <p>If you did not create this account, please ignore this email.</p>
                        
                        <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                        
                        <p style="color: #666; font-size: 12px;">
                            Ride India Rentals<br>
                            Email: support@rideindiarentals.com<br>
                            © 2025 All rights reserved.
                        </p>
                    </div>
                </body>
            </html>
            """
        }
        
        response = requests.post(api_url, json=payload, headers=headers, timeout=10)

        # Log detailed response for debugging deliverability issues
        try:
            body_text = response.text
        except Exception:
            body_text = '<no body>'

        if response.status_code in (200, 201):
            current_app.logger.info('OTP email accepted by ZeptoMail (%s) for %s', response.status_code, email)
            current_app.logger.debug('ZeptoMail response: %s', body_text)
            return True
        else:
            current_app.logger.error('Error sending OTP email: %s - %s', response.status_code, body_text)
            return False
            
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def send_activation_email(email, name):
    """Send account activation confirmation email using ZeptoMail API"""
    try:
        api_url = current_app.config.get('ZEPTOMAIL_API_URL')
        api_key = current_app.config.get('ZEPTOMAIL_API_KEY')
        from_email = current_app.config.get('ZEPTOMAIL_FROM_EMAIL')

        if api_key:
            api_key = api_key.strip()

        if not api_key:
            current_app.logger.warning('ZeptoMail API key not configured')
            return False
        
        headers = {
            'Authorization': api_key,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'from': {
                'address': from_email,
                'name': 'Ride India Rentals'
            },
            'to': [
                {
                    'email_address': {
                        'address': email
                    }
                }
            ],
            'subject': 'Account Activated - Ride India Rentals',
            'htmlbody': f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #333;">Account Activated Successfully</h2>
                        
                        <p>Hello {name},</p>
                        
                        <p>Congratulations! Your account has been activated successfully. You can now log in and start booking vehicles.</p>
                        
                        <p style="margin: 20px 0;">
                            <a href="http://localhost:8080/login" style="background-color: #2196F3; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                                Go to Login
                            </a>
                        </p>
                        
                        <p>Happy renting!</p>
                        
                        <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                        
                        <p style="color: #666; font-size: 12px;">
                            Ride India Rentals<br>
                            Email: support@rideindiarentals.com<br>
                            © 2025 All rights reserved.
                        </p>
                    </div>
                </body>
            </html>
            """
        }
        
        response = requests.post(api_url, json=payload, headers=headers, timeout=10)
        try:
            body_text = response.text
        except Exception:
            body_text = '<no body>'

        if response.status_code in (200, 201):
            current_app.logger.info('Activation email accepted by ZeptoMail (%s) for %s', response.status_code, email)
            current_app.logger.debug('ZeptoMail response: %s', body_text)
            return True
        else:
            current_app.logger.error('Error sending activation email: %s - %s', response.status_code, body_text)
            return False
            
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def send_password_reset_email(email, reset_link):
    """Send password reset link to user email"""
    try:
        api_url = current_app.config.get('ZEPTOMAIL_API_URL')
        api_key = current_app.config.get('ZEPTOMAIL_API_KEY')
        from_email = current_app.config.get('ZEPTOMAIL_FROM_EMAIL')

        if api_key:
            api_key = api_key.strip()

        if not api_key:
            current_app.logger.warning('ZeptoMail API key not configured')
            return False

        headers = {
            'Authorization': api_key,
            'Content-Type': 'application/json'
        }

        payload = {
            'from': {
                'address': from_email,
                'name': 'Ride India Rentals'
            },
            'to': [
                {
                    'email_address': {
                        'address': email
                    }
                }
            ],
            'subject': 'Reset your Ride India Rentals password',
            'htmlbody': f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #333;">Password reset requested</h2>
                        <p>Hello,</p>
                        <p>We received a request to reset the password associated with this email address. Click the button below to choose a new password.</p>
                        <p><strong>This link is valid for 15 minutes.</strong></p>
                        <p>If you did not request a password reset, you can safely ignore this email.</p>
                        <p style="margin: 20px 0;">
                            <a href="{reset_link}" style="background-color: #2196F3; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                                Reset password
                            </a>
                        </p>
                        <p style="font-size: 12px; color: #555; word-break: break-all;">
                            Or copy and paste this link into your browser:<br />
                            {reset_link}
                        </p>
                        <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                        <p style="color: #666; font-size: 12px;">
                            Ride India Rentals<br>
                            Email: support@rideindiarentals.com<br>
                            © 2025 All rights reserved.
                        </p>
                    </div>
                </body>
            </html>
            """
        }

        response = requests.post(api_url, json=payload, headers=headers, timeout=10)
        try:
            body_text = response.text
        except Exception:
            body_text = '<no body>'

        if response.status_code in (200, 201):
            current_app.logger.info('Password reset email accepted by ZeptoMail (%s) for %s', response.status_code, email)
            current_app.logger.debug('ZeptoMail response: %s', body_text)
            return True
        else:
            current_app.logger.error('Error sending password reset email: %s - %s', response.status_code, body_text)
            return False

    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False


def send_feedback_request(email, booking_id):
    """Send a feedback request email to the customer when booking is completed."""
    try:
        api_url = current_app.config.get('ZEPTOMAIL_API_URL')
        api_key = current_app.config.get('ZEPTOMAIL_API_KEY')
        from_email = current_app.config.get('ZEPTOMAIL_FROM_EMAIL')

        if api_key:
            api_key = api_key.strip()

        if not api_key:
            current_app.logger.warning('ZeptoMail API key not configured')
            return False

        headers = {
            'Authorization': api_key,
            'Content-Type': 'application/json'
        }

        feedback_url = current_app.config.get('FRONTEND_BASE_URL', '') + f"/bookings/{booking_id}/feedback"

        payload = {
            'from': {
                'address': from_email,
                'name': 'Ride India Rentals'
            },
            'to': [
                {
                    'email_address': {
                        'address': email
                    }
                }
            ],
            'subject': 'How was your ride? Please provide feedback',
            'htmlbody': f"""
            <html>
                <body>
                    <p>Hi,</p>
                    <p>Thank you for completing your booking. We'd love to know how your experience was.</p>
                    <p>Please click the link below to submit your feedback:</p>
                    <p><a href=\"{feedback_url}\">Leave feedback</a></p>
                    <p>Thanks,<br/>Ride India Rentals Team</p>
                </body>
            </html>
            """
        }

        response = requests.post(api_url, json=payload, headers=headers, timeout=10)
        try:
            body_text = response.text
        except Exception:
            body_text = '<no body>'

        if response.status_code in (200, 201):
            current_app.logger.info('Feedback request email accepted by ZeptoMail (%s) for %s', response.status_code, email)
            current_app.logger.debug('ZeptoMail response: %s', body_text)
            return True
        else:
            current_app.logger.error('Error sending feedback request email: %s - %s', response.status_code, body_text)
            return False
    except Exception as e:
        print(f"Error sending feedback email: {str(e)}")
        return False
