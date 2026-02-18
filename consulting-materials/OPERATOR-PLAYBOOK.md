# OPERATOR PLAYBOOK
## Run MCP Implementation Service Without Coding

---

## YOUR ROLE

You are the **implementation operator**, not a software engineer.

**What you do:**
- Map client workflows and pain points
- Configure systems using checklists
- Test and validate automations
- Train users and hand off documentation
- Provide monthly support and optimization

**What you DON'T do:**
- Write code from scratch
- Debug complex Python errors
- Build custom features (hire a freelancer for this)

**Goal:** 80% of installs are checklist-driven, 20% need light custom work.

---

## PHASE 1: DISCOVERY (Day 1-2)

### Discovery Call Checklist

Use this exact list on every call:

**1. Business Context**
- [ ] What industry/business model?
- [ ] Team size using Claude?
- [ ] Current Claude plan (Team/Enterprise)?

**2. Current Pain Points**
- [ ] What tools do they switch between daily?
- [ ] Estimate hours lost per week per person
- [ ] What's the most painful manual task?

**3. Technical Landscape**
- [ ] What systems do they use? (list all: Slack, GitHub, Stripe, databases, CRMs)
- [ ] Do they have API access to those systems?
- [ ] Who manages API keys/credentials? (IT admin name + contact)

**4. Success Criteria**
- [ ] What would make this a "win" for them?
- [ ] What's their timeline expectation?
- [ ] What's their budget range?

**5. Technical Feasibility Quick Check**
- [ ] Can they provide API credentials?
- [ ] Can they install software on team machines?
- [ ] Do they have someone technical to coordinate with you?

### After the Call

**Deliverable: Implementation Plan (1-page doc)**

```
CLIENT: [Company Name]
DATE: [Today's date]

WORKFLOWS TO IMPLEMENT:
1. [Workflow name] - connects [System A] + [System B]
   Example prompt: "Show me..."
   
2. [Workflow name] - connects [System C]
   Example prompt: "Create..."

SYSTEMS NEEDED:
- System 1: [API access required? Yes/No]
- System 2: [API access required? Yes/No]

TIMELINE:
- Week 1: Setup + credentials
- Week 2: Install + testing
- Week 3: Rollout + training

INVESTMENT:
- Initial install: $[amount]
- Monthly support: $[amount]/month (optional)

NEXT STEP:
Kickoff call [date/time]
```

Send this within 24 hours of discovery call.

---

## PHASE 2: PRE-INSTALL PREP (Day 3-5)

### Credentials Collection Checklist

Send this exact template to your client's IT contact:

```
Hi [Name],

To set up your Claude Desktop automation, I need the following credentials.

REQUIRED:
☐ Anthropic API key (for Claude)
   - Get it here: https://console.anthropic.com/
   - Permissions needed: "Messages" access

☐ [System 1 name] API key
   - How to get it: [link to their docs]
   - Permissions needed: [list specific permissions]

☐ [System 2 name] API key
   - How to get it: [link]
   - Permissions needed: [list]

SECURITY NOTE:
These credentials stay on your team's machines only. They are never stored externally.

Please reply with these by [date].

Thanks,
[Your name]
```

### Installation Planning

**For each client machine that needs this:**
- [ ] Windows, Mac, or Linux?
- [ ] Do they have Docker installed? (if not, add 30 min to timeline)
- [ ] Do they have Claude Desktop installed?
- [ ] Who will you do the install session with? (name + calendar link)

---

## PHASE 3: INSTALLATION (Week 1-2)

### Standard Install Process (2-3 hours per machine)

**Session 1: Initial Setup (1 hour)**

Do this live with the client over Zoom/screen-share:

1. **Verify Prerequisites**
   - [ ] Docker Desktop is running
   - [ ] Claude Desktop is installed and logged in
   - [ ] You have all API credentials ready

2. **Install MCP Server**
   
   Open PowerShell and run:
   ```
   cd C:\Users\[username]\mcp-consulting-kit\showcase-servers\[server-name]
   docker build -t [server-name] .
   ```
   
   This takes 2-5 minutes. You'll see lots of text scroll by — that's normal.

