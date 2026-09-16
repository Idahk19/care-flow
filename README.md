# CareFlow

## Problem Statement

Hospitals often face challenges managing patient appointments and queues efficiently. Patients may have to wait for long periods without knowing their position in the queue or how long they are likely to wait. Doctors and hospital staff may also struggle to manage patient flow, especially when patients arrive late, are skipped, or need to be checked in manually.

Traditional appointment systems often focus only on booking appointments and do not provide an integrated way to manage the patient's journey from booking to check-in, queuing, consultation, and completion.

CareFlow was developed to provide a centralized system that improves appointment management and patient queue handling while giving patients better visibility of their appointment and queue status.

## Solution

CareFlow is a hospital appointment and patient queue management system built with Django and Django REST Framework.

The system allows patients to register, log in, book appointments, select available doctors and time slots, check in when they arrive at the hospital, and monitor their position in the queue.

Doctors can view their daily patient queue, call the next patient, skip patients when necessary, start consultations, and complete consultations.

The system also provides estimated waiting times and in-app notifications to keep patients informed about their queue status.

### Queue Workflow

```
Book Appointment
       ↓
Patient Arrives
       ↓
Check In
       ↓
Queue Number Assigned
       ↓
WAITING
       ↓
Doctor Calls Patient
       ↓
CALLED
       ↓
Consultation Starts
       ↓
IN_PROGRESS
       ↓
Consultation Completed
       ↓
COMPLETED
```
# Features
## Patient Features
- Patient registration
- Patient authentication
- JWT authentication
- Book appointments
- Select services
- Select doctors
- Select appointment dates
- Select available time slots
- View appointments
- Update appointments
- Cancel appointments
- Check in for appointments
- Automatically receive a queue number
- View current queue status
- View number of patients ahead
- View estimated waiting time
- Receive in-app notifications
## Doctor Features
- Doctor authentication
- View today's patient queue
- Call the next patient
- Skip a patient
- Call skipped patients after waiting patients are handled
- Start consultations
- Complete consultations
- Automatically update appointment status
## Queue Features
- Automatic queue number assignment
- Queue numbers based on check-in order
- Waiting patient management
- Called patient management
- In-progress consultation tracking
- Completed patient tracking
- Skipped patient handling
- Dynamic calculation of patients ahead
- Dynamic estimated waiting time
- Notification Features
- Check-in notifications
- Almost-turn notifications
- Your-turn notifications

## Tech Stack
### Backend
- Python
- Django
- Django REST Framework
### Authentication
- JSON Web Tokens (JWT)
- djangorestframework-simplejwt
### Database
- PostgreSQL 
### API Testing
- Postman
- Django REST Framework Browsable API
### Development Tools
Visual Studio Code
Git
GitHub

# Project Structure
```
care-flow/
│
├── accounts/
│   ├── migrations/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── ...
│
├── appointments/
│   ├── migrations/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── ...
│
├── queue_management/
│   ├── migrations/
│   ├── models.py
│   ├── serializers.py
│   ├── services.py
│   ├── views.py
│   ├── urls.py
│   └── ...
│
├── notifications/
│   ├── migrations/
│   ├── models.py
│   ├── serializers.py
│   ├── services.py
│   ├── views.py
│   ├── urls.py
│   └── ...
│
├── careflow/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   ├── wsgi.py
│   └── ...
│
├── manage.py
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```
# Future Improvements

The following improvements could be added in future versions:

- SMS notifications(After front-end)
- More accurate waiting-time predictions using historical consultation data
- Appointment reminders

## License

MIT license

## Author

Idah Karwitha - fullstack developer