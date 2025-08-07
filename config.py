from datetime import datetime

# Telegram config
BOT_TOKEN = '8155238330:AAH2t2i3zk7v8yzGnP73bw0PiJTmpgI-Ovw'
CHAT_ID = '5713801301'

# Get today's date
today = datetime.now().strftime('%d-%m-%Y')

# Filter keywords common for all companies
FILTER_KEYWORDS = ['Senior', 'Middle', 'Lead', 'Manager', 'Head', 'Mid', 'Associate', 'Analyst',
                  'Medior', 'Consultant', 'Principal', 'Solution', 'Director', 'Customer',
                  'Business', 'PMO', 'Affiliate', 'Recruiter', 'Master', 'QC', 'Tester', 'QA',
                  'Test', 'Data', 'DevOps', 'AWS', 'Azure', 'Mobile', 'Game', 'IOS']