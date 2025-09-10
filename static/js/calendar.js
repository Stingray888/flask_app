// Store availability data
let availabilityData = {};

// Current calendar state
let currentCalendarMonth = new Date().getMonth();
let currentCalendarYear = new Date().getFullYear();

// Initialize with existing availability data if provided
function initializeAvailability(existingData) {
    if (existingData && typeof existingData === 'object') {
        availabilityData = { ...existingData };
        console.log('Loaded existing availability:', availabilityData);
    }
}

function generateCalendar() {
    const today = new Date();
    const todayMonth = today.getMonth();
    const todayYear = today.getFullYear();
    const todayDate = today.getDate();

    // Set month and year header
    const monthNames = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ];
    document.getElementById('monthYear').textContent = 
        `${monthNames[currentCalendarMonth]} ${currentCalendarYear}`;

    // Update navigation button states
    updateNavigationButtons();

    // Get first day of the month and number of days
    const firstDayOfMonth = new Date(currentCalendarYear, currentCalendarMonth, 1);
    const lastDayOfMonth = new Date(currentCalendarYear, currentCalendarMonth + 1, 0);
    const firstDayWeekday = firstDayOfMonth.getDay();
    const daysInMonth = lastDayOfMonth.getDate();

    // Get last month's last few days
    const lastDayOfPrevMonth = new Date(currentCalendarYear, currentCalendarMonth, 0).getDate();

    const calendarGrid = document.getElementById('calendarGrid');
    calendarGrid.innerHTML = '';

    // Add day headers
    const dayHeaders = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    dayHeaders.forEach(day => {
        const dayHeader = document.createElement('div');
        dayHeader.className = 'calendar-day-header';
        dayHeader.textContent = day;
        calendarGrid.appendChild(dayHeader);
    });

    // Add previous month's trailing days
    for (let i = firstDayWeekday - 1; i >= 0; i--) {
        const dayElement = document.createElement('div');
        dayElement.className = 'calendar-day other-month';
        dayElement.textContent = lastDayOfPrevMonth - i;
        calendarGrid.appendChild(dayElement);
    }

    // Add current month's days
    for (let day = 1; day <= daysInMonth; day++) {
        const dayElement = document.createElement('div');
        dayElement.className = 'calendar-day';
        dayElement.textContent = day;
        
        // Create date key for availability tracking
        const dateKey = `${currentCalendarYear}-${currentCalendarMonth + 1}-${day}`;
        dayElement.setAttribute('data-date', dateKey);
        
        // Check if this is today
        if (day === todayDate && currentCalendarMonth === todayMonth && currentCalendarYear === todayYear) {
            dayElement.classList.add('today');
        }
        
        // Apply availability status
        if (availabilityData[dateKey]) {
            dayElement.classList.add(availabilityData[dateKey]);
        }
        
        // Add click event for current month days only
        dayElement.addEventListener('click', () => handleDayClick(dayElement, dateKey));
        
        calendarGrid.appendChild(dayElement);
    }

    // Add next month's leading days
    const totalCells = calendarGrid.children.length - 7; // Subtract day headers
    const remainingCells = 42 - totalCells; // 6 rows × 7 days = 42 cells
    for (let day = 1; day <= remainingCells; day++) {
        const dayElement = document.createElement('div');
        dayElement.className = 'calendar-day other-month';
        dayElement.textContent = day;
        calendarGrid.appendChild(dayElement);
    }
}

function updateNavigationButtons() {
    const today = new Date();
    const currentMonth = today.getMonth();
    const currentYear = today.getFullYear();
    
    // Calculate month difference
    const monthDiff = (currentCalendarYear - currentYear) * 12 + (currentCalendarMonth - currentMonth);
    
    // Enable/disable previous button (can't go before current month)
    const prevButton = document.getElementById('prevMonth');
    prevButton.disabled = monthDiff <= 0;
    
    // Enable/disable next button (can't go beyond 2 months ahead)
    const nextButton = document.getElementById('nextMonth');
    nextButton.disabled = monthDiff >= 2;
}

function previousMonth() {
    const today = new Date();
    const currentMonth = today.getMonth();
    const currentYear = today.getFullYear();
    
    // Calculate current month difference
    const monthDiff = (currentCalendarYear - currentYear) * 12 + (currentCalendarMonth - currentMonth);
    
    // Only allow going back if not at current month
    if (monthDiff > 0) {
        currentCalendarMonth--;
        if (currentCalendarMonth < 0) {
            currentCalendarMonth = 11;
            currentCalendarYear--;
        }
        generateCalendar();
        updateStatusDisplay();
    }
}

