from pydantic import BaseModel, Field
from typing import List


class Decision(BaseModel):
    title: str = Field(description="כותרת ההחלטה")
    summary: str = Field(description="תקציר ההחלטה הטכנית")
    status: str = Field(description="סטטוס ההחלטה (בוצע/בתהליך/בוטל)")
    source_tool: str = Field(description="שם הכלי שממנו הגיע המידע (Windsurf/Copilot)")
    source_file: str = Field(description="שם הקובץ שממנו חולץ הפריט")


class Rule(BaseModel):
    rule: str = Field(description="תיאור הכלל או ההנחיה")
    scope: str = Field(description="היקף היישום (UI, Backend, Security וכו')")
    source_tool: str = Field(description="שם הכלי שממנו הגיע המידע (Windsurf/Copilot)")
    source_file: str = Field(description="שם הקובץ שממנו חולץ הפריט")


class WarningItem(BaseModel):
    area: str = Field(description="האזור אליו מתייחסת האזהרה")
    message: str = Field(description="תוכן האזהרה")
    severity: str = Field(description="דרגת חומרה (High, Medium, Low)")
    source_tool: str = Field(description="שם הכלי שממנו הגיע המידע (Windsurf/Copilot)")
    source_file: str = Field(description="שם הקובץ שממנו חולץ הפריט")


class ExtractedProjectData(BaseModel):
    decisions: List[Decision] = Field(default_factory=list)
    rules: List[Rule] = Field(default_factory=list)
    warnings: List[WarningItem] = Field(default_factory=list)
