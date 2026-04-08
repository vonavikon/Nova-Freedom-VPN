"""
Tests for Database - User Approval System
"""

import pytest
import tempfile
import os
import sys

# Add project root to path for absolute imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from bot.database import Database, STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED


@pytest.fixture
def db():
    """Create temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    database = Database(db_path)
    yield database
    # Cleanup
    os.unlink(db_path)


class TestUserStatusConstants:
    """Test status constants are defined correctly"""

    def test_status_pending_value(self):
        assert STATUS_PENDING == 'pending'

    def test_status_approved_value(self):
        assert STATUS_APPROVED == 'approved'

    def test_status_rejected_value(self):
        assert STATUS_REJECTED == 'rejected'

    def test_statuses_are_distinct(self):
        assert STATUS_PENDING != STATUS_APPROVED
        assert STATUS_PENDING != STATUS_REJECTED
        assert STATUS_APPROVED != STATUS_REJECTED


class TestUserCreation:
    """Test user creation with pending status"""

    def test_new_user_has_pending_status(self, db):
        """New users should have 'pending' status by default"""
        user = db.get_or_create_user(
            telegram_id=12345,
            username='testuser',
            first_name='Test',
            last_name='User'
        )

        assert user is not None
        assert user['telegram_id'] == 12345
        assert user['status'] == STATUS_PENDING

    def test_existing_user_returns_same_user(self, db):
        """Calling get_or_create_user twice returns same user"""
        user1 = db.get_or_create_user(telegram_id=12345, username='user1')
        user2 = db.get_or_create_user(telegram_id=12345, username='user1')

        assert user1['id'] == user2['id']
        assert user1['telegram_id'] == user2['telegram_id']

    def test_get_user_returns_none_for_nonexistent(self, db):
        """get_user returns None for non-existent user"""
        user = db.get_user(telegram_id=99999)
        assert user is None


class TestUserApproval:
    """Test user approval workflow"""

    def test_approve_user_changes_status(self, db):
        """Approving user changes status to 'approved'"""
        db.get_or_create_user(telegram_id=12345, username='testuser')

        result = db.approve_user(telegram_id=12345)

        assert result is True
        user = db.get_user(telegram_id=12345)
        assert user['status'] == STATUS_APPROVED

    def test_approve_nonexistent_user_returns_false(self, db):
        """Approving non-existent user returns False"""
        result = db.approve_user(telegram_id=99999)
        assert result is False

    def test_is_user_approved_returns_true_for_approved(self, db):
        """is_user_approved returns True for approved user"""
        db.get_or_create_user(telegram_id=12345, username='testuser')
        db.approve_user(telegram_id=12345)

        result = db.is_user_approved(telegram_id=12345)

        assert result is True

    def test_is_user_approved_returns_false_for_pending(self, db):
        """is_user_approved returns False for pending user"""
        db.get_or_create_user(telegram_id=12345, username='testuser')

        result = db.is_user_approved(telegram_id=12345)

        assert result is False

    def test_is_user_approved_returns_false_for_nonexistent(self, db):
        """is_user_approved returns False for non-existent user"""
        result = db.is_user_approved(telegram_id=99999)
        assert result is False


class TestUserRejection:
    """Test user rejection workflow"""

    def test_reject_user_changes_status(self, db):
        """Rejecting user changes status to 'rejected'"""
        db.get_or_create_user(telegram_id=12345, username='testuser')

        result = db.reject_user(telegram_id=12345)

        assert result is True
        user = db.get_user(telegram_id=12345)
        assert user['status'] == STATUS_REJECTED

    def test_reject_nonexistent_user_returns_false(self, db):
        """Rejecting non-existent user returns False"""
        result = db.reject_user(telegram_id=99999)
        assert result is False

    def test_is_user_approved_returns_false_for_rejected(self, db):
        """is_user_approved returns False for rejected user"""
        db.get_or_create_user(telegram_id=12345, username='testuser')
        db.reject_user(telegram_id=12345)

        result = db.is_user_approved(telegram_id=12345)

        assert result is False


class TestGetUserStatus:
    """Test get_user_status method"""

    def test_get_status_returns_pending_for_new_user(self, db):
        """New user has 'pending' status"""
        db.get_or_create_user(telegram_id=12345, username='testuser')

        status = db.get_user_status(telegram_id=12345)

        assert status == STATUS_PENDING

    def test_get_status_returns_approved_after_approval(self, db):
        """Status is 'approved' after approval"""
        db.get_or_create_user(telegram_id=12345, username='testuser')
        db.approve_user(telegram_id=12345)

        status = db.get_user_status(telegram_id=12345)

        assert status == STATUS_APPROVED

    def test_get_status_returns_rejected_after_rejection(self, db):
        """Status is 'rejected' after rejection"""
        db.get_or_create_user(telegram_id=12345, username='testuser')
        db.reject_user(telegram_id=12345)

        status = db.get_user_status(telegram_id=12345)

        assert status == STATUS_REJECTED

    def test_get_status_returns_none_for_nonexistent(self, db):
        """get_user_status returns None for non-existent user"""
        status = db.get_user_status(telegram_id=99999)
        assert status is None


class TestGetPendingUsers:
    """Test get_pending_users method"""

    def test_returns_empty_list_when_no_pending(self, db):
        """Returns empty list when no pending users"""
        users = db.get_pending_users()
        assert users == []

    def test_returns_pending_users(self, db):
        """Returns list of pending users"""
        db.get_or_create_user(telegram_id=11111, username='user1')
        db.get_or_create_user(telegram_id=22222, username='user2')
        db.get_or_create_user(telegram_id=33333, username='user3')
        db.approve_user(telegram_id=33333)  # Approve one

        pending = db.get_pending_users()

        assert len(pending) == 2
        pending_ids = [u['telegram_id'] for u in pending]
        assert 11111 in pending_ids
        assert 22222 in pending_ids
        assert 33333 not in pending_ids

    def test_excludes_approved_and_rejected(self, db):
        """Pending list excludes approved and rejected users"""
        db.get_or_create_user(telegram_id=11111, username='pending')
        db.get_or_create_user(telegram_id=22222, username='approved')
        db.get_or_create_user(telegram_id=33333, username='rejected')

        db.approve_user(telegram_id=22222)
        db.reject_user(telegram_id=33333)

        pending = db.get_pending_users()

        assert len(pending) == 1
        assert pending[0]['telegram_id'] == 11111


class TestGetStats:
    """Test get_stats method"""

    def test_stats_counts_correctly(self, db):
        """Stats count users correctly"""
        # Create users
        db.get_or_create_user(telegram_id=11111, username='pending1')
        db.get_or_create_user(telegram_id=22222, username='pending2')
        db.get_or_create_user(telegram_id=33333, username='approved1')
        db.get_or_create_user(telegram_id=44444, username='approved2')
        db.get_or_create_user(telegram_id=55555, username='rejected')

        # Approve some
        db.approve_user(telegram_id=33333)
        db.approve_user(telegram_id=44444)
        db.reject_user(telegram_id=55555)

        stats = db.get_stats()

        assert stats['total_users'] == 5
        assert stats['approved_users'] == 2
        assert stats['pending_users'] == 2
        assert stats['total_devices'] == 0
