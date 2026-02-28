from pydantic import BaseModel, Field, validator
from typing import Literal, Optional

class RecommendRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Investment amount in INR")
    duration_value: float = Field(..., gt=0, description="Duration numeric value")
    duration_unit: Literal["days", "months", "years"] = Field(..., description="Duration unit")
    magic_mode: bool = Field(False, description="Enable AI autonomous allocation")
    risk_appetite: Optional[Literal["low", "medium", "high"]] = Field("medium")

    @validator("amount")
    def amount_reasonable(cls, v):
        if v < 100:
            raise ValueError("Minimum investment amount is ₹100")
        return v

    def duration_in_days(self) -> int:
        if self.duration_unit == "days":
            return int(self.duration_value)
        elif self.duration_unit == "months":
            return int(self.duration_value * 30)
        else:
            return int(self.duration_value * 365)
