"""
Service for managing versioned prompt templates.
"""

from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from app.models.prompt_template import PromptTemplate
from app.core.logging import logger
import uuid


class PromptService:
    """
    Manages fetching and versioning of AI prompts.
    """
    
    def get_active_prompt(self, db: Session, name: str) -> Optional[PromptTemplate]:
        """
        Fetch the currently active version of a prompt by name.
        """
        return db.query(PromptTemplate).filter(
            PromptTemplate.name == name,
            PromptTemplate.is_active == True
        ).first()
    
    def get_prompt_version(self, db: Session, name: str, version: int) -> Optional[PromptTemplate]:
        """
        Fetch a specific version of a prompt.
        """
        return db.query(PromptTemplate).filter(
            PromptTemplate.name == name,
            PromptTemplate.version == version
        ).first()
    
    def create_prompt_version(
        self, 
        db: Session, 
        name: str, 
        content: str, 
        config: Optional[Dict[str, Any]] = None,
        activate: bool = False
    ) -> PromptTemplate:
        """
        Create a new version for a prompt.
        If activate=True, it will deactivate previous versions of the same name.
        """
        # Get latest version number
        latest = db.query(PromptTemplate).filter(
            PromptTemplate.name == name
        ).order_by(PromptTemplate.version.desc()).first()
        
        new_version = (latest.version + 1) if latest else 1
        
        prompt = PromptTemplate(
            name=name,
            version=new_version,
            content=content,
            config=config,
            is_active=activate
        )
        
        if activate:
            # Deactivate others
            db.query(PromptTemplate).filter(
                PromptTemplate.name == name,
                PromptTemplate.is_active == True
            ).update({"is_active": False})
            
        db.add(prompt)
        db.commit()
        db.refresh(prompt)
        
        logger.info(f"Created new prompt version: {name} v{new_version} (active={activate})")
        return prompt

    def activate_version(self, db: Session, prompt_id: uuid.UUID) -> bool:
        """
        Activate a specific prompt version.
        """
        prompt = db.query(PromptTemplate).filter(PromptTemplate.id == prompt_id).first()
        if not prompt:
            return False
            
        # Deactivate others with same name
        db.query(PromptTemplate).filter(
            PromptTemplate.name == prompt.name,
            PromptTemplate.is_active == True
        ).update({"is_active": False})
        
        prompt.is_active = True
        db.commit()
        
        logger.info(f"Activated prompt version: {prompt.name} v{prompt.version}")
        return True

# Singleton instance
prompt_service = PromptService()
