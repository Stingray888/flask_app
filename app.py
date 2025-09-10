# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import signal
import sys
from types import FrameType
import random
import string
import os

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from google.cloud import firestore

from utils.logging import logger

app = Flask(__name__)
# Use environment variable for secret key in production, fallback for development
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')

# Initialize Firestore client
db = firestore.Client()

# Database helper functions
def get_calendar(code):
    """Get calendar data from Firestore"""
    doc_ref = db.collection('calendars').document(code)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    return None

def save_calendar(code, data):
    """Save calendar data to Firestore"""
    doc_ref = db.collection('calendars').document(code)
    doc_ref.set(data)

def update_calendar(code, updates):
    """Update specific fields in calendar"""
    doc_ref = db.collection('calendars').document(code)
    doc_ref.update(updates)

def calendar_exists(code):
    """Check if calendar exists in Firestore"""
    return get_calendar(code) is not None


def generate_calendar_code():
    """Generate a unique 6-character calendar code"""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not calendar_exists(code):
            return code


@app.route("/")
def landing():
    """Landing page where users can join or create a calendar"""
    return render_template("landing.html")


@app.route("/", methods=["POST"])
def handle_landing():
    """Handle form submission from landing page"""
    action = request.form.get('action')
    
    if action == 'join':
        calendar_code = request.form.get('calendar_code', '').strip().upper()
        user_name = request.form.get('user_name', '').strip().upper()
        
        # Validate inputs
        if not calendar_code or len(calendar_code) != 6:
            return render_template("landing.html", error="Invalid calendar code. Please enter a 6-character code.")
        
        if not user_name:
            return render_template("landing.html", error="Name is required to join a calendar.")
        
        # Check if calendar exists, create if it doesn't
        calendar_data = get_calendar(calendar_code)
        if not calendar_data:
            calendar_data = {
                'title': f'Calendar {calendar_code}',
                'users': [],
                'availability': {},
                'user_availability': {}
            }
            save_calendar(calendar_code, calendar_data)
        
        # Add user to calendar if not already there
        if user_name not in calendar_data['users']:
            calendar_data['users'].append(user_name)
            update_calendar(calendar_code, {'users': calendar_data['users']})
        
        # Store session data
        session['calendar_code'] = calendar_code
        session['user_name'] = user_name
        
        logger.info(f"User {user_name} joined calendar {calendar_code}")
        
        # Check if user has existing availability data
        user_availability = calendar_data.get('user_availability', {})
        if user_name in user_availability:
            # User exists with previous availability - redirect to calendar to update
            logger.info(f"Existing user {user_name} rejoining calendar {calendar_code} to update availability")
        
        return redirect(url_for('calendar', code=calendar_code))
    
    elif action == 'create':
        creator_name = request.form.get('creator_name', '').strip().upper()
        calendar_title = request.form.get('calendar_title', '').strip()
        
        if not creator_name:
            return render_template("landing.html", error="Name is required to create a calendar.")
        
        # Generate new calendar
        calendar_code = generate_calendar_code()
        calendar_data = {
            'title': calendar_title or f'Calendar {calendar_code}',
            'users': [creator_name],
            'availability': {},
            'user_availability': {}
        }
        save_calendar(calendar_code, calendar_data)
        
        # Store session data
        session['calendar_code'] = calendar_code
        session['user_name'] = creator_name
        
        logger.info(f"New calendar {calendar_code} created by {creator_name}")
        return redirect(url_for('calendar_created', code=calendar_code))
    
    return render_template("landing.html", error="Invalid action. Please select an option.")


@app.route("/calendar/<code>")
def calendar(code):
    """Main calendar page"""
    code = code.upper()
    
    calendar_data = get_calendar(code)
    if not calendar_data:
        return redirect(url_for('landing'))
    
    # Get current user's existing availability
    user_name = session.get('user_name', 'Guest')
    user_availability = calendar_data.get('user_availability', {}).get(user_name, {})
    
    # Use basic logging with custom fields
    logger.info(logField="custom-entry", arbitraryField="custom-entry")

    # https://cloud.google.com/run/docs/logging#correlate-logs
    logger.info("Child logger with trace Id.")

    return render_template("calendar_edit.html", 
                         calendar_code=code,
                         calendar_title=calendar_data['title'],
                         user_name=user_name,
                         existing_availability=user_availability)


@app.route("/created/<code>")
def calendar_created(code):
    """Calendar creation success page"""
    code = code.upper()
    
    calendar_data = get_calendar(code)
    if not calendar_data:
        return redirect(url_for('landing'))
    
    return render_template("calendar_created.html", 
                         calendar_code=code,
                         calendar_title=calendar_data['title'],
                         user_name=session.get('user_name', 'Guest'))


@app.route("/submit_availability", methods=["POST"])
def submit_availability():
    """Handle availability submission"""
    try:
        data = request.get_json()
        calendar_code = data.get('calendar_code', '').upper()
        user_name = data.get('user_name', '').upper()
        availability = data.get('availability', {})
        
        # Validate inputs
        calendar_data = get_calendar(calendar_code)
        if not calendar_code or not calendar_data:
            return jsonify({'success': False, 'error': 'Invalid calendar code'})
        
        if not user_name:
            return jsonify({'success': False, 'error': 'User name is required'})
        
        # Store availability data
        if 'user_availability' not in calendar_data:
            calendar_data['user_availability'] = {}
        
        calendar_data['user_availability'][user_name] = availability
        
        # Update the calendar in Firestore
        update_calendar(calendar_code, {'user_availability': calendar_data['user_availability']})
        
        logger.info(f"Availability submitted for {user_name} in calendar {calendar_code}")
        
        return jsonify({'success': True, 'message': 'Availability submitted successfully'})
        
    except Exception as e:
        logger.error(f"Error submitting availability: {str(e)}")
        return jsonify({'success': False, 'error': 'Server error occurred'})


@app.route("/debug/<code>")
def debug_calendar(code):
    """Debug route to see raw calendar data"""
    code = code.upper()
    
    calendar_data = get_calendar(code)
    if not calendar_data:
        return jsonify({'error': 'Calendar not found'})
    
    return jsonify({
        'calendar_code': code,
        'calendar_data': calendar_data,
        'user_availability': calendar_data.get('user_availability', {}),
        'users': calendar_data.get('users', [])
    })


@app.route("/view_availability/<code>")
def view_availability(code):
    """View all submitted availability for a calendar"""
    code = code.upper()
    
    calendar_data = get_calendar(code)
    if not calendar_data:
        return redirect(url_for('landing'))
    
    user_availability = calendar_data.get('user_availability', {})
    
    return render_template("view_availability.html",
                         calendar_code=code,
                         calendar_title=calendar_data['title'],
                         user_availability=user_availability,
                         users=calendar_data['users'])


def shutdown_handler(signal_int: int, frame: FrameType) -> None:
    logger.info(f"Caught Signal {signal.strsignal(signal_int)}")

    from utils.logging import flush

    flush()

    # Safely exit program
    sys.exit(0)


if __name__ == "__main__":
    # Running application locally, outside of a Google Cloud Environment
    
    # handles Ctrl-C termination
    signal.signal(signal.SIGINT, shutdown_handler)

    port = int(os.environ.get('PORT', 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
else:
    # handles Cloud Run container termination
    signal.signal(signal.SIGTERM, shutdown_handler)
