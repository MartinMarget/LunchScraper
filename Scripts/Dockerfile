FROM python:3.11-slim


# Install cron
RUN apt-get update && apt-get install -y cron && apt-get clean

# Install Python deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy files
COPY . .

# Install crontab
RUN crontab /crontab.txt

# Start cron in foreground
CMD ["cron", "-f"]

