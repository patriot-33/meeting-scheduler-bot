from sqlalchemy.orm import Session
from src.database import User, UserRole, UserStatus
from typing import List, Optional

class UserService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID."""
        return self.db.query(User).filter(User.telegram_id == telegram_id).first()
    
    def create_user(self, telegram_id: int, username: str, first_name: str, 
                   last_name: str, department: str) -> User:
        """Create a new user."""
        user = User(
            telegram_id=telegram_id,
            telegram_username=username,
            first_name=first_name,
            last_name=last_name,
            department=department,
            role=UserRole.PENDING
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def approve_user(self, user_id: int) -> bool:
        """Approve a pending user."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if user and user.role == UserRole.PENDING:
            user.role = UserRole.MANAGER
            self.db.commit()
            return True
        return False
    
    def get_pending_users(self) -> List[User]:
        """Get all users pending approval."""
        return self.db.query(User).filter(User.role == UserRole.PENDING).all()
    
    def get_active_managers(self) -> List[User]:
        """Get all active managers."""
        return self.db.query(User).filter(
            User.role == UserRole.MANAGER,
            User.status == UserStatus.ACTIVE
        ).all()
    
    def update_user_status(self, user_id: int, status: UserStatus) -> bool:
        """Update user status."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.status = status
            self.db.commit()
            return True
        return False
    
    def delete_user(self, user_id: int) -> bool:
        """Delete a user."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            self.db.delete(user)
            self.db.commit()
            return True
        return False