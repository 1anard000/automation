-- Sample data for Personal CRM testing
-- Run this to populate your CRM database with test contacts

-- Insert sample contacts
INSERT OR IGNORE INTO contacts (id, name, email, company, title, location, linkedin_url, how_we_met, notes, relationship_health_score, last_contact_date, created_at) VALUES
(1, 'Sarah Chen', 'sarah.chen@nvidia.com', 'NVIDIA', 'Senior Product Manager', 'San Francisco, CA', 'https://linkedin.com/in/sarahchen', 'Tech conference 2023', 'Interested in AI/ML products. Follow up about partnership opportunities.', 85, '2026-06-01', datetime('now')),
(2, 'Michael Rodriguez', 'm.rodriguez@tesla.com', 'Tesla', 'Engineering Director', 'Austin, TX', 'https://linkedin.com/in/mrodriguez', 'LinkedIn outreach', 'Looking for senior engineers. Discussed potential roles.', 72, '2026-05-28', datetime('now')),
(3, 'Emily Watson', 'emily.w@stripe.com', 'Stripe', 'Staff Software Engineer', 'Seattle, WA', 'https://linkedin.com/in/emilywatson', 'University alumni event', 'Stanford alum. Expert in payments infrastructure.', 68, '2026-05-15', datetime('now')),
(4, 'David Kim', 'david.kim@a16z.com', 'Andreessen Horowitz', 'General Partner', 'Menlo Park, CA', 'https://linkedin.com/in/davidkim', 'Warm intro from John', 'VC contact. Interested in AI startups.', 90, '2026-06-05', datetime('now')),
(5, 'Lisa Thompson', 'lisa.t@ycombinator.com', 'Y Combinator', 'Partner', 'San Francisco, CA', 'https://linkedin.com/in/lisathompson', 'Demo Day 2024', 'Met at YC Demo Day. Follow up on portfolio companies.', 45, '2026-04-20', datetime('now')),
(6, 'James Park', 'james.park@google.com', 'Google', 'VP of Engineering', 'Mountain View, CA', 'https://linkedin.com/in/jamespark', 'Previous colleague', 'Worked together at startup. Now at Google Cloud.', 78, '2026-05-30', datetime('now')),
(7, 'Anna Kowalski', 'anna.k@sequoiacap.com', 'Sequoia Capital', 'Principal', 'San Francisco, CA', 'https://linkedin.com/in/annakowalski', 'Coffee chat referral', 'Focus on enterprise software. Good connection.', 55, '2026-05-10', datetime('now')),
(8, 'Robert Zhang', 'robert.z@meta.com', 'Meta', 'Research Scientist', 'Menlo Park, CA', 'https://linkedin.com/in/robertzhang', 'AI research conference', 'Expert in LLMs. Potential collaboration.', 82, '2026-06-03', datetime('now')),
(9, 'Jennifer Lee', 'jennifer.lee@apple.com', 'Apple', 'Senior Designer', 'Cupertino, CA', 'https://linkedin.com/in/jenniferlee', 'Design workshop', 'Met at design thinking workshop.', 35, '2026-03-15', datetime('now')),
(10, 'Thomas Mueller', 't.mueller@amazon.com', 'Amazon', 'Principal Engineer', 'Seattle, WA', 'https://linkedin.com/in/thomasmueller', 'AWS re:Invent', 'AWS expert. Discussed cloud architecture.', 62, '2026-05-22', datetime('now')),
(11, 'Maria Garcia', 'maria.g@openai.com', 'OpenAI', 'Research Engineer', 'San Francisco, CA', 'https://linkedin.com/in/mariagarcia', 'AI safety summit', 'Working on alignment research.', 88, '2026-06-06', datetime('now')),
(12, 'Kevin O''Brien', 'kevin.ob@accel.com', 'Accel', 'Associate', 'Palo Alto, CA', 'https://linkedin.com/in/kevinobrien', 'VC networking event', 'Early stage investor. Good to keep in touch.', 40, '2026-04-10', datetime('now')),
(13, 'Rachel Green', 'rachel.green@figma.com', 'Figma', 'Head of Product', 'San Francisco, CA', 'https://linkedin.com/in/rachelgreen', 'Product conference', 'Product strategy expert.', 75, '2026-05-25', datetime('now')),
(14, 'Daniel Brown', 'daniel.b@anthropic.com', 'Anthropic', 'ML Engineer', 'San Francisco, CA', 'https://linkedin.com/in/danielbrown', 'AI meetup', 'Working on Claude. Interesting perspectives.', 70, '2026-05-20', datetime('now')),
(15, 'Sophie Martin', 'sophie.m@notion.so', 'Notion', 'Growth Lead', 'New York, NY', 'https://linkedin.com/in/sophiemartin', 'Growth marketing webinar', 'Met in virtual event. Discuss growth strategies.', 25, '2026-02-28', datetime('now'));

