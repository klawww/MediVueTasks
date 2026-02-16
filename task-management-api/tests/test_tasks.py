from datetime import date, timedelta
import pytest


class TestCreateTask:
    """Tests for POST /tasks endpoint."""

    def test_create_task_success(self, client):
        """Test successful task creation."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        response = client.post(
            "/tasks",
            json={
                "title": "Test Task",
                "description": "Test description",
                "priority": 3,
                "due_date": tomorrow,
                "tags": ["work", "urgent"],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Task"
        assert data["description"] == "Test description"
        assert data["priority"] == 3
        assert data["due_date"] == tomorrow
        assert data["completed"] is False
        assert set(data["tags"]) == {"work", "urgent"}
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_task_minimal(self, client):
        """Test task creation with only required fields."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        response = client.post(
            "/tasks",
            json={
                "title": "Minimal Task",
                "priority": 1,
                "due_date": tomorrow,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Minimal Task"
        assert data["description"] is None
        assert data["tags"] == []

    def test_create_task_empty_title(self, client):
        """Test validation error for empty title."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        response = client.post(
            "/tasks",
            json={
                "title": "",
                "priority": 3,
                "due_date": tomorrow,
            },
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "Validation Failed"
        assert "title" in data["details"]

    def test_create_task_title_too_long(self, client):
        """Test validation error for title exceeding 200 characters."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        response = client.post(
            "/tasks",
            json={
                "title": "x" * 201,
                "priority": 3,
                "due_date": tomorrow,
            },
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "Validation Failed"

    def test_create_task_invalid_priority_low(self, client):
        """Test validation error for priority below 1."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        response = client.post(
            "/tasks",
            json={
                "title": "Test Task",
                "priority": 0,
                "due_date": tomorrow,
            },
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "Validation Failed"
        assert "priority" in data["details"]

    def test_create_task_invalid_priority_high(self, client):
        """Test validation error for priority above 5."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        response = client.post(
            "/tasks",
            json={
                "title": "Test Task",
                "priority": 6,
                "due_date": tomorrow,
            },
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "Validation Failed"
        assert "priority" in data["details"]

    def test_create_task_past_due_date(self, client):
        """Test validation error for due_date in the past."""
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        response = client.post(
            "/tasks",
            json={
                "title": "Test Task",
                "priority": 3,
                "due_date": yesterday,
            },
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "Validation Failed"
        assert "due_date" in data["details"]


class TestListTasks:
    """Tests for GET /tasks endpoint."""

    def test_list_tasks_empty(self, client):
        """Test listing tasks when none exist."""
        response = client.get("/tasks")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["tasks"] == []

    def test_list_tasks_pagination(self, client):
        """Test pagination parameters."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        # Create 5 tasks
        for i in range(5):
            client.post(
                "/tasks",
                json={"title": f"Task {i}", "priority": 3, "due_date": tomorrow},
            )

        # Get first 2
        response = client.get("/tasks?limit=2&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["tasks"]) == 2
        assert data["limit"] == 2
        assert data["offset"] == 0

        # Get next 2
        response = client.get("/tasks?limit=2&offset=2")
        data = response.json()
        assert len(data["tasks"]) == 2
        assert data["offset"] == 2

    def test_filter_by_completed(self, client):
        """Test filtering by completion status."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        # Create tasks
        client.post("/tasks", json={"title": "Task 1", "priority": 3, "due_date": tomorrow})
        response = client.post("/tasks", json={"title": "Task 2", "priority": 3, "due_date": tomorrow})
        task_id = response.json()["id"]

        # Mark one as completed
        client.patch(f"/tasks/{task_id}", json={"completed": True})

        # Filter completed
        response = client.get("/tasks?completed=true")
        data = response.json()
        assert data["total"] == 1
        assert data["tasks"][0]["completed"] is True

        # Filter not completed
        response = client.get("/tasks?completed=false")
        data = response.json()
        assert data["total"] == 1
        assert data["tasks"][0]["completed"] is False

    def test_filter_by_priority(self, client):
        """Test filtering by priority level."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        client.post("/tasks", json={"title": "Low Priority", "priority": 1, "due_date": tomorrow})
        client.post("/tasks", json={"title": "High Priority", "priority": 5, "due_date": tomorrow})

        response = client.get("/tasks?priority=5")
        data = response.json()
        assert data["total"] == 1
        assert data["tasks"][0]["priority"] == 5
        assert data["tasks"][0]["title"] == "High Priority"

    def test_filter_by_tags(self, client):
        """Test filtering by tags (any match)."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        client.post("/tasks", json={"title": "Work Task", "priority": 3, "due_date": tomorrow, "tags": ["work"]})
        client.post("/tasks", json={"title": "Personal Task", "priority": 3, "due_date": tomorrow, "tags": ["personal"]})
        client.post("/tasks", json={"title": "Work Urgent", "priority": 5, "due_date": tomorrow, "tags": ["work", "urgent"]})

        # Filter by single tag
        response = client.get("/tasks?tags=work")
        data = response.json()
        assert data["total"] == 2

        # Filter by multiple tags (OR logic)
        response = client.get("/tasks?tags=work,personal")
        data = response.json()
        assert data["total"] == 3

        # Filter by tag that doesn't exist
        response = client.get("/tasks?tags=nonexistent")
        data = response.json()
        assert data["total"] == 0


class TestGetTask:
    """Tests for GET /tasks/{id} endpoint."""

    def test_get_task_success(self, client):
        """Test getting a specific task."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        create_response = client.post(
            "/tasks",
            json={"title": "Test Task", "priority": 3, "due_date": tomorrow},
        )
        task_id = create_response.json()["id"]

        response = client.get(f"/tasks/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert data["title"] == "Test Task"

    def test_get_task_not_found(self, client):
        """Test 404 for non-existent task."""
        response = client.get("/tasks/9999")
        assert response.status_code == 404
        data = response.json()
        # Error format is consistent with validation errors: {"error": "...", "details": {...}}
        assert data["error"] == "Not Found"
        assert "task_id" in data["details"]


class TestUpdateTask:
    """Tests for PATCH /tasks/{id} endpoint."""

    def test_update_task_partial(self, client):
        """Test partial update - only specified fields change."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        create_response = client.post(
            "/tasks",
            json={
                "title": "Original Title",
                "description": "Original Description",
                "priority": 3,
                "due_date": tomorrow,
            },
        )
        task_id = create_response.json()["id"]

        # Only update title
        response = client.patch(f"/tasks/{task_id}", json={"title": "Updated Title"})
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["description"] == "Original Description"  # Unchanged
        assert data["priority"] == 3  # Unchanged

    def test_update_task_completed(self, client):
        """Test marking task as completed."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        create_response = client.post(
            "/tasks",
            json={"title": "Test Task", "priority": 3, "due_date": tomorrow},
        )
        task_id = create_response.json()["id"]

        response = client.patch(f"/tasks/{task_id}", json={"completed": True})
        assert response.status_code == 200
        assert response.json()["completed"] is True

    def test_update_task_tags(self, client):
        """Test updating task tags."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        create_response = client.post(
            "/tasks",
            json={"title": "Test Task", "priority": 3, "due_date": tomorrow, "tags": ["old"]},
        )
        task_id = create_response.json()["id"]

        response = client.patch(f"/tasks/{task_id}", json={"tags": ["new", "updated"]})
        assert response.status_code == 200
        assert set(response.json()["tags"]) == {"new", "updated"}

    def test_update_task_not_found(self, client):
        """Test 404 for updating non-existent task."""
        response = client.patch("/tasks/9999", json={"title": "New Title"})
        assert response.status_code == 404

    def test_update_task_invalid_priority(self, client):
        """Test validation error for invalid priority in update."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        create_response = client.post(
            "/tasks",
            json={"title": "Test Task", "priority": 3, "due_date": tomorrow},
        )
        task_id = create_response.json()["id"]

        response = client.patch(f"/tasks/{task_id}", json={"priority": 10})
        assert response.status_code == 422


class TestDeleteTask:
    """Tests for DELETE /tasks/{id} endpoint."""

    def test_delete_task_success(self, client):
        """Test soft deleting a task."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        create_response = client.post(
            "/tasks",
            json={"title": "Test Task", "priority": 3, "due_date": tomorrow},
        )
        task_id = create_response.json()["id"]

        # Delete the task
        response = client.delete(f"/tasks/{task_id}")
        assert response.status_code == 204

        # Task should not be accessible anymore
        response = client.get(f"/tasks/{task_id}")
        assert response.status_code == 404

        # Task should not appear in list
        response = client.get("/tasks")
        assert response.json()["total"] == 0

    def test_delete_task_not_found(self, client):
        """Test 404 for deleting non-existent task."""
        response = client.delete("/tasks/9999")
        assert response.status_code == 404

    def test_delete_task_idempotent(self, client):
        """Test that deleting already deleted task returns 404."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        create_response = client.post(
            "/tasks",
            json={"title": "Test Task", "priority": 3, "due_date": tomorrow},
        )
        task_id = create_response.json()["id"]

        # First delete
        client.delete(f"/tasks/{task_id}")

        # Second delete should return 404
        response = client.delete(f"/tasks/{task_id}")
        assert response.status_code == 404
