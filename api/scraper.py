import requests
import cloudscraper
from bs4 import BeautifulSoup
import json
import re
import time
import sys

# Constants
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
MOBILE_USER_AGENT = 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36'

def get_html(url, mobile=False):
    # Use cloudscraper to bypass some bot detection
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'android' if mobile else 'windows',
            'desktop': not mobile
        }
    )

    headers = {
        'User-Agent': MOBILE_USER_AGENT if mobile else USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
    }
    try:
        response = scraper.get(url, headers=headers, timeout=15)
        
        # Check for login page
        if "Login • Instagram" in response.text or "Log In" in response.text:
            print(f"WARNING: Possible Login Wall detected for {url}")
            
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def find_key(obj, key):
    """Recursively find a key in a nested dictionary/list."""
    if isinstance(obj, dict):
        if key in obj: return obj[key]
        for k, v in obj.items():
            res = find_key(v, key)
            if res: return res
    elif isinstance(obj, list):
        for item in obj:
            res = find_key(item, key)
            if res: return res
    return None

def parse_instagram(url):
    print(f"Parsing Instagram: {url}")
    html = get_html(url)
    if not html: return None
    
    result = {'type': 'instagram', 'url': url, 'media': []}
    soup = BeautifulSoup(html, 'lxml')

    # Method 1: Try to find the new GraphQL-like JSON data
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string and 'xdt_api__v1__media__shortcode__web_info' in script.string:
            try:
                match = re.search(r'({.*"xdt_api__v1__media__shortcode__web_info".*})', script.string)
                if match:
                    data = json.loads(match.group(1))
                    media_info = find_key(data, 'xdt_api__v1__media__shortcode__web_info')
                    if media_info and 'items' in media_info:
                        item = media_info['items'][0]
                        
                        def extract_media_from_node(node):
                            media_item = {}
                            if node.get('video_versions'):
                                best_video = sorted(node['video_versions'], key=lambda x: x['width'] * x['height'], reverse=True)[0]
                                media_item = {'type': 'video', 'url': best_video['url'], 'width': best_video['width'], 'height': best_video['height']}
                            elif node.get('image_versions2'):
                                candidates = node['image_versions2']['candidates']
                                best_image = sorted(candidates, key=lambda x: x['width'] * x['height'], reverse=True)[0]
                                media_item = {'type': 'image', 'url': best_image['url'], 'width': best_image['width'], 'height': best_image['height']}
                            return media_item

                        if item.get('carousel_media'):
                            for child in item['carousel_media']:
                                m = extract_media_from_node(child)
                                if m: result['media'].append(m)
                        else:
                            m = extract_media_from_node(item)
                            if m: result['media'].append(m)
                            
                        if result['media']:
                            return result
            except Exception as e:
                print(f"Error parsing IG JSON: {e}")

    # Method 2: Fallback to Open Graph
    print("  -> Fallback to OG tags")
    og_video = soup.find('meta', property='og:video')
    og_image = soup.find('meta', property='og:image')
    
    if og_video:
        result['media'].append({'type': 'video', 'url': og_video['content']})
    elif og_image:
        result['media'].append({'type': 'image', 'url': og_image['content']})
        
    return result

def parse_facebook(url):
    print(f"Parsing Facebook: {url}")
    # Use desktop user agent for RelayPrefetchedStreamCache
    html = get_html(url, mobile=False)
    if not html: return None

    result = {'type': 'facebook', 'url': url, 'media': []}
    soup = BeautifulSoup(html, 'lxml')
    
    # 1. Try RelayPrefetchedStreamCache (New FB Video Structure)
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string and 'RelayPrefetchedStreamCache' in script.string:
            try:
                # Extract the JSON-like structure
                # It's usually inside require(...) or just a JSON object
                # We'll try to find the video data directly using regex on the script content
                # looking for "playable_url_quality_hd" or "playable_url"
                
                hd_match = re.search(r'"playable_url_quality_hd":"([^"]+)"', script.string)
                sd_match = re.search(r'"playable_url":"([^"]+)"', script.string)
                
                # New patterns for browser_native_url
                native_hd_match = re.search(r'"browser_native_hd_url":"([^"]+)"', script.string)
                native_sd_match = re.search(r'"browser_native_sd_url":"([^"]+)"', script.string)
                
                # Collect candidates
                hd_url = None
                sd_url = None
                
                if hd_match: hd_url = hd_match.group(1)
                elif native_hd_match: hd_url = native_hd_match.group(1)
                
                if sd_match: sd_url = sd_match.group(1)
                elif native_sd_match: sd_url = native_sd_match.group(1)
                
                # Add Video (Prioritize HD)
                if hd_url:
                    clean_url = hd_url.replace('\\/', '/')
                    if not any(x['url'] == clean_url for x in result['media']):
                        result['media'].append({'type': 'video', 'quality': 'hd', 'url': clean_url})
                elif sd_url:
                    clean_url = sd_url.replace('\\/', '/')
                    if not any(x['url'] == clean_url for x in result['media']):
                        result['media'].append({'type': 'video', 'quality': 'sd', 'url': clean_url})

                # Extract Images (Look for "image":{...} with width > 500)
                image_matches = re.finditer(r'"image":\s*\{[^}]+\}', script.string)
                for m in image_matches:
                    content = m.group(0)
                    if '"uri":' in content and '"width":' in content:
                        try:
                            w_match = re.search(r'"width":(\d+)', content)
                            uri_match = re.search(r'"uri":"([^"]+)"', content)
                            if w_match and uri_match:
                                width = int(w_match.group(1))
                                if width > 500:
                                    clean_url = uri_match.group(1).replace('\\/', '/')
                                    # Avoid duplicates
                                    if not any(x['url'] == clean_url for x in result['media']):
                                        result['media'].append({'type': 'image', 'url': clean_url})
                        except:
                            pass
                    if not any(x['url'] == clean_url for x in result['media']):
                        result['media'].append({'type': 'video', 'quality': 'sd', 'url': clean_url})
                        
            except Exception as e:
                print(f"FB Relay error: {e}")

    if result['media']:
        return result

    # 2. Fallback to Mobile Parsing (Old method)
    print("  -> Fallback to Mobile Parsing")
    html_mobile = get_html(url, mobile=True)
    if html_mobile:
        soup_mobile = BeautifulSoup(html_mobile, 'lxml')
        
        # Video Regex
        hd_src = re.search(r'"hd_src":"([^"]+)"', html_mobile)
        sd_src = re.search(r'"sd_src":"([^"]+)"', html_mobile)
        
        if hd_src:
            result['media'].append({'type': 'video', 'quality': 'hd', 'url': hd_src.group(1).replace('\\/', '/')})
        elif sd_src:
            result['media'].append({'type': 'video', 'quality': 'sd', 'url': sd_src.group(1).replace('\\/', '/')})
            
        # Images
        if not result['media']:
            divs = soup_mobile.find_all('div', attrs={'data-ploi': True})
            for div in divs:
                url = div['data-ploi']
                if not any(x['url'] == url for x in result['media']):
                    result['media'].append({'type': 'image', 'url': url})

    return result