-- Insert sample interactions
INSERT OR IGNORE INTO interactions (contact_id, interaction_type, date, notes, created_at) VALUES
(1, 'coffee', '2026-06-01', 'Great coffee chat at Blue Bottle. Discussed AI product strategy and potential collaboration on ML tools.', datetime('now')),
(1, 'email', '2026-05-15', 'Sent follow-up email with deck about our platform.', datetime('now')),
(2, 'call', '2026-05-28', 'Phone call about engineering roles at Tesla. He''s looking for senior backend engineers.', datetime('now')),
(3, 'meeting', '2026-05-15', 'Alumni networking event at Stanford. Caught up on her work at Stripe.', datetime('now')),
(4, 'coffee', '2026-06-05', 'Excellent meeting. Discussed AI startup landscape. He''s interested in seeing our pitch deck.', datetime('now')),
(5, 'email', '2026-04-20', 'Sent update about our progress. Need to follow up more consistently.', datetime('now')),
(6, 'call', '2026-05-30', 'Catching up since we last worked together. He''s happy at Google Cloud.', datetime('now')),
(7, 'coffee', '2026-05-10', 'Coffee at Philz. Discussed enterprise software trends.', datetime('now')),
(8, 'meeting', '2026-06-03', 'Research discussion at Meta. Potential collaboration on LLM safety.', datetime('now')),
(9, 'email', '2026-03-15', 'Sent design collaboration proposal. No response yet - need to follow up.', datetime('now')),
(10, 'call', '2026-05-22', 'Discussed AWS architecture best practices.', datetime('now')),
(11, 'coffee', '2026-06-06', 'Fascinating conversation about AI alignment at OpenAI.', datetime('now')),
(12, 'email', '2026-04-10', 'Initial outreach email. Should follow up.', datetime('now')),
(13, 'meeting', '2026-05-25', 'Product strategy discussion at Figma HQ.', datetime('now')),
(14, 'coffee', '2026-05-20', 'AI meetup at Anthropic. Discussed Claude development.', datetime('now')),
(15, 'email', '2026-02-28', 'Growth marketing discussion. Haven''t followed up - relationship getting cold.');

-- Insert sample reminders
INSERT OR IGNORE INTO reminders (contact_id, due_date, note, status, created_at) VALUES
(5, '2026-06-10', 'Follow up on YC portfolio companies discussion', 'pending', datetime('now')),
(9, '2026-06-08', 'Send design collaboration follow-up', 'pending', datetime('now')),
(12, '2026-06-15', 'Check in with Kevin about deal flow', 'pending', datetime('now')),
(15, '2026-06-09', 'Reconnect about growth strategies', 'pending', datetime('now')),
(3, '2026-06-20', 'Coffee catch-up with Emily', 'pending', datetime('now')),
(7, '2026-06-25', 'Lunch with James', 'pending', datetime('now'));
