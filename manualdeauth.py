from models import User, Session

def deactivate_subscription(telegram_id):
    telegram_id_str = str(telegram_id)  # Convert the telegram_id to a string
    with Session() as session:
        user = session.query(User).filter(User.telegram_id == telegram_id_str).first()
        if user and user.subscription_status == 'active':
            user.subscription_status = 'inactive'
            session.commit()
            print(f"User with telegram_id {telegram_id} subscription has been deactivated manually.")
        else:
            print(f"User with telegram_id {telegram_id} not found or is already inactive.")

# Call the function
telegram_id_to_deactivate = 6152661939  # replace with the actual telegram_id
deactivate_subscription(telegram_id_to_deactivate)
