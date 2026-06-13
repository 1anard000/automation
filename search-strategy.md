# Job Search Strategy — Liepin (Optimized)

## Search Terms (Will Run Automatically)

### Primary Searches (High Priority)
1. `产品经理 英语` — Product Manager + English
2. `出海 产品经理` — Going global Product Manager
3. `海外 产品经理` — Overseas Product Manager
4. `跨境 产品经理` — Cross-border Product Manager
5. `国际业务 产品经理` — International business Product Manager

### Secondary Searches (Medium Priority)
6. `英语 项目经理` — English Project Manager
7. `英语 策略经理` — English Strategy Manager
8. `英语 深圳` — English + Shenzhen (any role)
9. `英语 广州` — English + Guangzhou (any role)
10. `英语 香港` — English + Hong Kong (any role)

### Role-Specific Searches
11. `程序经理 英语` — Program Manager + English
12. `运营经理 英语` — Operations Manager + English
13. `业务经理 英语` — Business Manager + English
14. `市场经理 英语` — Marketing Manager + English

### Location-Specific Searches (All Roles)
15. `深圳 英语` — Shenzhen + English
16. `广州 英语` — Guangzhou + English
17. `香港 英语` — Hong Kong + English
18. `上海 英语` — Shanghai + English
19. `新加坡 英语` — Singapore + English

## Search Parameters

- **Platform:** Liepin (liepin.com)
- **Tool:** agent-browser
- **Frequency:** Mon/Thu at 9am Shanghai time
- **Jobs per search:** 40 (first page)
- **Deduplication:** Remove jobs already in database

## Grading Criteria

### Grade A (High Fit)
- English as working language explicitly mentioned
- International/overseas/cross-border focus
- Location: Shenzhen, Guangzhou, Hong Kong, Singapore
- Experience: 3-10 years
- Salary: 25k+ or competitive

### Grade B (Medium Fit)
- English mentioned but not primary language
- Product/program/strategy role
- Location matches target cities
- Experience: 2-5 years
- Salary: 15-25k

### Grade C (Lower Fit)
- English mentioned but not verified
- General PM role
- Location: Other cities
- Salary: <15k
- Very technical roles

### Grade D (Skip)
- No English mentioned
- Pure engineering roles
- Entry-level
- Location not in target cities

## Output Structure

```
/job-database.html (main dashboard)
  - Summary of all jobs by location and grade
  - Links to individual job pages

/jobs/job-{{id}}.html (individual job)
  - Full job details
  - Apply link
  - Cover letter template
  - Notes/updates
```

## Automation Workflow

1. Run all search terms via agent-browser
2. Extract job data
3. Deduplicate against existing jobs
4. Grade each job
5. Generate individual HTML pages using template
6. Update main dashboard
7. Git commit & push
8. Send WeChat summary (new jobs + top picks)