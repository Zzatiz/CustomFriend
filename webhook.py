from flask import Flask, request
from datetime import datetime, timedelta
from models import User, Session
import stripe
import os
import logging
import json

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")

stripe.api_key = STRIPE_SECRET_KEY
stripe_webhook_secret = os.getenv("stripe_webhook_secret")

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)  # This will print logs to the console


@app.route('/stripe_webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Event.construct_from(
            json.loads(payload), stripe.api_key
        )

    except ValueError as e:
        # Invalid payload
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return 'Invalid signature', 400

    # Log the event type for debugging purposes
    logging.info(f"Received event: {event['type']}")

    handle_event(event)
    return '', 200


def extract_telegram_id_from_event(event):
    # Directly extract telegram_id from the event's metadata if present
    if 'metadata' in event['data']['object'] and 'telegram_id' in event['data']['object']['metadata']:
        return event['data']['object']['metadata']['telegram_id']

    # For charge events, try to find the metadata in related objects
    if event['type'].startswith('charge.'):
        charge = event['data']['object']

        # If charge is linked to an invoice, try retrieving telegram_id from the invoice
        if charge.get('invoice'):
            invoice = stripe.Invoice.retrieve(charge['invoice'])
            if 'telegram_id' in invoice['metadata']:
                return invoice['metadata']['telegram_id']

            # If the invoice is linked to a subscription, try retrieving telegram_id from the subscription
            if invoice.get('subscription'):
                subscription = stripe.Subscription.retrieve(invoice['subscription'])
                if 'telegram_id' in subscription['metadata']:
                    return subscription['metadata']['telegram_id']

    logging.warning("No telegram_id found in metadata or related entities.")
    return None




def handle_event(event):
    telegram_id = extract_telegram_id_from_event(event)
    
    # If we can't find the telegram_id from the event metadata, attempt to fetch from PaymentIntent
    if not telegram_id and 'charge' in event['data']['object']:
        try:
            charge = event['data']['object']
            payment_intent = stripe.PaymentIntent.retrieve(charge['payment_intent'])
            if 'metadata' in payment_intent and 'telegram_id' in payment_intent['metadata']:
                telegram_id = payment_intent['metadata']['telegram_id']
        except Exception as e:
            logging.error(f"Failed to fetch PaymentIntent for charge: {e}")

    if not telegram_id:
        logging.warning(f"Cannot process event of type {event['type']} due to missing telegram_id.")
        return '', 200

    if event['type'] == 'checkout.session.completed':
        handle_successful_session(event, telegram_id)

    elif event['type'] == 'charge.failed':
        handle_failed_payment(event, telegram_id)

    elif event['type'] == 'charge.dispute.created':
        handle_dispute(event, telegram_id)

    elif event['type'] == 'charge.refunded':
        handle_refund(event, telegram_id)

    elif event['type'] == 'charge.succeeded':
        logging.info(f"Received successful charge for telegram_id {telegram_id}")

    else:
        logging.warning(f"Received unhandled event type: {event['type']}")

    return '', 200


def handle_successful_session(event, telegram_id):
    with Session() as session:
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            user.subscription_status = 'active'
            user.subscribed_until = datetime.utcnow() + timedelta(days=30)  # Assuming a monthly subscription
            session.commit()
            print(f"User with telegram_id {telegram_id} subscription updated to active until {user.subscribed_until}")
        else:
            new_user = User(telegram_id=telegram_id, subscription_status='active', subscribed_until=datetime.utcnow() + timedelta(days=30))
            session.add(new_user)
            session.commit()
            print(f"New user with telegram_id {telegram_id} added with active subscription until {new_user.subscribed_until}")
            
    session = event['data']['object']
    
    # If the session resulted in a subscription, ensure it has the telegram_id metadata
    if session.get('subscription'):
        subscription_id = session['subscription']
        subscription = stripe.Subscription.retrieve(subscription_id)

        # Check if the metadata is not already present
        if 'telegram_id' not in subscription['metadata']:
            subscription.metadata['telegram_id'] = telegram_id
            subscription.save()

    # If the session resulted in a payment intent, ensure it has the telegram_id metadata
    if session.get('payment_intent'):
        payment_intent_id = session['payment_intent']
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        # Check if the metadata is not already present
        if 'telegram_id' not in payment_intent['metadata']:
            payment_intent.metadata['telegram_id'] = telegram_id
            payment_intent.save()
            
def handle_failed_payment(event, telegram_id):
    with Session() as session:
        try:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if user:
                user.subscription_status = 'inactive'
                session.commit()
                logging.info(f"User with telegram_id {telegram_id} subscription marked as inactive due to failed payment")
            else:
                logging.warning(f"No user found with telegram_id {telegram_id} to mark as inactive due to failed payment")
        except Exception as e:
            logging.error(f"Error processing failed payment for telegram_id {telegram_id}: {e}")
            
def handle_dispute(event, telegram_id):
    with Session() as session:
        try:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if user:
                user.subscription_status = 'inactive'
                session.commit()
                logging.info(f"User with telegram_id {telegram_id} subscription marked as inactive due to dispute")
            else:
                logging.warning(f"No user found with telegram_id {telegram_id} to mark as inactive due to dispute")
        except Exception as e:
            logging.error(f"Error processing dispute for telegram_id {telegram_id}: {e}")
            
def handle_refund(event, telegram_id):
    if not telegram_id:
        charge_id = event['data']['object']['id']
        charge = stripe.Charge.retrieve(charge_id)
        payment_intent = stripe.PaymentIntent.retrieve(charge.payment_intent)
        telegram_id = payment_intent.metadata.get('telegram_id')
    if not telegram_id:
        logging.warning(f"Cannot process event of type {event['type']} due to missing telegram_id.")
        return '', 200
    with Session() as session:
        try:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if user:
                user.subscription_status = 'inactive'
                session.commit()
                logging.info(f"User with telegram_id {telegram_id} subscription marked as inactive due to refund")
            else:
                logging.warning(f"No user found with telegram_id {telegram_id} to mark as inactive due to refund")
        except Exception as e:
            logging.error(f"Error processing refund for telegram_id {telegram_id}: {e}")

if __name__ == '__main__':
    app.run(port=5000)
