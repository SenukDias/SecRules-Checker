from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import ROLE_ADMIN, CurrentUser, require_roles
from app.db import get_db
from app.models.db_models import CustomRule

router = APIRouter(prefix="/admin/custom-rules", tags=["admin"])


class CustomRuleIn(BaseModel):
    name: str
    severity: str = "medium"
    category: str = "custom"
    condition: dict
    description_template: str
    remediation: str
    enabled: bool = True


class CustomRuleOut(CustomRuleIn):
    id: str
    created_by: str


@router.get("", response_model=list[CustomRuleOut])
def list_custom_rules(db: Session = Depends(get_db), user: CurrentUser = Depends(require_roles(ROLE_ADMIN))):
    return db.query(CustomRule).all()


@router.post("", response_model=CustomRuleOut, status_code=201)
def create_custom_rule(
    payload: CustomRuleIn,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(ROLE_ADMIN)),
):
    rule = CustomRule(**payload.model_dump(), created_by=user.username)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.put("/{rule_id}", response_model=CustomRuleOut)
def update_custom_rule(
    rule_id: str,
    payload: CustomRuleIn,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(ROLE_ADMIN)),
):
    rule = db.get(CustomRule, rule_id)
    if rule is None:
        raise HTTPException(404, "Custom rule not found")
    for key, value in payload.model_dump().items():
        setattr(rule, key, value)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{rule_id}", status_code=204)
def delete_custom_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(ROLE_ADMIN)),
):
    rule = db.get(CustomRule, rule_id)
    if rule is None:
        raise HTTPException(404, "Custom rule not found")
    db.delete(rule)
    db.commit()
