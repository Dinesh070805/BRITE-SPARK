# AI Usage & Pair Programming Statement

This document transparently describes the use of AI-assisted pair
programming during the development of the full-stack
**Reminder That Reaches** application.

The project was primarily designed, implemented, tested, and
reviewed by the developer. AI tools were used selectively as a
development assistant rather than as a replacement for the
developer's implementation and decision-making.

---

## 1. Developer Ownership

The developer was primarily responsible for:

- Understanding the problem statement and requirements.
- Identifying the core problem and designing the overall solution.
- Planning the application workflow and major system components.
- Making architectural and technical decisions.
- Implementing and integrating the main application functionality.
- Working with the provided datasets and mock communication channels.
- Testing the application and verifying its behaviour.
- Reviewing and correcting AI-assisted code where necessary.
- Making final decisions about the user interface and user experience.
- Validating the application against the challenge requirements.
- Adapting the system when the regulator's surprise requirement was
  introduced.

AI-generated suggestions were reviewed and adapted rather than being
accepted blindly.

---

## 2. Areas Where AI Assistance Was Used

### Understanding the Problem Statement

AI was used to help:

- Break down the problem statement into technical requirements.
- Clarify ambiguous requirements and expected system behaviour.
- Identify important edge cases and constraints.
- Reason about how the requirements could be translated into
  application functionality.

The final interpretation of the requirements and implementation
decisions were made by the developer.

### Backend & API Assistance

AI assistance was used selectively for parts of the backend,
including:

- Drafting some FastAPI API endpoints.
- Suggesting API request/response structures.
- Assisting with backend service organization.
- Helping with selected SQLAlchemy and Pydantic implementations.
- Debugging and improving some backend code.

The developer reviewed, integrated, tested, and modified these
components as required.

### Database Assistance

AI was used for limited assistance with:

- SQLAlchemy model structure.
- Database relationships.
- CSV-to-database seeding logic.
- Identifying validation and data-handling cases.

The developer was responsible for deciding what data the application
needed and verifying the resulting database behaviour.

### Frontend & UI/UX

AI assistance was used primarily as a design and development aid for:

- Exploring UI/UX layouts.
- Suggesting dashboard structures.
- Improving page organization and navigation.
- Assisting with selected React components.
- Suggesting visual hierarchy, tables, cards, filters, and charts.
- Reviewing frontend/backend integration issues.

The developer directed the overall UI requirements and reviewed the
resulting implementation.

### Testing & Debugging

AI was also used as a debugging and reasoning assistant to:

- Interpret error messages.
- Suggest possible causes of bugs.
- Propose test cases and edge cases.
- Assist in identifying integration issues.
- Suggest improvements to implementation logic.

All relevant fixes were tested and verified by the developer.

---

## 3. Mock Channels and Data

AI assistance was used in selected areas involving:

- Database seeding.
- Integration with the provided mock communication channels.
- Structuring backend services around the supplied channel
  implementation.

The developer verified that the application used the provided
challenge resources correctly and that the resulting behaviour
matched the requirements.

---

## 4. Developer Review & Verification

AI-assisted code was not treated as automatically correct.

The developer reviewed and verified the implementation through:

### Backend Integration

Verified that the backend correctly handles:

- Reminder records.
- Reminder attempts.
- Audit records.
- Database persistence.
- Reminder processing.
- API communication.

### Frontend Integration

Verified that the React frontend communicates with the FastAPI
backend through the required REST APIs, including:

- `/api/dashboard`
- `/api/appointments`
- `/api/residents`
- `/api/reminders`
- `/api/audit-logs`
- `/api/metrics`
- `/api/policies`

### Automated Testing

Backend tests were executed using:

```bash
python -m unittest discover -s backend/tests -p "test_*.py" -v
```
