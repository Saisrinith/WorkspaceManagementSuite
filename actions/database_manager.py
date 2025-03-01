import sqlite3
from typing import List, Tuple, Optional
from datetime import datetime

class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect(':memory:', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.setup_database()

    def setup_database(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS workspace (
            id INTEGER PRIMARY KEY,
            room_name TEXT,
            capacity INTEGER,
            status TEXT,
            booking_date DATE,
            start_time TIME,
            end_time TIME,
            booked_by TEXT,
            room_type TEXT,
            floor_number INTEGER,
            amenities TEXT,
            last_cleaned DATETIME,
            maintenance_status TEXT,
            price_per_hour DECIMAL(10,2)
        )
        ''')
        self._insert_sample_data()

    def _insert_sample_data(self):
        sample_data = [
                    # Standard Available Rooms
            ('Conference Room A', 20, 'available', None, None, None, None, 
            'conference', 1, 'projector,whiteboard,video_conf', '2024-01-19 18:00', 'good', 50.00),
            
            ('Meeting Room B', 8, 'available', None, None, None, None, 
            'meeting', 2, 'whiteboard,tv', '2024-01-19 17:00', 'good', 30.00),
            
            # Currently Booked Rooms
            ('Board Room', 15, 'booked', '2024-01-20', '09:00', '17:00', 'John Smith',
            'board', 3, 'projector,whiteboard,catering', '2024-01-19 18:00', 'good', 75.00),
            
            ('Training Room', 30, 'booked', '2024-01-20', '14:00', '16:00', 'HR Department',
            'training', 1, 'projector,laptops,whiteboard', '2024-01-19 15:00', 'good', 100.00),
            
            # Under Maintenance
            ('Meeting Room C', 10, 'maintenance', None, None, None, None,
            'meeting', 2, 'whiteboard,tv', '2024-01-18 09:00', 'under_repair', 35.00),
            
            # High Capacity Rooms
            ('Auditorium', 100, 'available', None, None, None, None,
            'conference', 1, 'projector,sound_system,stage', '2024-01-19 20:00', 'good', 200.00),
            
            # Small Rooms
            ('Focus Room 1', 4, 'available', None, None, None, None,
            'focus', 3, 'whiteboard', '2024-01-19 16:00', 'good', 20.00),
            
            # Partially Booked (Morning)
            ('Team Space 1', 12, 'booked', '2024-01-20', '09:00', '13:00', 'Team Alpha',
            'team', 2, 'tv,whiteboard', '2024-01-19 18:00', 'good', 45.00),
            
            # Special Equipment
            ('Video Conference Room', 15, 'available', None, None, None, None,
            'conference', 4, 'video_conf,tv,sound_system', '2024-01-19 17:00', 'good', 80.00),
            
            # Multiple Day Booking
            ('Event Space', 50, 'booked', '2024-01-20', '09:00', '18:00', 'Conference Organizers',
            'event', 1, 'projector,sound_system,catering', '2024-01-19 20:00', 'good', 150.00),
            
            # Needs Cleaning
            ('Quick Meet 1', 6, 'available', None, None, None, None,
            'meeting', 3, 'whiteboard', '2024-01-17 18:00', 'needs_cleaning', 25.00),
            
            # Weekend Availability
            ('Weekend Space', 25, 'available', None, None, None, None,
            'multipurpose', 2, 'projector,whiteboard', '2024-01-19 18:00', 'good', 65.00),
            
            # Late Hours Booking
            ('Night Room', 10, 'booked', '2024-01-20', '18:00', '22:00', 'Night Team',
            'meeting', 4, 'whiteboard,tv', '2024-01-19 17:00', 'good', 40.00),
            
            # Special Purpose Room
            ('Innovation Lab', 20, 'available', None, None, None, None,
            'lab', 2, 'smartboard,3d_printer,computers', '2024-01-19 18:00', 'good', 90.00),
            
            # Budget Option
            ('Basic Room 1', 8, 'available', None, None, None, None,
            'basic', 1, 'whiteboard', '2024-01-19 17:00', 'good', 15.00),
            
            # Premium Option
            ('Executive Suite', 12, 'available', None, None, None, None,
            'executive', 5, 'projector,video_conf,catering,bar', '2024-01-19 18:00', 'good', 120.00),
            
            # Partially Maintained
            ('Flexible Space 1', 15, 'partial_maintenance', None, None, None, None,
            'flexible', 3, 'movable_walls,whiteboard', '2024-01-19 12:00', 'partial_repair', 45.00),
            
            # Short Duration Booking
            ('Quick Meet 2', 4, 'booked', '2024-01-20', '10:00', '11:00', 'Quick Team',
            'focus', 2, 'whiteboard', '2024-01-19 17:00', 'good', 20.00),
            
            # Long Duration Booking
            ('Workshop Room', 40, 'booked', '2024-01-20', '09:00', '20:00', 'Workshop Group',
            'workshop', 1, 'projector,tables,tools', '2024-01-19 18:00', 'good', 85.00),
            
            # Emergency Maintenance
            ('Crisis Room', 15, 'maintenance', None, None, None, None,
            'emergency', 1, 'video_conf,phones,screens', '2024-01-19 10:00', 'emergency_repair', 60.00)
        ]
        
        self.cursor.executemany('''
        INSERT OR IGNORE INTO workspace (
            room_name, capacity, status, booking_date, start_time, end_time,
            booked_by, room_type, floor_number, amenities, last_cleaned,
            maintenance_status, price_per_hour
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_data)
        self.conn.commit()

    def check_room_availability(self, date: str = None, time: str = None) -> List[Tuple]:
        """
        Check room availability with optional date and time filters
        """
        try:
            # Start with base query
            query = '''
            SELECT room_name, capacity, amenities, price_per_hour
            FROM workspace
            WHERE status = 'available'
            AND maintenance_status = 'good'
            '''
            params = []

            # Add date and time conditions if provided
            if date and time:
                query += '''
                AND (booking_date != ? OR booking_date IS NULL)
                AND (
                    start_time > ? OR end_time < ?
                    OR (start_time IS NULL AND end_time IS NULL)
                )
                '''
                params.extend([date, time, time])
            elif date:
                query += '''
                AND (booking_date != ? OR booking_date IS NULL)
                '''
                params.append(date)

            # Add ordering
            query += '''
            ORDER BY capacity, price_per_hour
            '''

            # Execute query with or without parameters
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)

            return self.cursor.fetchall()

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []
        except Exception as e:
            print(f"Error: {e}")
            return []

    def validate_datetime(self, date: str = None, time: str = None) -> bool:
        """
        Validate date and time formats
        """
        try:
            if date:
                datetime.strptime(date, '%Y-%M-%D')
            if time:
                datetime.strptime(time, '%H:%M')
            return True
        except ValueError:
            return False

    def book_room(self, room_name: str, date: str, start_time: str, 
                 end_time: str, booked_by: str) -> bool:
        try:
            self.cursor.execute('''
            UPDATE workspace
            SET status = 'booked',
                booking_date = ?,
                start_time = ?,
                end_time = ?,
                booked_by = ?
            WHERE room_name = ?
            AND status = 'available'
            ''', (date, start_time, end_time, booked_by, room_name))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Booking error: {e}")
            return False

    def __del__(self):
        self.conn.close()