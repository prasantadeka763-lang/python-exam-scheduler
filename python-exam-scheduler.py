import json
import os
from datetime import datetime

# Configuration
DATA_FILE = "student_exam_schedule.json"

class Exam:
    """Represents a single exam event."""
    def __init__(self, subject: str, exam_date: str, start_time: str, duration_mins: int, room: str):
        self.subject = subject.strip().upper()
        self.exam_date = exam_date.strip()  # YYYY-MM-DD
        self.start_time = start_time.strip()  # HH:MM (24-hour format)
        self.duration_mins = int(duration_mins)
        self.room = room.strip().upper()

    def to_dict(self):
        """Converts the class properties to a dictionary for JSON conversion."""
        return {
            "subject": self.subject,
            "exam_date": self.exam_date,
            "start_time": self.start_time,
            "duration_mins": self.duration_mins,
            "room": self.room
        }

    def get_datetime_object(self):
        """Returns a datetime object for comparison logic."""
        return datetime.strptime(f"{self.exam_date} {self.start_time}", "%Y-%m-%d %H:%M")

    def get_days_remaining(self) -> int:
        """Calculates days left until this exam."""
        exam_dt = self.get_datetime_object()
        today = datetime.now()
        delta = exam_dt - today
        return delta.days + 1 if delta.days >= 0 else delta.days


class RoutineManager:
    """Manages the full collection of exams, validation rules, and operations."""
    def __init__(self):
        self.exams = []
        self.load_data()

    def load_data(self):
        """Loads data from the JSON file safely."""
        if not os.path.exists(DATA_FILE):
            self.exams = []
            return

        try:
            with open(DATA_FILE, "r") as file:
                raw_data = json.load(file)
                self.exams = [Exam(**item) for item in raw_data]
        except (json.JSONDecodeError, KeyError, TypeError):
            print("⚠️ Data file corrupt or unreadable. Initializing fresh routine.")
            self.exams = []

    def save_data(self):
        """Saves current memory registry state to disk."""
        try:
            with open(DATA_FILE, "w") as file:
                json.dump([exam.to_dict() for exam in self.exams], file, indent=4)
        except IOError as e:
            print(f"❌ Failed to write schedule to local file registry: {e}")

    def sort_exams(self):
        """Sorts exams sequentially by date and start times."""
        self.exams.sort(key=lambda x: x.get_datetime_object())

    def check_time_collision(self, new_date: str, new_time: str, new_duration: int) -> bool:
        """Helper to ensure two exams aren't scheduled at the exact same hour."""
        new_start = datetime.strptime(f"{new_date} {new_time}", "%Y-%m-%d %H:%M")
        new_end = new_start.replace(minute=new_start.minute + new_duration)

        for exam in self.exams:
            exist_start = exam.get_datetime_object()
            exist_end = exist_start.replace(minute=exist_start.minute + exam.duration_mins)
            
            # Intersection checker logic
            if max(new_start, exist_start) < min(new_end, exist_end):
                return True
        return False

    def add_exam(self):
        print("\n=== ➕ SCHEDULE A NEW EXAM ===")
        subject = input("Enter Subject/Course Code: ").strip()
        if not subject:
            print("❌ Invalid input: Subject cannot be blank.")
            return

        # Double subject check
        if any(e.subject == subject.upper() for e in self.exams):
            print(f"❌ An exam for '{subject.upper()}' is already scheduled.")
            return

        # Validate Date format
        date_str = input("Enter Exam Date (YYYY-MM-DD): ").strip()
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            print("❌ Incorrect format: Must use YYYY-MM-DD.")
            return

        # Validate Time format
        time_str = input("Enter Start Time (24h clock, e.g., 09:30 or 14:00): ").strip()
        try:
            datetime.strptime(time_str, "%H:%M")
        except ValueError:
            print("❌ Incorrect format: Must use military 24h format (HH:MM).")
            return

        # Validate Duration integers
        try:
            duration = int(input("Enter Exam Duration (in total minutes): "))
            if duration <= 0: raise ValueError
        except ValueError:
            print("❌ Invalid entry: Minutes must be a positive whole number.")
            return

        room = input("Enter Hall/Room Number: ").strip()
        if not room:
            room = "UNASSIGNED HALL"

        # Check for timing overlaps/collisions
        if self.check_time_collision(date_str, time_str, duration):
            print("⚠️ TIMING WARNING: This duration overlaps with an existing exam schedule!")
            confirm = input("Override and save anyway? (y/n): ").strip().lower()
            if confirm != 'y':
                print("❌ Exam insertion cancelled.")
                return

        # Build objects and append
        new_exam = Exam(subject, date_str, time_str, duration, room)
        self.exams.append(new_exam)
        self.sort_exams()
        self.save_data()
        print(f"✅ Exam routine configured successfully for {new_exam.subject}!")

    def display_routine(self):
        print("\n" + "="*85)
        print(f"{'📆 MASTER EXAM ROUTINE DASHBOARD':^85}")
        print("="*85)

        if not self.exams:
            print(f"{'No exam schedules recorded in database registry. Check back later.':^85}")
            print("="*85)
            return

        self.sort_exams()
        # Table Header
        print(f"{'SUBJECT':<15} | {'DATE':<12} | {'START':<8} | {'MINS':<6} | {'ROOM/HALL':<15} | {'STATUS / COUNTDOWN'}")
        print("-" * 85)

        for exam in self.exams:
            days = exam.get_days_remaining()
            if days < 0:
                status_str = f"🛑 Completed ({abs(days)} days ago)"
            elif days == 0:
                status_str = "🔥 HAPPENING TODAY!"
            elif days == 1:
                status_str = "⏳ Tomorrow!"
            else:
                status_str = f"⏳ {days} Days Left"

            print(f"{exam.subject:<15} | {exam.exam_date:<12} | {exam.start_time:<8} | {exam.duration_mins:<6} | {exam.room:<15} | {status_str}")
        print("="*85)

    def search_exam(self):
        print("\n=== 🔍 SEARCH TRANSACTION LOGS ===")
        query = input("Search by Subject name: ").strip().upper()
        
        matches = [e for e in self.exams if query in e.subject]
        
        if not matches:
            print(f"❌ No registered exam rows match query: '{query}'")
            return
            
        print(f"\nFound {len(matches)} matching entries:")
        for index, exam in enumerate(matches, 1):
            print(f"\n[{index}] --- {exam.subject} ---")
            print(f" 📅 Date & Time : {exam.exam_date} at {exam.start_time} ({exam.duration_mins} mins)")
            print(f" 📍 Location    : Room/Hall {exam.room}")
            print(f" ⏱️ Countdown   : {exam.get_days_remaining()} Day(s)")

    def delete_exam(self):
        print("\n=== 🗑️ REMOVE EXAM ROUTINE ===")
        subject = input("Enter precise Subject Name to erase: ").strip().upper()
        
        target = None
        for exam in self.exams:
            if exam.subject == subject:
                target = exam
                break

        if target:
            print(f"⚠️ Target identified: {target.subject} set for {target.exam_date}.")
            confirm = input("Confirm permanent deletion? (type 'YES'): ").strip()
            if confirm == "YES":
                self.exams.remove(target)
                self.save_data()
                print(f"🗑️ Cleaned record for {subject} from working memory registry.")
            else:
                print("❌ Deletion process aborted.")
        else:
            print(f"❌ Subject '{subject}' is not found within active routine records.")


