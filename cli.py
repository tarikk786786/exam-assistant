"""
Interactive CLI for University Exam Portal Assistant
"""

import sys
import getpass
from assistant import UniversityExamAssistant, DEFAULT_STUDENT_ID

def main():
    print("=" * 60)
    print("🎓 UNIVERSITY EXAM PORTAL ASSISTANT & STUDY SYSTEM")
    print("=" * 60)
    print("Student ID: ", DEFAULT_STUDENT_ID)
    print("Security Notice: Submissions & final answers are always user-controlled.")
    print("-" * 60)

    assistant = UniversityExamAssistant(headless=False)
    try:
        assistant.start()
        assistant.navigate_login(DEFAULT_STUDENT_ID)
        
        print("\n[Action Required] Please log in on the browser window.")
        logged_in = assistant.wait_for_dashboard(timeout_sec=180)
        
        if not logged_in:
            print("[!] Login timeout or window closed.")
            return

        print("\n--- Available Exams & Subjects ---")
        exams = assistant.list_available_exams()
        for idx, ex in enumerate(exams, 1):
            print(f"[{idx}] {ex['name']} | ID: {ex['subjectId']} | Status: {ex['status']} | Questions: {ex['questionCount']}")

        print("\nDashboard inspection complete.")
        input("\nPress Enter to exit session...")
    finally:
        assistant.close()

if __name__ == "__main__":
    main()