def parse_threads(url):
    print(f"Parsing Threads: {url}")
    html = get_html(url)
    if not html: return None
    
    result = {'type': 'threads', 'url': url, 'media': []}
    soup = BeautifulSoup(html, 'lxml')
    
    # Extract Shortcode
    shortcode_match = re.search(r'/post/([^/?]+)', url)
    target_shortcode = shortcode_match.group(1) if shortcode_match else None
    
    # 1. Try ScheduledServerJS (New Threads Structure)
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string and 'ScheduledServerJS' in script.string:
            try:
                # Try to parse the script content as JSON directly
                try:
                    data = json.loads(script.string)
                except:
                    # If not valid JSON, try to extract the relevant part
                    # It might be inside require(...)
                    continue

                # Helper to extract from a post node
                def extract_threads_media(node):
                    media_list = []
                    
                    # Check for Carousel
                    if node.get('carousel_media'):
                        for item in node['carousel_media']:
                            media_list.extend(extract_threads_media(item))
                        return media_list

                    # Check for Video
                    if node.get('video_versions'):
                        videos = node['video_versions']
                        if videos:
                            best_video = sorted(videos, key=lambda x: x.get('width', 0) * x.get('height', 0), reverse=True)[0]
                            media_list.append({'type': 'video', 'url': best_video['url'], 'width': best_video.get('width'), 'height': best_video.get('height')})
                        return media_list
                    
                    # Check for Image
                    if node.get('image_versions2'):
                        candidates = node['image_versions2'].get('candidates', [])
                        if candidates:
                            best_image = sorted(candidates, key=lambda x: x.get('width', 0) * x.get('height', 0), reverse=True)[0]
                            media_list.append({'type': 'image', 'url': best_image['url'], 'width': best_image.get('width'), 'height': best_image.get('height')})
                        return media_list
                        
                    return media_list

                # Helper to find the specific post node by shortcode
                def find_post_node(obj, code):
                    if isinstance(obj, dict):
                        if obj.get('code') == code:
                            return obj
                        for k, v in obj.items():
                            found = find_post_node(v, code)
                            if found: return found
                    elif isinstance(obj, list):
                        for item in obj:
                            found = find_post_node(item, code)
                            if found: return found
                    return None

                if target_shortcode:
                    post_node = find_post_node(data, target_shortcode)
                    if post_node:
                        extracted = extract_threads_media(post_node)
                        result['media'].extend(extracted)
                        return result # Found the specific post, return immediately

            except Exception as e:
                print(f"Threads JSON error: {e}")

    # 2. Fallback to OG
    if not result['media']:
        og_video = soup.find('meta', property='og:video')
        og_image = soup.find('meta', property='og:image')
        
        if og_video:
            result['media'].append({'type': 'video', 'url': og_video['content']})
        elif og_image:
            result['media'].append({'type': 'image', 'url': og_image['content']})
        
    return result

def main():
    urls = [
        "https://www.instagram.com/p/DSFXUE2GC8u/?utm_source=ig_web_copy_link&igsh=NTc4MTIwNjQ2YQ==",
        "https://www.facebook.com/share/p/1Cgn85ERrX/",
        "https://www.threads.com/@jiyih9232/post/DS1QuNAEeto?xmt=AQF00waWvlSH_VgJvRAc1rz9cAjeea0lElL8zX6Ls_mmOw"
    ]
    
    print("--- Starting Scraper Test ---")
    for url in urls:
        if "instagram.com" in url:
            res = parse_instagram(url)
        elif "facebook.com" in url:
            res = parse_facebook(url)
        elif "threads.com" in url or "threads.net" in url:
            res = parse_threads(url)
        else:
            print(f"Unknown URL type: {url}")
            continue
            
        print(json.dumps(res, indent=2))
        print("-" * 30)
        time.sleep(2) # Be nice

if __name__ == "__main__":
    main()