def clear_console():
    """Wipes active viewport shell logs."""
    os.system('cls' if os.name == 'nt' else 'clear')


def main():
    """Primary thread execution orchestration engine loop."""
    manager = RoutineManager()
    
    while True:
        print("\n" + "╔" + "═"*40 + "╗")
        print("║      🎓 EXAM MANAGEMENT TERMINAL       ║")
        print("╠" + "═"*40 + "╣")
        print("║  [1] 📋 View Master Exam Routine      ║")
        print("║  [2] ➕ Add or Update Exam Entry      ║")
        print("║  [3] 🔍 Search Exam Schedules         ║")
        print("║  [4] 🗑️ Erase Exam Record             ║")
        print("║  [5] 🚪 Terminate Workspace Execution ║")
        print("╚" + "═"*40 + "╝")
        
        choice = input("Select System Operations Core Engine Route (1-5): ").strip()
        
        if choice == '1':
            manager.display_routine()
        elif choice == '2':
            manager.add_exam()
        elif choice == '3':
            manager.search_exam()
        elif choice == '4':
            manager.delete_exam()
        elif choice == '5':
            print("\n🔐 Flushing temporary array frames to disk storage module...")
            print("👋 Session terminated successfully. Good luck preparing for tests!")
            break
        else:
            print("❌ Operator error: Option code range exception. Try input values 1 to 5.")
            
        input("\nPress [Enter] key to recycle console loop pipeline...")
        clear_console()


if __name__ == "__main__":
    main()