3. **Create Environment File**
   
   In the same folder, create a file called `.env` (yes, it starts with a dot).
   
   Copy this template and fill in their real values:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   API_KEY=your-secure-random-key-here
   SLACK_BOT_TOKEN=xoxb-...
   GITHUB_TOKEN=ghp_...
   DB_URL=postgresql://user:pass@host:5432/dbname
   ```

4. **Start the Server**
   ```
   docker run --env-file .env -p 8101:8101 [server-name]
   ```
   
   You should see: `Uvicorn running on http://0.0.0.0:8101`

5. **Test Basic Connection**
   
   Open another PowerShell window:
   ```
   curl http://localhost:8101/health
   ```
   
   Should return: `{"status":"ok"}`

**Session 2: Claude Desktop Integration (30 min)**

Configure Claude Desktop to use the MCP server:

1. Open Claude Desktop settings
2. Add MCP server configuration
3. Test with a simple prompt
4. Verify response comes from the server

**Session 3: Workflow Testing (1 hour)**

Test each workflow from your Implementation Plan:

- [ ] Workflow 1: [test prompt] → [expected result]
- [ ] Workflow 2: [test prompt] → [expected result]
- [ ] Workflow 3: [test prompt] → [expected result]

Document any issues and adjust configuration.

---

## PHASE 4: ROLLOUT & TRAINING (Week 2-3)

### Team Training Session (45 min)

**Agenda template:**

1. **Overview (5 min)**
   - "This is your new Claude automation. It connects [systems] so you don't have to switch windows."

2. **Demo (15 min)**
   - Show 3-5 example prompts live
   - Show results in real-time
   - Emphasize natural language (no special syntax)

3. **Hands-On (20 min)**
   - Have each person try 2-3 prompts
   - Watch for confusion and clarify
   - Answer questions

4. **Next Steps (5 min)**
   - Share documentation
   - Share support contact info
   - Schedule 1-week check-in

### Handoff Documentation

Create a simple 1-page doc for the team:

```
# [Workflow Name] Quick Reference

## What This Does
[1-sentence explanation]

## How to Use It

**Example 1: [Task name]**
Prompt: "Show me..."
Result: You'll see...

**Example 2: [Task name]**
Prompt: "Create a..."
Result: Claude will...

**Example 3: [Task name]**
Prompt: "Find all..."
Result: You'll get...

## Common Questions

Q: What if I get an error?
A: [Brief troubleshooting tip]

Q: Can I use this for [X]?
A: [Yes/No + explanation]

## Support
- Email: [your email]
- Response time: Within 4 hours (business days)
- Monthly support includes: fixes, updates, new workflow requests
```

---

## PHASE 5: MONTHLY SUPPORT (Ongoing)

### What "Monthly Support" Includes

**Included in retainer:**
- Bug fixes and error troubleshooting
- Credential rotation/updates
- Adding 1-2 new simple workflows per month
- Performance monitoring
- Security updates
- Quarterly optimization review

**NOT included (charge extra):**
- Major new system integrations (quote separately)
- Custom feature development (hire freelancer)
- Architectural redesigns

### Monthly Check-In Template (15 min call)

Schedule this recurring monthly call:

**Agenda:**
1. Review usage stats (how often are they using it?)
2. Collect feedback (what's working? what's not?)
3. Address any issues
4. Propose 1-2 optimization ideas
5. Confirm next month's billing

