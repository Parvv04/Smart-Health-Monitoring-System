# break_reminder.py
import time

class BreakReminder:
    def __init__(self, break_interval=1*60):  
        """
        break_interval: seconds between reminders. Default = 20 minutes.
        """
        self.break_interval = break_interval
        self.last_break_time = time.time()

    def process(self):
        """
        Returns a break reminder string once the interval has passed.
        Otherwise returns None.
        """
        current_time = time.time()

        if current_time - self.last_break_time >= self.break_interval:
            self.last_break_time = current_time  # reset timer
            return "BREAK: Take a 20-second eye rest (20-20-20 Rule)."

        return None
