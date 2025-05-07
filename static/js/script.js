// Main JavaScript for Blood Donor Website

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    
    // Check for flash messages and auto-dismiss after 5 seconds
    const flashMessages = document.querySelectorAll('.alert-dismissible');
    flashMessages.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // Handle emergency response buttons
    const emergencyResponseBtns = document.querySelectorAll('.emergency-response-btn');
    emergencyResponseBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            const response = this.getAttribute('data-response');
            const requestId = this.getAttribute('data-request-id');
            
            // You would normally send this to the server via fetch/AJAX
            console.log(`Emergency request ${requestId} response: ${response}`);
            
            // Show confirmation message
            const responseMsg = response === 'available' ? 'Thank you for responding!' : 'Thank you for your response';
            const alertType = response === 'available' ? 'success' : 'secondary';
            
            // Display alert (in real app would be handled by server response)
            const alertContainer = document.getElementById('alert-container');
            if (alertContainer) {
                alertContainer.innerHTML = `
                    <div class="alert alert-${alertType} alert-dismissible fade show" role="alert">
                        <strong>${responseMsg}</strong> Your response has been recorded.
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                `;
            }
        });
    });
    
    // Blood type selection handler for donation scheduling
    const bloodTypeSelect = document.getElementById('blood_type');
    if (bloodTypeSelect) {
        bloodTypeSelect.addEventListener('change', function() {
            // This could be used to show/hide additional fields or requirements
            // based on the selected blood type
            console.log(`Selected blood type: ${this.value}`);
        });
    }
    
    // Location services for donor
    if (navigator.geolocation && document.getElementById('update-location-btn')) {
        document.getElementById('update-location-btn').addEventListener('click', function() {
            navigator.geolocation.getCurrentPosition(
                function(position) {
                    const lat = position.coords.latitude;
                    const lng = position.coords.longitude;
                    
                    // In a real app, you would send this to the server
                    console.log(`Location updated: Lat ${lat}, Lng ${lng}`);
                    
                    // Update UI to show location is current
                    document.getElementById('location-status').textContent = 'Location updated';
                    document.getElementById('location-status').classList.add('text-success');
                },
                function(error) {
                    console.error("Error getting location: ", error);
                    document.getElementById('location-status').textContent = 'Error updating location';
                    document.getElementById('location-status').classList.add('text-danger');
                }
            );
        });
    }
    
    // Appointment calendar functionality
    if (document.getElementById('appointment-calendar')) {
        initializeAppointmentCalendar();
    }
    
    // Dashboard chart initialization
    if (document.getElementById('donations-chart')) {
        initializeDonationChart();
    }
    
    // Eligibility calculator
    const eligibilityForm = document.getElementById('eligibility-form');
    if (eligibilityForm) {
        eligibilityForm.addEventListener('submit', function(e) {
            e.preventDefault();
            calculateEligibility();
        });
    }
});

// Appointment calendar initialization
function initializeAppointmentCalendar() {
    // This would be replaced with a proper calendar library in a real app
    console.log('Appointment calendar initialized');
    
    // Setup click handler for available dates
    const availableDates = document.querySelectorAll('.calendar-day');
    availableDates.forEach(day => {
        day.addEventListener('click', function() {
            // Remove previous selections
            document.querySelectorAll('.calendar-day.active').forEach(el => {
                el.classList.remove('active');
            });
            
            // Add active class to selected date
            this.classList.add('active');
            
            // Update selection in form
            const selectedDate = this.getAttribute('data-date');
            document.getElementById('selected_date').value = selectedDate;
        });
    });
}

// Eligibility calculation based on form inputs
function calculateEligibility() {
    // Example calculations - real logic would be more complex
    const weight = parseFloat(document.getElementById('weight').value);
    const hasTattoos = document.getElementById('has_tattoos_yes').checked;
    const lastDonation = new Date(document.getElementById('last_donation').value);
    const today = new Date();
    
    // Days since last donation
    const daysSinceLastDonation = Math.floor((today - lastDonation) / (1000 * 60 * 60 * 24));
    
    let isEligible = true;
    const reasons = [];
    
    // Weight check
    if (weight < 50) {
        isEligible = false;
        reasons.push('Weight must be at least 50kg');
    }
    
    // Tattoo check
    if (hasTattoos) {
        const tattooDate = new Date(document.getElementById('tattoo_date').value);
        const daysSinceTattoo = Math.floor((today - tattooDate) / (1000 * 60 * 60 * 24));
        
        if (daysSinceTattoo < 365) {
            isEligible = false;
            reasons.push('Must wait 1 year after getting a tattoo');
        }
    }
    
    // Last donation check
    if (!isNaN(daysSinceLastDonation) && daysSinceLastDonation < 90) {
        isEligible = false;
        reasons.push(`Must wait ${90 - daysSinceLastDonation} more days since last donation`);
    }
    
    // Update UI with results
    const resultElement = document.getElementById('eligibility-result');
    if (isEligible) {
        resultElement.innerHTML = '<div class="alert alert-success">You are eligible to donate blood!</div>';
    } else {
        let reasonsHtml = reasons.map(reason => `<li>${reason}</li>`).join('');
        resultElement.innerHTML = `
            <div class="alert alert-warning">
                <p class="mb-2">You are not eligible to donate at this time due to:</p>
                <ul>${reasonsHtml}</ul>
            </div>
        `;
    }
}

// Sample donation chart initialization
function initializeDonationChart() {
    console.log('Donation chart would be initialized here with a library like Chart.js');
    // In a real app, you would use Chart.js or similar to create a chart
}

// Function to handle notification preferences toggling
function toggleNotificationPreference(type) {
    const elem = document.getElementById(`notification-${type}`);
    if (elem && elem.checked) {
        console.log(`${type} notifications enabled`);
    } else {
        console.log(`${type} notifications disabled`);
    }
    
    // In a real app, you would send this preference to the server
}

// Function for hospital to update blood inventory
function updateInventory(formElement) {
    if (!formElement) return;
    
    // Gather all blood type quantities
    const bloodTypes = ['A_pos', 'A_neg', 'B_pos', 'B_neg', 'AB_pos', 'AB_neg', 'O_pos', 'O_neg'];
    const inventory = {};
    
    bloodTypes.forEach(type => {
        const input = document.getElementById(`inventory_${type}`);
        if (input) {
            inventory[type] = input.value;
        }
    });
    
    // In a real app, you would send this to the server
    console.log('Updated inventory:', inventory);
    
    // Show success message
    const feedbackElem = document.getElementById('inventory-feedback');
    if (feedbackElem) {
        feedbackElem.innerHTML = '<div class="alert alert-success">Inventory updated successfully!</div>';
        
        // Auto-dismiss after 3 seconds
        setTimeout(() => {
            feedbackElem.innerHTML = '';
        }, 3000);
    }
    
    return false; // Prevent form submission if used in onsubmit
}