**If they're not using it much:**
- Ask why (too complex? doesn't solve real problem?)
- Offer to simplify or adjust workflows
- If still no usage after 2 months, suggest pausing

---

## COMMON ISSUES & FIXES

### "It's not working" Troubleshooting

**Step 1: Is the server running?**
```
curl http://localhost:8101/health
```
If this fails, restart Docker.

**Step 2: Are credentials valid?**
Check the `.env` file — did any API keys expire?

**Step 3: Check logs**
```
docker logs [container-id]
```
Look for error messages in red.

**Step 4: Test with simple prompt**
Try: "List all tables" (for database server)
If this works, issue is with specific workflow, not system.

### When to Bring in a Freelancer

**You can handle:**
- Configuration changes
- Credential updates
- Simple workflow adjustments
- Documentation updates

**Hire help for:**
- Error messages you don't understand after 30 min
- Custom API integrations not in the showcase servers
- Performance/scaling issues
- Security incidents

**Where to find help:**
- Upwork: search "Python FastAPI developer"
- Rate: $50-$100/hour
- Scope: "Fix specific error" or "Add integration for [tool]"

---

## PRICING & SALES PROCESS

### Service Packages

**Starter - $2,500**
- 1-2 workflows
- 1 system integration
- 1 week delivery
- 30 days support

**Professional - $7,500** ⭐ MOST COMMON
- 3-5 workflows
- 2-3 system integrations
- 2 weeks delivery
- 90 days support

**Enterprise - $15,000+**
- Unlimited workflows
- Complex integrations
- 3 weeks delivery
- 6 months support

### Monthly Retainer Add-On

**Basic - $1,500/month**
- Bug fixes
- 1 new workflow/month
- Email support

**Premium - $3,000/month**
- Everything in Basic
- 3 new workflows/month
- Priority support
- Monthly optimization review

**Enterprise - $5,000+/month**
- Everything in Premium
- Dedicated Slack channel
- Custom development hours included

### Payment Process

**For installs:**
1. Send invoice: 50% upfront
2. Complete install
3. Send final invoice: 50% on go-live
4. Collect payment before handoff

**For retainers:**
1. Auto-charge on 1st of month
2. Use Stripe or PayPal subscriptions
3. Minimum 3-month commitment
4. Cancel with 30 days notice

---

## YOUR FIRST 30 DAYS

### Week 1: Setup

- [ ] Run one demo locally (pick Content Automation — easiest)
- [ ] Record a 2-minute Loom demo video
- [ ] Customize landing page with your contact info
- [ ] Set up Calendly for discovery calls

### Week 2: Outreach

- [ ] Send 10 cold emails using Template 1
- [ ] Post demo video on LinkedIn
- [ ] Post demo video on Twitter
- [ ] Engage with 5 relevant posts daily

### Week 3: First Sales

- [ ] Book 2-3 discovery calls
- [ ] Send Implementation Plans within 24 hours
- [ ] Close your first pilot install (offer 20% discount)

### Week 4: Deliver

- [ ] Complete first install
- [ ] Get testimonial quote
- [ ] Document your actual process
- [ ] Pitch monthly support during handoff

---

## SUCCESS METRICS

Track these weekly:

| Metric | Week 1 | Week 2 | Week 3 | Week 4 |
|--------|--------|--------|--------|--------|
| Emails sent | 10 | 20 | 30 | 40 |
| Responses | - | 2 | 4 | 6 |
| Calls booked | - | 1 | 2 | 3 |
| Installs closed | - | - | 1 | 1 |
| MRR from retainers | $0 | $0 | $0 | $1,500 |

**Month 3 goal:** 6 installs completed, 3 retainer clients, $6k/month MRR

---

## WHEN YOU'RE STUCK

**Can't figure out technical issue?**
- Google the error message
- Ask ChatGPT to explain it
- Hire Upwork freelancer ($50-100)

**Client ghosting after install?**
- Send check-in: "How's it going?"
- If no response in 1 week, send: "Can I help troubleshoot?"
- If still nothing, note in CRM and move on

**Not getting responses to outreach?**
- Your subject line might be generic (make it specific to them)
- Timing might be bad (try Tuesday 10am)
- Offer might not be clear (focus on one pain point)

**Feeling overwhelmed?**
- You don't need 10 clients right now
- Focus on 1-2 great installs per month
- Quality > quantity in year 1

---

## NEXT STEP

Ready to run your first demo?

1. Pick a showcase server (I recommend Content Automation — simplest)
2. Follow the install steps in Phase 3
3. Test with a few example prompts
4. Record a 2-minute demo video

Then you're ready to start outreach.

Need help with any specific step? Just ask.
