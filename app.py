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

from utils.logging import logger

app = Flask(__name__)
# Use environment variable for secret key in production, fallback for development
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')

# In-memory storage for demo purposes (use a database in production)
calendars = {}


def generate_calendar_code():
    """Generate a unique 6-character calendar code"""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if code not in calendars:
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
        user_name = request.form.get('user_name', '').strip()
        
        # Validate inputs
        if not calendar_code or len(calendar_code) != 6:
            return render_template("landing.html", error="Invalid calendar code. Please enter a 6-character code.")
        
        if not user_name:
            return render_template("landing.html", error="Name is required to join a calendar.")
        
        # Check if calendar exists (for now, accept any 6-character code)
        if calendar_code not in calendars:
            calendars[calendar_code] = {
                'title': f'Calendar {calendar_code}',
                'users': [],
                'availability': {},
                'user_availability': {}
            }
        
        # Add user to calendar
        if user_name not in calendars[calendar_code]['users']:
            calendars[calendar_code]['users'].append(user_name)
        
        # Store session data
        session['calendar_code'] = calendar_code
        session['user_name'] = user_name
        
        logger.info(f"User {user_name} joined calendar {calendar_code}")
        return redirect(url_for('calendar', code=calendar_code))
    
    elif action == 'create':
        creator_name = request.form.get('creator_name', '').strip()
        calendar_title = request.form.get('calendar_title', '').strip()
        
        if not creator_name:
            return render_template("landing.html", error="Name is required to create a calendar.")
        
        # Generate new calendar
        calendar_code = generate_calendar_code()
        calendars[calendar_code] = {
            'title': calendar_title or f'Calendar {calendar_code}',
            'users': [creator_name],
            'availability': {},
            'user_availability': {}
        }
        
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
    
    if code not in calendars:
        return redirect(url_for('landing'))
    
    # Use basic logging with custom fields
    logger.info(logField="custom-entry", arbitraryField="custom-entry")

    # https://cloud.google.com/run/docs/logging#correlate-logs
    logger.info("Child logger with trace Id.")

    return render_template("index.html", 
                         calendar_code=code,
                         calendar_title=calendars[code]['title'],
                         user_name=session.get('user_name', 'Guest'))


@app.route("/created/<code>")
def calendar_created(code):
    """Calendar creation success page"""
    code = code.upper()
    
    if code not in calendars:
        return redirect(url_for('landing'))
    
    return render_template("calendar_created.html", 
                         calendar_code=code,
                         calendar_title=calendars[code]['title'],
                         user_name=session.get('user_name', 'Guest'))


@app.route("/submit_availability", methods=["POST"])
def submit_availability():
    """Handle availability submission"""
    try:
        data = request.get_json()
        calendar_code = data.get('calendar_code', '').upper()
        user_name = data.get('user_name', '')
        availability = data.get('availability', {})
        
        # Validate inputs
        if not calendar_code or calendar_code not in calendars:
            return jsonify({'success': False, 'error': 'Invalid calendar code'})
        
        if not user_name:
            return jsonify({'success': False, 'error': 'User name is required'})
        
        # Store availability data
        if 'user_availability' not in calendars[calendar_code]:
            calendars[calendar_code]['user_availability'] = {}
        
        calendars[calendar_code]['user_availability'][user_name] = availability
        
        logger.info(f"Availability submitted for {user_name} in calendar {calendar_code}")
        
        return jsonify({'success': True, 'message': 'Availability submitted successfully'})
        
    except Exception as e:
        logger.error(f"Error submitting availability: {str(e)}")
        return jsonify({'success': False, 'error': 'Server error occurred'})


@app.route("/view_availability/<code>")
def view_availability(code):
    """View all submitted availability for a calendar"""
    code = code.upper()
    
    if code not in calendars:
        return redirect(url_for('landing'))
    
    calendar_data = calendars[code]
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
