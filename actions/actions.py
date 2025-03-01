from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from .database_manager import DatabaseManager  # Updated import
from datetime import datetime, timedelta
from rasa_sdk.types import DomainDict
from rasa_sdk.forms import FormValidationAction


class ValidateRoomBookingForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_room_booking_form"

    def _is_valid_time(self, time_str: str) -> bool:
        """Validate time format HH:MM"""
        try:
            # Check if time string matches format
            datetime.strptime(time_str, "%H:%M")

            # Extract hours and minutes
            hours, minutes = map(int, time_str.split(":"))

            # Check if within business hours (8:00 - 22:00)
            if 8 <= hours < 22:
                return True
            return False
        except ValueError:
            return False

    def validate_time(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate time value."""
        if self._is_valid_time(slot_value):
            return {"time": slot_value}
        else:
            dispatcher.utter_message(template="utter_invalid_time_format")
            return {"time": None}

    def validate_date(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate date value."""
        try:
            # Validate date format
            input_date = datetime.strptime(slot_value, "%Y-%m-%d")
            today = datetime.now()

            # Check if date is not in the past
            if input_date.date() >= today.date():
                return {"date": slot_value}
            else:
                dispatcher.utter_message(text="Please select a future date.")
                return {"date": None}
        except ValueError:
            dispatcher.utter_message(template="utter_invalid_date_format")
            return {"date": None}

    def validate_duration(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate duration value."""
        try:
            duration = float(slot_value)
            if 0.5 <= duration <= 8:  # Between 30 minutes and 8 hours
                return {"duration": duration}
            else:
                dispatcher.utter_message(
                    text="Duration must be between 30 minutes (0.5) and 8 hours."
                )
                return {"duration": None}
        except ValueError:
            dispatcher.utter_message(
                text="Please provide a valid number for duration (e.g., 1.5 for 1.5 hours)"
            )
            return {"duration": None}

    def validate_number_of_people(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate number of people."""
        try:
            num_people = int(slot_value)
            if 1 <= num_people <= 50:  # Adjust max capacity as needed
                return {"number_of_people": num_people}
            else:
                dispatcher.utter_message(
                    text="Number of people must be between 1 and 50."
                )
                return {"number_of_people": None}
        except ValueError:
            dispatcher.utter_message(
                text="Please provide a valid number of people."
            )
            return {"number_of_people": None}

    def validate_contact_number(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate contact number."""
        # Simple validation for 10-digit number
        if slot_value.isdigit() and len(slot_value) == 10:
            return {"contact_number": slot_value}
        else:
            dispatcher.utter_message(
                text="Please provide a valid 10-digit contact number."
            )
            return {"contact_number": None}


class ActionCheckRoomAvailability(Action):
    def __init__(self):
        self.db = DatabaseManager()

    def name(self) -> Text:
        return "action_check_room_availability"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Get slots with None as default
        date = tracker.get_slot("date")
        time = tracker.get_slot("time")

        try:
            available_rooms = self.db.check_room_availability(date, time)

            if available_rooms:
                # Format the response based on provided parameters
                if date and time:
                    response = f"Available rooms for {date} at {time}:\n"
                elif date:
                    response = f"Available rooms for {date}:\n"
                else:
                    response = "Currently available rooms:\n"

                # Add room details
                for room in available_rooms:
                    response += (f"- {room[0]} (Capacity: {room[1]}, "
                                 f"Amenities: {room[2]}, Price: ${room[3]}/hr)\n")

                dispatcher.utter_message(text=response)
            else:
                if date and time:
                    response = f"No rooms available for {date} at {time}."
                elif date:
                    response = f"No rooms available for {date}."
                else:
                    response = "No rooms currently available."

                dispatcher.utter_message(text=response)

        except Exception as e:
            dispatcher.utter_message(
                text="Sorry, there was an error checking room availability.")
            print(f"Error checking room availability: {e}")

        return []


class ActionBookRoom(Action):
    def __init__(self):
        self.db = DatabaseManager()

    def name(self) -> Text:
        return "action_book_room"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        room_name = tracker.get_slot("room_name")
        date = tracker.get_slot("date")
        start_time = tracker.get_slot("time")
        duration = tracker.get_slot("duration")
        person_name = tracker.get_slot("person_name")

        start_datetime = datetime.strptime(
            f"{date} {start_time}", "%Y-%m-%d %H:%M")

        # Convert duration to hours and minutes
        duration_hours = float(duration)
        hours = int(duration_hours)
        minutes = int((duration_hours % 1) * 60)

        # Calculate end time
        end_datetime = start_datetime + timedelta(hours=hours, minutes=minutes)
        end_time = end_datetime.strftime("%H:%M")

        success = self.db.book_room(
            room_name, date, start_time, end_time, person_name
        )

        if success:
            response = f"Successfully booked {room_name} for {date} at {start_time}"
        else:
            response = f"Sorry, couldn't book {room_name}. Please try another room or time."

        dispatcher.utter_message(text=response)
        return []
