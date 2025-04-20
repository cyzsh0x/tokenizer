import random
import string
import uuid
import requests
import sys
import os
import time
from rich.console import Console
from rich.panel import Panel

def loading(duration: float = 2, message: str = "Processing") -> None:
    """Display a loading animation"""
    symbols = ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷']
    end_time = time.time() + duration
    while time.time() < end_time:
        for symbol in symbols:
            print(f"\033[94m  {symbol} {message}...\033[0m", end='\r')
            time.sleep(0.1)
    print(" " * (len(message) + 10), end='\r')

def print2(t, d, c):
    Console().print(Panel(d, title=t, width=None, padding=(1, 3), style=c))
    
def print3(title, content, color):
    """Print tokens in a clean, copy-friendly format"""
    console = Console()
    
    # Title with color
    console.print(f"[{color}]{title}[/{color}]")
    
    # Content without box (plain text)
    console.print(content, markup=False, highlight=False)
    
    # Separator line for visual clarity
    console.print(f"[{color}]{'─' * 59}[/{color}]\n")

def clear():
    platform = sys.platform.lower()
    if 'linux' in platform:
        os.system('clear')
    elif 'win' in platform:
        os.system('cls')
    else:
        pass

class FacebookTokenGetter:
    def __init__(self):
        self.useragent = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1"
        self.endpoints = {
            "b_graph": "https://b-graph.facebook.com",
            "key": "https://b-api.facebook.com",
            "business": "https://business.facebook.com"
        }
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.useragent,
            'Accept-Language': 'en_US'
        })

    def get_eaaau_token(self, email, password):
        try:
            loading(3, "Authenticating")
            headers = {
                'authorization': 'OAuth 350685531728|62f8ce9f74b12f84c123cc23437a4a32',
                'x-fb-friendly-name': 'Authenticate',
                'x-fb-connection-type': 'Unknown',
                'accept-encoding': 'gzip, deflate',
                'content-type': 'application/x-www-form-urlencoded',
                'x-fb-http-engine': 'Liger'
            }
            data = {
                'adid': ''.join(random.choices(string.hexdigits, k=16)),
                'format': 'json',
                'device_id': str(uuid.uuid4()),
                'email': email,
                'password': password,
                'generate_analytics_claims': '0',
                'credentials_type': 'password',
                'source': 'login',
                'error_detail_type': 'button_with_disabled',
                'enroll_misauth': 'false',
                'generate_session_cookies': '0',
                'generate_machine_id': '0',
                'fb_api_req_friendly_name': 'authenticate',
            }
            
            response = self.session.post(
                f"{self.endpoints['b_graph']}/auth/login",
                headers=headers,
                data=data
            ).json()
            
            if 'session_key' in response:
                return {
                    "token": response["access_token"]
                }
            else:
                error = response.get('error', {})
                error_msg = error.get('message', 'Unknown error')
                return {"error": error_msg}
                
        except Exception as e:
            return {"error": str(e)}

    def get_eaad6v7_token(self, eaaau_token):
        try:
            loading(3, "Generating EAAD6V7 Token")
            url = f"{self.endpoints['key']}/method/auth.getSessionforApp?format=json&access_token={eaaau_token}&new_app_id=275254692598279"
            response = self.session.get(url).json()
            
            if 'access_token' in response:
                return {"token": response["access_token"]}
            else:
                return {"error": response.get('error', {}).get('message', 'Failed to get EAAD6V7 token')}
                
        except Exception as e:
            return {"error": str(e)}

    def get_eaag_token(self, cookies):
        try:
            loading(3, "Extracting EAAG Token")
            headers = {
                'authority': 'business.facebook.com',
                'cookie': cookies,
                'referer': 'https://www.facebook.com/',
                'user-agent': self.useragent
            }
            
            response = self.session.get(
                'https://business.facebook.com/content_management',
                headers=headers
            )
            
            if 'EAAG' in response.text:
                token = response.text.split('EAAG')[1].split('","')[0]
                return {"token": f"EAAG{token}"}
            return {"error": "EAAG token not found"}
            
        except Exception as e:
            return {"error": str(e)}

    def get_both_tokens(self, email, password):
        try:
            # Get EAAAAU token
            loading(3, "Getting EAAAAU Token")
            eaaau_result = self.get_eaaau_token(email, password)
            if "error" in eaaau_result:
                return {"error": f"EAAAAU: {eaaau_result['error']}"}
            
            # Get EAAD6V7 token
            loading(3, "Getting EAAD6V7 Token")
            eaad6v7_result = self.get_eaad6v7_token(eaaau_result["token"])
            if "error" in eaad6v7_result:
                return {
                    "eaaau": eaaau_result["token"],
                    "error": f"EAAD6V7: {eaad6v7_result['error']}"
                }
            
            return {
                "eaaau": eaaau_result["token"],
                "eaad6v7": eaad6v7_result["token"]
            }
                
        except Exception as e:
            return {"error": str(e)}