function nextMonth() {
    const today = new Date();
    const currentMonth = today.getMonth();
    const currentYear = today.getFullYear();
    
    // Calculate current month difference
    const monthDiff = (currentCalendarYear - currentYear) * 12 + (currentCalendarMonth - currentMonth);
    
    // Only allow going forward if less than 2 months ahead
    if (monthDiff < 2) {
        currentCalendarMonth++;
        if (currentCalendarMonth > 11) {
            currentCalendarMonth = 0;
            currentCalendarYear++;
        }
        generateCalendar();
        updateStatusDisplay();
    }
}

function handleDayClick(dayElement, dateKey) {
    // Don't allow clicking on other month days
    if (dayElement.classList.contains('other-month')) {
        return;
    }
    
    // Remove previous availability classes
    dayElement.classList.remove('available', 'unavailable');
    
    // Cycle through availability states: none -> available -> unavailable -> none
    let newStatus = '';
    if (!availabilityData[dateKey]) {
        newStatus = 'available';
        dayElement.classList.add('available');
    } else if (availabilityData[dateKey] === 'available') {
        newStatus = 'unavailable';
        dayElement.classList.add('unavailable');
    } else {
        newStatus = '';
        // Remove from availability data
        delete availabilityData[dateKey];
    }
    
    // Store the new status
    if (newStatus) {
        availabilityData[dateKey] = newStatus;
    }
    
    // Update status display
    updateStatusDisplay();
}

function updateStatusDisplay() {
    const statusElement = document.getElementById('availabilityStatus');
    const availableDays = Object.keys(availabilityData).filter(key => availabilityData[key] === 'available').length;
    const unavailableDays = Object.keys(availabilityData).filter(key => availabilityData[key] === 'unavailable').length;
    
    statusElement.innerHTML = `
        <div class="status-item">
            <span class="status-indicator available"></span>
            Available: ${availableDays} days
        </div>
        <div class="status-item">
            <span class="status-indicator unavailable"></span>
            Unavailable: ${unavailableDays} days
        </div>
    `;
    
    // Enable/disable submit button based on whether there's any availability data
    const submitButton = document.getElementById('submitAvailability');
    const hasData = availableDays > 0 || unavailableDays > 0;
    submitButton.disabled = !hasData;
    submitButton.textContent = hasData ? 
        `Submit Availability (${availableDays + unavailableDays} days marked)` : 
        'Mark some days to submit';
}

function submitAvailability() {
    const calendarCode = document.getElementById('calendarCode').textContent;
    const userName = document.getElementById('userName').textContent;
    
    // Prepare data for submission
    const submitData = {
        calendar_code: calendarCode,
        user_name: userName,
        availability: availabilityData
    };
    
    // Show loading state
    const submitButton = document.getElementById('submitAvailability');
    const originalText = submitButton.textContent;
    submitButton.disabled = true;
    submitButton.textContent = 'Submitting...';
    
    // Submit to server
    fetch('/submit_availability', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(submitData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show success message
            showMessage('✅ Availability submitted successfully!', 'success');
            
            // Reset submit button
            submitButton.textContent = 'Submitted ✓';
            submitButton.style.backgroundColor = '#4caf50';
            
            // Reset after 3 seconds
            setTimeout(() => {
                submitButton.style.backgroundColor = '';
                updateStatusDisplay();
            }, 3000);
        } else {
            throw new Error(data.error || 'Failed to submit availability');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showMessage('❌ Failed to submit availability. Please try again.', 'error');
        submitButton.disabled = false;
        submitButton.textContent = originalText;
    });
}

function showMessage(message, type) {
    // Remove existing message
    const existingMessage = document.querySelector('.status-message');
    if (existingMessage) {
        existingMessage.remove();
    }
    
    // Create new message
    const messageDiv = document.createElement('div');
    messageDiv.className = `status-message ${type}`;
    messageDiv.textContent = message;
    
    // Insert after availability status
    const statusDiv = document.querySelector('.availability-status');
    statusDiv.parentNode.insertBefore(messageDiv, statusDiv.nextSibling);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (messageDiv.parentNode) {
            messageDiv.remove();
        }
    }, 5000);
}

// Generate calendar when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Initialize with existing data if available
    if (typeof window.existingAvailability !== 'undefined') {
        initializeAvailability(window.existingAvailability);
    }
    generateCalendar();
    updateStatusDisplay(); // Update status display with any loaded data
});
