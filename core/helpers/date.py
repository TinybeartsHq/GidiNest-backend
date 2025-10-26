from datetime import datetime, timedelta


def get_start_end_date():
    # Define the start date as tomorrow
    start_date = datetime.now() + timedelta(days=1)

    # Compute the end date as one year from the start date
    end_date = start_date + timedelta(days=365)

    # Format the dates as strings
    start_date_str = start_date.strftime("%d %B %Y")
    end_date_str = end_date.strftime("%d %B %Y")

    return start_date_str, end_date_str



def get_age_from_date(birth_date_str):
    try:
        # Convert the birth date string to a datetime object
        birth_date = datetime.strptime(birth_date_str, "%d/%m/%Y")

        # Get the current date
        current_date = datetime.now()

        # Calculate the age
        age = current_date.year - birth_date.year - ((current_date.month, current_date.day) < (birth_date.month, birth_date.day))
        
        return age

    except:
        return None

    