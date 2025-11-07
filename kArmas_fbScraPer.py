#!/usr/bin/env python3
"""
kArmas_fbScraPer.py v11.0 - PYTHON EDITION
THE ULTIMATE FACEBOOK CREDENTIAL & OSINT HARVESTER
MADE BY kArmasec - November 07, 2025

Features:
  - Full post + comment + reply scraping
  - Email, Phone, Password extraction
  - Undetectable via mbasic.facebook.com
  - Zero Selenium | Pure requests + BeautifulSoup
  - Auto "See More" & "View more comments"
  - Saves JSON + TXT credential dump

Usage:
  python3 kArmas_fbScraPer.py harvest "https://mbasic.facebook.com/groups/secretgroup" 100
"""

import requests
from bs4 import BeautifulSoup
import re
import sys
import time
import random
import json
from urllib.parse import urljoin
import os
from datetime import datetime

print("=" * 88)
print("  kArmas_fbScraPer.py v11.0 - FACEBOOK CREDENTIAL HARVESTER")
print("  MADE BY kArmasec")
print("  Emails | Phones | Passwords | Posts | Comments")
print("=" * 88 + "\n")

class kArmas_fbScraPer:
    def __init__(self, proxy=None):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': random.choice([
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/129.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/129 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/129 Firefox/129',
            ]),
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        if proxy:
            self.session.proxies.update({'http': proxy, 'https': proxy})
        
        self.cookies_file = f"kArmas_session_{int(time.time())}.txt"
        print(f"[+] Session: {self.cookies_file}")
        print(f"[+] User-Agent: {self.session.headers['User-Agent'][:60]}...\n")

    def login(self, email, password):
        print(f"[*] Logging in as {email}...")
        url = "https://mbasic.facebook.com/login"
        response = self.session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        form = soup.find('form', {'method': 'post'})
        if not form:
            print("[-] Login form not found!")
            return False
            
        data = {}
        for inp in form.find_all('input'):
            if inp.get('name') and inp.get('value') is not None:
                data[inp['name']] = inp['value']
        
        data.update({
            'email': email,
            'pass': password,
            'login': 'Log In'
        })
        
        login_url = urljoin(url, form['action'])
        resp = self.session.post(login_url, data=data)
        
        if 'Find Friends' in resp.text or 'feed_jewel' in resp.text:
            print("[+] LOGIN SUCCESSFUL — kArmas_fbScraPer IS ARMED\n")
            return True
        else:
            print("[-] Login failed. Check credentials or solve checkpoint.")
            return False

    def extract_credentials(self, text):
        creds = {'email': [], 'phone': [], 'password': []}
        
        # Emails
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        creds['email'] = list(set(emails))
        
        # Phones
        phones = re.findall(r'(\+?\d{1,4}[\s.-]?)?(\(?\d{3}\)?[\s.-]?)?[\d\s.-]{7,15}', text)
        clean_phones = []
        for p in [''.join(phone) for phone in phones]:
            digits = re.sub(r'\D', '', p)
            if len(digits) >= 10:
                clean_phones.append(p.strip())
        creds['phone'] = list(set(clean_phones))
        
        # Passwords
        pw1 = re.findall(r'(?:pass|pwd|password)[\s:]+([a-zA-Z0-9!@#$%^&*]{6,})', text, re.I)
        pw2 = re.findall(r'([a-zA-Z0-9!@#$%^&*]{8,})[\s]*(?:is|my|pass|password|pwd)', text, re.I)
        passwords = [p.strip() for p in pw1 + pw2 if len(p.strip()) >= 6]
        creds['password'] = list(set(passwords))
        
        return creds

    def harvest(self, url, limit=50):
        print(f"[*] HARVESTING: {url}")
        print(f"[*] Limit: {limit} posts\n")
        
        posts = []
        credentials = []
        count = 0
        next_url = url
        
        while next_url and count < limit:
            try:
                response = self.session.get(next_url, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find all post links
                post_links = []
                for h3 in soup.find_all('h3'):
                    a = h3.find('a', href=True)
                    if a and ('posts' in a['href'] or 'story.php' in a['href']):
                        post_links.append((a['href'], a.get_text(strip=True)))
                
                for link, author in post_links:
                    if count >= limit:
                        break
                        
                    post_url = urljoin("https://mbasic.facebook.com", link)
                    print(f"[{count}] {author} → ", end="")
                    
                    post_data = self.get_post(post_url)
                    post_data['author'] = author
                    
                    # Extract from post + comments
                    full_text = post_data['text']
                    for c in post_data['comments']:
                        full_text += " " + c['text']
                    
                    creds = self.extract_credentials(full_text)
                    if any(creds.values()):
                        cred_entry = {
                            'source': post_url,
                            'author': author,
                            **creds
                        }
                        credentials.append(cred_entry)
                        print("CREDENTIALS FOUND! ", end="")
                        if creds['email']: print(f"{len(creds['email'])}e ", end="")
                        if creds['phone']: print(f"{len(creds['phone'])}p ", end="")
                        if creds['password']: print(f"{len(creds['password'])}pwd ", end="")
                    
                    print()
                    posts.append(post_data)
                    count += 1
                
                # Next page
                next_link = soup.find('a', string=re.compile(r'See Older Posts|See More Posts', re.I))
                next_url = urljoin("https://mbasic.facebook.com", next_link['href']) if next_link else None
                
                time.sleep(3 + random.uniform(1, 4))
                
            except Exception as e:
                print(f"[-] Error: {e}")
                time.sleep(10)
                continue
        
        # Save results
        ts = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        with open(f"kArmas_posts_{ts}.json", 'w', encoding='utf-8') as f:
            json.dump(posts, f, indent=2, ensure_ascii=False)
        
        with open(f"kArmas_CREDENTIALS_{ts}.txt", 'w', encoding='utf-8') as f:
            f.write("=== kArmas_fbScraPer.py v11.0 CREDENTIAL HARVEST ===\n")
            f.write("MADE BY kArmasec\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            for c in credentials:
                f.write(f"SOURCE: {c['source']}\n")
                f.write(f"AUTHOR: {c['author']}\n")
                if c['email']: f.write(f"EMAIL: {', '.join(c['email'])}\n")
                if c['phone']: f.write(f"PHONE: {', '.join(c['phone'])}\n")
                if c['password']: f.write(f"PASS: {', '.join(c['password'])}\n")
                f.write("-" * 60 + "\n")
        
        print(f"\n[+] HARVEST COMPLETE")
        print(f"[+] Posts scraped: {count}")
        print(f"[+] Credential leaks: {len(credentials)}")
        print(f"[+] Saved:")
        print(f"    → kArmas_posts_{ts}.json")
        print(f"    → kArmas_CREDENTIALS_{ts}.txt")
        print(f"[+] MADE BY kArmasec\n")

    def get_post(self, url):
        response = self.session.get(url, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Post text
        text_div = soup.find('div', {'data-ft': True})
        text = text_div.get_text(strip=True) if text_div else ""
        
        # Comments
        comments = []
        for h3 in soup.find_all('h3'):
            a = h3.find('a', href=True)
            if a and a['href'].startswith('/'):
                comment_div = h3.find_next('div')
                comment_text = comment_div.get_text(strip=True) if comment_div else ""
                comments.append({
                    'author': a.get_text(strip=True),
                    'text': comment_text
                })
        
        # Load more comments
        more_links = soup.find_all('a', string=re.compile(r'View more comments|View previous comments', re.I))
        for link in more_links:
            more_url = urljoin("https://mbasic.facebook.com", link['href'])
            try:
                more_resp = self.session.get(more_url, timeout=30)
                more_soup = BeautifulSoup(more_resp.text, 'html.parser')
                for h3 in more_soup.find_all('h3'):
                    a = h3.find('a', href=True)
                    if a and a['href'].startswith('/'):
                        cdiv = h3.find_next('div')
                        ctext = cdiv.get_text(strip=True) if cdiv else ""
                        comments.append({
                            'author': a.get_text(strip=True),
                            'text': ctext
                        })
                time.sleep(2)
            except:
                pass
        
        return {'url': url, 'text': text, 'comments': comments}

# ====================== CLI ======================
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python3 kArmas_fbScraPer.py login <email> <password>")
        print("  python3 kArmas_fbScraPer.py harvest <url> [limit]")
        print("\nExample:")
        print("  python3 kArmas_fbScraPer.py harvest \"https://mbasic.facebook.com/groups/dataleaks\" 100")
        sys.exit(1)
    
    scraper = kArmas_fbScraPer()
    
    cmd = sys.argv[1].lower()
    
    if cmd == "login" and len(sys.argv) == 4:
        scraper.login(sys.argv[2], sys.argv[3])
    elif cmd == "harvest" and len(sys.argv) >= 3:
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 50
        scraper.harvest(sys.argv[2], limit)
    else:
        print("Invalid command.")
