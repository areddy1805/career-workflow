import re

with open("src/client/job_classifier.py", "r") as f:
    code = f.read()

def inject(pattern, replacement):
    global code
    code = re.sub(pattern, replacement, code, flags=re.MULTILINE | re.DOTALL)

# Hard Veto (Title)
inject(
    r'print\(f"  \[VETO\] \{j\.get\('"'"'title'"'"'\)\}"\)\n\s*if self\.metrics:\n\s*self\.metrics\.record_rejection\("Hard Veto \(Title\)"\)',
    r'self.record_decision(j, "Hard Veto", "WALK_IN_RECRUITMENT", f"Title matched veto pattern")\n                if self.metrics:\n                    self.metrics.record_rejection("Hard Veto (Title)")'
)

# Hard Veto (Seniority)
inject(
    r'print\(f"  \[VETO - Seniority\] \{j\.get\('"'"'title'"'"'\)\}"\)\n\s*if self\.metrics:\n\s*self\.metrics\.record_rejection\("Hard Veto \(Experience/Seniority\)"\)',
    r'self.record_decision(j, "Hard Veto", "EXPERIENCE_TOO_HIGH", f"Title indicates non-target seniority level")\n                if self.metrics:\n                    self.metrics.record_rejection("Hard Veto (Experience/Seniority)")'
)

# Experience Filter (Fresher)
inject(
    r'print\(f"  \[EXP FILTER - fresher\] \{job\.get\('"'"'title'"'"'\)\}"\)\n\s*if self\.metrics:\n\s*self\.metrics\.record_rejection\("Experience \(Fresher\)"\)',
    r'self.record_decision(job, "Experience Filter", "EXPERIENCE_TOO_LOW", f"Requires fresher/0 years experience")\n                if self.metrics:\n                    self.metrics.record_rejection("Experience (Fresher)")'
)

# Experience Filter (High)
inject(
    r'print\(f"  \[EXP FILTER - high\] \{job\.get\('"'"'title'"'"'\)\}"\)\n\s*if self\.metrics:\n\s*self\.metrics\.record_rejection\("Experience \(High\)"\)',
    r'self.record_decision(job, "Experience Filter", "EXPERIENCE_TOO_HIGH", f"Requires {exp_min}+ years experience")\n                if self.metrics:\n                    self.metrics.record_rejection("Experience (High)")'
)

# Desc Red Flag Check
inject(
    r'print\(f"  \[RED FLAG \{flagged\}\] \{j\.get\('"'"'title'"'"'\)"\)\n\s*if self\.metrics:\n\s*self\.metrics\.record_rejection\(f"Red Flag \(Desc\): \{flagged\[0\]\}"\)',
    r'self.record_decision(j, "Desc Red Flag Check", "DESC_RED_FLAG", f"Description matched red flag pattern: {flagged[0]}")\n                if self.metrics:\n                    self.metrics.record_rejection(f"Red Flag (Desc): {flagged[0]}")'
)

# Full Desc Red Flag Check
inject(
    r'print\(\n\s*f"  \[FULL JD RED FLAG \{flagged\}\] "\n\s*f"\{job\.get\('"'"'title'"'"'\) @ "\n\s*f"\{job\.get\('"'"'company'"'"'\)"\n\s*\)\n\s*if self\.metrics:\n\s*self\.metrics\.record_rejection\(f"Red Flag \(Full JD\): \{flagged\[0\]\}"\)',
    r'self.record_decision(job, "Full Desc Red Flag Check", "FULL_DESC_RED_FLAG", f"Full description matched red flag pattern: {flagged[0]}")\n                if self.metrics:\n                    self.metrics.record_rejection(f"Red Flag (Full JD): {flagged[0]}")'
)

# Title Filter (Not SW/AI)
inject(
    r'print\(f"  \[TITLE FILTER - not software/AI\] \{job\.get\('"'"'title'"'"'\)\}"\)\n\s*if self\.metrics:\n\s*self\.metrics\.record_rejection\("Title Filter \(Not SW/AI\)"\)',
    r'self.record_decision(job, "Title Filter", "NON_SOFTWARE_ROLE", "Non-software role")\n                if self.metrics:\n                    self.metrics.record_rejection("Title Filter (Not SW/AI)")'
)

