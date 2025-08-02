#!/usr/bin/env python3
"""
Diagnostic script to analyze why owner calendar events are not being created.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import get_db, User, UserRole, Meeting
from datetime import datetime, timedelta
import json

def analyze_owner_calendar_setup():
    """Analyze owner calendar configuration and issues."""
    with get_db() as db:
        print("=" * 60)
        print("OWNER CALENDAR DIAGNOSTIC ANALYSIS")
        print("=" * 60)
        
        # 1. Check owners
        owners = db.query(User).filter(User.role == UserRole.OWNER).all()
        print(f"\n1. OWNER ACCOUNTS ({len(owners)} found):")
        for owner in owners:
            print(f"\n   Owner: {owner.first_name} {owner.last_name}")
            print(f"   - Email: '{owner.email}'")
            print(f"   - Google Calendar ID: {owner.google_calendar_id}")
            print(f"   - Has OAuth credentials: {bool(owner.oauth_credentials)}")
            print(f"   - Calendar connected flag: {owner.calendar_connected}")
            
            # Check email validity
            if owner.email and owner.email == "Я назначил":
                print(f"   ⚠️  ISSUE: Invalid email value (Russian text instead of email)")
            
        # 2. Check managers
        managers = db.query(User).filter(User.role == UserRole.MANAGER).all()
        print(f"\n\n2. MANAGER ACCOUNTS ({len(managers)} found):")
        for manager in managers:
            print(f"\n   Manager: {manager.first_name} {manager.last_name}")
            print(f"   - Email: {manager.email}")
            print(f"   - Google Calendar ID: {manager.google_calendar_id}")
            print(f"   - Has OAuth credentials: {bool(manager.oauth_credentials)}")
            print(f"   - Calendar connected flag: {manager.calendar_connected}")
        
        # 3. Check recent meetings
        recent_meetings = db.query(Meeting).order_by(Meeting.created_at.desc()).limit(5).all()
        print(f"\n\n3. RECENT MEETINGS ({len(recent_meetings)} found):")
        for meeting in recent_meetings:
            manager = db.query(User).filter(User.id == meeting.manager_id).first()
            print(f"\n   Meeting ID: {meeting.id}")
            print(f"   - Scheduled: {meeting.scheduled_time}")
            print(f"   - Manager: {manager.first_name if manager else 'Unknown'}")
            print(f"   - Google Event ID: {meeting.google_event_id}")
            print(f"   - Manager Event ID: {meeting.google_manager_event_id}")
            print(f"   - Owner Event ID: {meeting.google_owner_event_id}")
            print(f"   - Calendar used: {meeting.google_calendar_id}")
            
            # Analyze dual calendar creation
            if meeting.google_manager_event_id and not meeting.google_owner_event_id:
                print(f"   ⚠️  ISSUE: Manager event created but NO owner event")
            elif meeting.google_owner_event_id and meeting.google_manager_event_id:
                print(f"   ✅ SUCCESS: Both calendar events created")
            
        # 4. Analyze the issue
        print("\n\n4. ROOT CAUSE ANALYSIS:")
        print("=" * 60)
        
        # Check owner calendar setup
        owners_with_valid_calendar = []
        for owner in owners:
            if owner.google_calendar_id and owner.oauth_credentials:
                # Check if email is valid
                if owner.email and "@" in str(owner.email):
                    owners_with_valid_calendar.append(owner)
                else:
                    print(f"\n❌ Owner {owner.first_name} has calendar but INVALID email: '{owner.email}'")
                    print("   - This prevents adding the owner as an attendee")
                    print("   - The invalid email may be blocking calendar event creation")
        
        if not owners_with_valid_calendar:
            print("\n❌ NO OWNERS have properly configured calendars with valid emails")
            print("   - Owner calendar events cannot be created without valid email addresses")
        
        # Check meeting service logic
        print("\n\n5. MEETING SERVICE LOGIC ANALYSIS:")
        print("=" * 60)
        print("\nBased on meeting_service.py code review:")
        print("1. Line 104-106: Gets primary owner for calendar creation")
        print("2. Line 111-116: Validates owner email - filters out invalid emails")
        print("3. Line 117-119: Sets owner_calendar_id only if owner has google_calendar_id")
        print("4. Line 117: The condition for creating in owner's calendar is:")
        print("   - owner_calendar_id must be set (line 117)")
        print("   - owner_calendar_id must be different from manager_calendar_id")
        print("\n⚠️  CRITICAL ISSUE FOUND:")
        print("   The owner has invalid email 'Я назначил' which fails validation")
        print("   This causes owner_email to be set to None (line 116)")
        print("   But the calendar creation still proceeds if owner has google_calendar_id")
        
        # 6. Recommendations
        print("\n\n6. RECOMMENDATIONS TO FIX:")
        print("=" * 60)
        print("\n1. Update owner's email to a valid email address:")
        print("   - Currently: 'Я назначил' (Russian text)")
        print("   - Should be: A valid email like 'owner@example.com'")
        print("\n2. Ensure calendar_connected flag is True for active calendars")
        print("\n3. The owner's google_calendar_id is set correctly to: plantatorbob@gmail.com")
        print("   - This should work once the email is fixed")
        
        # 7. SQL commands to fix
        print("\n\n7. SQL COMMANDS TO FIX THE ISSUE:")
        print("=" * 60)
        for owner in owners:
            if owner.email == "Я назначил":
                print(f"\n-- Fix owner email (replace with actual email):")
                print(f"UPDATE users SET email = 'plantatorbob@gmail.com' WHERE id = {owner.id};")
                print(f"UPDATE users SET calendar_connected = true WHERE id = {owner.id};")

if __name__ == "__main__":
    analyze_owner_calendar_setup()