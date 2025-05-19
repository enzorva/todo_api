# Todo List API

A simple RESTful API for managing users, todo lists, and todo items, built with Flask and SQLite.

## Features
- User registration and login with JWT authentication
- Create, read, update, and delete todo lists
- Create, read, update, and delete todo items
- Pagination and filtering for lists and items
- Secure secret key management using a `.env` file (not committed to version control)

## Getting Started

### Prerequisites
- Python 3.8+
- pip

### Installation
1. Clone the repository:
   ```sh
   git clone <your-repo-url>
   cd todo_api
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project root and add your secret key:
   ```env
   SECRET_KEY=your-very-secret-key
   ```
4. Run the application:
   ```sh
   python api.py
   ```

## API Endpoints

### Authentication
- `POST /auth/register` — Register a new user
- `POST /auth/login` — Login and receive a JWT token
- `POST /auth/logout` — Logout (client-side token discard)

### Todo Lists
- `GET /lists` — Get all lists (with pagination/filtering)
- `POST /lists` — Create a new list
- `GET /lists/<list_id>` — Get a specific list
- `PUT /lists/<list_id>` — Update a list
- `DELETE /lists/<list_id>` — Delete a list

### Todo Items
- `GET /lists/<list_id>/items` — Get items in a list (with pagination/filtering)
- `POST /lists/<list_id>/items` — Create a new item
- `GET /lists/<list_id>/items/<item_id>` — Get a specific item
- `PUT /lists/<list_id>/items/<item_id>` — Update an item
- `DELETE /lists/<list_id>/items/<item_id>` — Delete an item

## Notes
- All protected endpoints require the `Authorization: Bearer <token>` header.
- The `.env` file is excluded from version control for security.

## Project Source
This project is based on the roadmap.sh Todo List API project:
https://roadmap.sh/projects/todo-list-api
