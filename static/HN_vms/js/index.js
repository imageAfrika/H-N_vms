
    
        function generateCalendar() {
            const date = new Date();
            const calendarDiv = document.getElementById('calendar');
            const daysOfWeek = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
            
            // Create day labels
            const daysRow = document.createElement('div');
            daysOfWeek.forEach(day => {
                const dayLabel = document.createElement('div');
                dayLabel.textContent = day;
                dayLabel.classList.add('day');
                daysRow.appendChild(dayLabel);
            });
            calendarDiv.appendChild(daysRow);

            // Determine the number of days in the month
            const daysInMonth = new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();

            // Start on the first day of the month
            date.setDate(1);

            // Fill in empty cells until the start of the month
            while (date.getDay()!== 0) { // 0 represents Sunday
                const emptyDay = document.createElement('div');
                emptyDay.classList.add('day');
                calendarDiv.appendChild(emptyDay);
                date.setDate(date.getDate() + 1);
            }

            // Fill in the rest of the month
            for (let i = 1; i <= daysInMonth; i++) {
                const dayElement = document.createElement('div');
                dayElement.textContent = i;
                dayElement.classList.add('day');
                calendarDiv.appendChild(dayElement);
                date.setDate(date.getDate() + 1);
            }
        }

        generateCalendar();
    

    
document.addEventListener('DOMContentLoaded', function() {
    var calendarEl = document.getElementById('calendar');
    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth'
    });
    calendar.render();
})
