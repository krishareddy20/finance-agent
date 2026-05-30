import sys
sys.path.insert(0, '.')
from tools.gmail_tool import GmailTool
g = GmailTool()
emails = g.get_unread_emails(max_results=5)
print(f'Connected! Found {len(emails)} unread emails.')
for e in emails[:3]:
    print(f'  - {e["subject"]}')