def display_error(error):
    error_messages = {
        "ACCOUNT_IN_CHECKPOINT": "\033[91m FAILED: ACCOUNT IN CHECKPOINT \033[0m",
        "2FA_ENABLED": "\033[91m FAILED: 2FA IS ENABLED. PLEASE DISABLE IT \033[0m",
        "WRONG_CREDENTIALS": "\033[91m FAILED: WRONG CREDENTIALS \033[0m",
        "ACCOUNT_NOT_EXIST": "\033[91m FAILED: ACCOUNT DOES NOT EXIST \033[0m",
        "REQUEST_LIMIT": "\033[91m FAILED: REQUEST LIMIT. USE VPN OR WAIT \033[0m",
        "MISSING_FIELDS": "\033[91m FAILED: PLEASE FILL ALL REQUIRED FIELDS \033[0m"
    }
    
    for key, msg in error_messages.items():
        if key in error.upper():
            print(msg)
            return
    
    print(f"\033[91m ERROR: {error}\033[0m")

def show_menu():
    clear()
    logo = r"""
 _____      _              _              
/__   \___ | | _____ _ __ (_)_______ _ __ 
  / /\/ _ \| |/ / _ \ '_ \| |_  / _ \ '__|
 / / | (_) |   <  __/ | | | |/ /  __/ |   
 \/   \___/|_|\_\___|_| |_|_/___\___|_|
                           """
    print2('', logo, 'violet')
    print2('', 'Facebook Token Getter by Cyzsh\n ~ github.com/cyzsh0x', 'violet')
    
    print("\n\033[95m [ OPTIONS ]\033[0m")
    print("\033[96m [1] Get EAAAAU & EAAD6V7 Tokens")
    print(" [2] Get EAAAAU Token")
    print(" [3] Get EAAD6V7 Token")
    print(" [4] Get EAAG Token")
    print(" [0] Exit\033[0m")

def main():
    fb = FacebookTokenGetter()
    
    while True:
        show_menu()
        choice = input('\n\033[0m [›] Select option :\033[90m ')
        
        if choice == '1':
            email = input('\033[0m [›] Email/Username :\033[90m ')
            password = input('\033[0m [›] Password       :\033[90m ')
            result = fb.get_both_tokens(email, password)
            
            if "error" in result:
                display_error(result["error"])
                if "eaaau" in result:
                    print("\n\033[92m[✓] EAAAAU Token\033[0m")
                    print3('', result['eaaau'], 'green')
            else:
                print("\n\033[92m [✓] Tokens retrieved successfully!\033[0m")
                print("\n\033[96mEAAAAU Token\033[0m")
                print3('', result['eaaau'], 'green')
                print("\n\033[96mEAAD6V7 Token\033[0m")
                print3('', result['eaad6v7'], 'green')
            
            input("\n\033[90m Press Enter to continue...\033[0m")
        
        elif choice == '2':
            email = input('\033[0m [›] Email/Username :\033[90m ')
            password = input('\033[0m [›] Password      :\033[90m ')
            result = fb.get_eaaau_token(email, password)
            
            if "token" in result:
                print("\n\033[92m[✓] EAAAAU Token\033[0m")
                print3('', result['token'], 'green')
            else:
                display_error(result.get("error", "Unknown error"))
            
            input("\n\033[90m Press Enter to continue...\033[0m")
        
        elif choice == '3':
            email = input('\033[0m [›] Email/Username :\033[90m ')
            password = input('\033[0m [›] Password       :\033[90m ')
            
            # First get EAAAAU token silently
            loading(3, "Getting EAAAAU Token")
            eaaau_result = fb.get_eaaau_token(email, password)
            if "error" in eaaau_result:
                display_error(eaaau_result["error"])
                input("\n\033[90m Press Enter to continue...\033[0m")
                continue
            
            # Then get EAAD6V7 token
            result = fb.get_eaad6v7_token(eaaau_result["token"])
            if "token" in result:
                print("\n\033[92m[✓] EAAD6V7 Token\033[0m")
                print3('', result['token'], 'green')
            else:
                display_error(result.get("error", "Unknown error"))
            
            input("\n\033[90m Press Enter to continue...\033[0m")
        
        elif choice == '4':
            cookies = input("\033[0m [›] Enter cookies :\033[90m ")
            result = fb.get_eaag_token(cookies)
            
            if "token" in result:
                print("\n\033[92m[✓] EAAG Token\033[0m")
                print3('', result['token'], 'green')
            else:
                display_error(result.get("error", "Unknown error"))
            
            input("\n\033[90m Press Enter to continue...\033[0m")
        
        elif choice == '0':
            print("\n\033[94m [+] Exiting...\033[0m")
            break
        
        else:
            print("\033[91m [!] Invalid option selected\033[0m")
            input("\n\033[90m Press Enter to continue...\033[0m")

if __name__ == "__main__":
    main()