# Title Filter (Wrong Track)
inject(
    r'print\(f"  \[TITLE FILTER - wrong track\] \{job\.get\('"'"'title'"'"'\)\}"\)\n\s*if self\.metrics:\n\s*self\.metrics\.record_rejection\("Title Filter \(Wrong Track\)"\)',
    r'self.record_decision(job, "Title Filter", "TITLE_WRONG_TRACK", "Target track mismatch")\n                if self.metrics:\n                    self.metrics.record_rejection("Title Filter (Wrong Track)")'
)

# Company Veto
inject(
    r'print\(f"  \[COMPANY VETO\] \{j\.get\('"'"'title'"'"'\) @ \{j\.get\('"'"'company'"'"'\)\}"\)\n\s*if self\.metrics:\n\s*self\.metrics\.record_rejection\("Company Veto"\)',
    r'self.record_decision(j, "Company Veto", "COMPANY_VETO", "Company is blacklisted")\n                if self.metrics:\n                    self.metrics.record_rejection("Company Veto")'
)

# AI Relevance Gate
inject(
    r'print\(\n\s*f"  \[AI RELEVANCE REJECT\] "\n\s*f"\{job\.get\('"'"'title'"'"'\) @ \{job\.get\('"'"'company'"'"'\)"\n\s*\)\n\s*if self\.metrics:\n\s*self\.metrics\.record_rejection\("Non-AI"\)',
    r'self.record_decision(job, "AI Relevance Gate", "LOW_AI_RELEVANCE", "Traditional backend role with no meaningful AI responsibilities")\n                if self.metrics:\n                    self.metrics.record_rejection("Non-AI")'
)

# Location Work Mode Gate - Remote mismatch
inject(
    r'print\(f"  \[WORK MODE GATE\] \{job\.get\('"'"'title'"'"'\) @ \{job\.get\('"'"'company'"'"'\) \| \{location\}"\)\n\s*if self\.metrics:\n\s*self\.metrics\.record_rejection\("Work Mode"\)',
    r'self.record_decision(job, "Location Gate", "HYBRID_OUTSIDE_PUNE", "Remote policy mismatch")\n                if self.metrics:\n                    self.metrics.record_rejection("Work Mode")'
)

# Location Work Mode Gate - Outside target location
inject(
    r'print\(f"  \[LOCATION GATE\] \{job\.get\('"'"'title'"'"'\) @ \{job\.get\('"'"'company'"'"'\) \| \{location\}"\)\n\s*if self\.metrics:\n\s*self\.metrics\.record_rejection\("Location"\)',
    r'self.record_decision(job, "Location Gate", "LOCATION_OUTSIDE_PUNE", "Role outside target location")\n                if self.metrics:\n                    self.metrics.record_rejection("Location")'
)

# AI Score Batch - Below threshold
inject(
    r'print\(\n\s*f"  \[LOW AI SCORE \{score\}\] "\n\s*f"\{job\.get\('"'"'title'"'"'\) @ \{job\.get\('"'"'company'"'"'\)"\n\s*\)\n\s*if self\.metrics:\n\s*self\.metrics\.record_rejection\("Low AI Score"\)',
    r'self.record_decision(job, "AI Score Gate", "LOW_MATCH_SCORE", "Low production AI relevance score", ai_explanation=result.get("reason", ""), score=score, threshold=min_apply_score)\n                if self.metrics:\n                    self.metrics.record_rejection("Low AI Score")'
)

# Post Score Guard
inject(
    r'print\(\n\s*f"  \[POST-SCORE GUARD \{score\}\] "\n\s*f"\{job\.get\('"'"'title'"'"'\) @ \{job\.get\('"'"'company'"'"'\)"\n\s*\)\n\s*if self\.metrics:\n\s*self\.metrics\.record_rejection\("Low AI Score"\)',
    r'self.record_decision(job, "Post Score Guard", "LOW_MATCH_SCORE", "Score dropped below threshold after penalties", score=score, threshold=min_apply_score)\n                if self.metrics:\n                    self.metrics.record_rejection("Low AI Score")'
)


with open("src/client/job_classifier.py", "w") as f:
    f.write(code)

