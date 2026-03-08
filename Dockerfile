FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Set timezone dynamically if needed, though pytz handles IST inside Python.
# It's good practice to set the container timezone anyway.
ENV TZ=Asia/Kolkata

# Set working directory
WORKDIR /app

# Ensure logs and temp directories exist
RUN mkdir -p /app/logs /app/media/temp

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium specifically to keep image size small
RUN playwright install chromium

# Copy the rest of the project files
COPY . .

# Run the scheduler indefinitely in the background
CMD ["python", "-m", "scheduler.task_scheduler"]
