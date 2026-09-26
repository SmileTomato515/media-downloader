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

def get_html(url, mobile=False, cookies=None):
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
    
    # Add cookies if provided (format: "name1=value1; name2=value2")
    if cookies:
        headers['Cookie'] = cookies
    
    try:
        response = scraper.get(url, headers=headers, timeout=15)
        
        # Precise login wall check: only the dedicated login page has this title
        if "Login • Instagram" in response.text or "login_required" in response.text:
            print(f"WARNING: Login wall detected for {url}")
            
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

def extract_media_from_node(node):
    """Extract best-quality media from an IG media node (image_versions2 or video_versions)."""
    if node.get('video_versions'):
        versions = node['video_versions']
        # Sort by resolution when available, else take first (highest quality)
        try:
            best = sorted(versions, key=lambda x: x.get('width', 0) * x.get('height', 0), reverse=True)[0]
        except Exception:
            best = versions[0]
        return {'type': 'video', 'url': best['url'],
                'width': best.get('width'), 'height': best.get('height')}
    if node.get('image_versions2'):
        candidates = node['image_versions2'].get('candidates', [])
        if not candidates:
            return {}
        # candidates[0] is always the highest-quality (original) in the new IG format
        # (no pWxH size restriction in its stp parameter)
        best = candidates[0]
        return {'type': 'image', 'url': best['url'],
                'width': node.get('original_width'), 'height': node.get('original_height')}
    return {}

def parse_instagram(url, cookies=None):
    print(f"Parsing Instagram: {url}")
    html = get_html(url, cookies=cookies)
    if not html: return None
    
    result = {'type': 'instagram', 'url': url, 'media': []}
    soup = BeautifulSoup(html, 'lxml')
    
    # Early login wall detection
    title_tag = soup.find('title')
    if title_tag and 'Login' in (title_tag.get_text() or ''):
        result['error'] = 'Instagram requires login. Please provide cookies in Advanced Options.'
        return result

    # Method 1: Try all application/json scripts first (highest quality)
    json_scripts = soup.find_all('script', type='application/json')
    for script in json_scripts:
        if not script.string or len(script.string) < 500:
            continue
        try:
            data = json.loads(script.string)
            
            # Look for carousel
            carousel = find_key(data, 'carousel_media')
            if carousel and isinstance(carousel, list):
                for child in carousel:
                    m = extract_media_from_node(child)
                    if m: result['media'].append(m)
                if result['media']:
                    print(f"  -> JSON script: found {len(result['media'])} media items")
                    return result
            
            # Look for single media with high resolution
            image_versions = find_key(data, 'image_versions2')
            video_versions = find_key(data, 'video_versions')
            
            if image_versions or video_versions:
                def find_media_nodes(obj, acc):
                    if isinstance(obj, dict):
                        # Check if it's a media node with original_height or high width
                        if 'image_versions2' in obj:
                            candidates = obj['image_versions2'].get('candidates', [])
                            if candidates and candidates[0].get('width', 0) > 500:
                                if obj not in acc:  # Avoid duplicates
                                    acc.append(obj)
                                return
                        elif 'video_versions' in obj:
                            if obj not in acc:
                                acc.append(obj)
                            return
                        for v in obj.values():
                            find_media_nodes(v, acc)
                    elif isinstance(obj, list):
                        for item in obj:
                            find_media_nodes(item, acc)
                
                nodes = []
                find_media_nodes(data, nodes)
                if nodes:
                    for node in nodes[:10]:  # Limit to first 10 to avoid profile pics
                        m = extract_media_from_node(node)
                        if m and m not in result['media']:
                            result['media'].append(m)
                    if result['media']:
                        print(f"  -> JSON script: found {len(result['media'])} media items")
                        return result
        except Exception:
            continue

    # Method 2: Legacy text search in regular scripts (contains image_versions2 as text)
    all_scripts = soup.find_all('script')
    for script in all_scripts:
        if not script.string or 'image_versions2' not in script.string:
            continue
        try:
            data = json.loads(script.string)
        except Exception:
            continue
        try:
            carousel = find_key(data, 'carousel_media')
            if carousel and isinstance(carousel, list):
                for child in carousel:
                    m = extract_media_from_node(child)
                    if m: result['media'].append(m)
            else:
                def find_media_nodes(obj, acc):
                    if isinstance(obj, dict):
                        if 'image_versions2' in obj and 'original_height' in obj:
                            acc.append(obj)
                            return
                        for v in obj.values():
                            find_media_nodes(v, acc)
                    elif isinstance(obj, list):
                        for item in obj:
                            find_media_nodes(item, acc)
                nodes = []
                find_media_nodes(data, nodes)
                if nodes:
                    m = extract_media_from_node(nodes[0])
                    if m: result['media'].append(m)
            if result['media']:
                print(f"  -> Text search: found {len(result['media'])} media items")
                return result
        except Exception as e:
            continue

    # Method 3: xdt_api legacy format
    for script in all_scripts:
        if script.string and 'xdt_api__v1__media__shortcode__web_info' in script.string:
            try:
                match = re.search(r'({.*"xdt_api__v1__media__shortcode__web_info".*})', script.string, re.DOTALL)
                if match:
                    data = json.loads(match.group(1))
                    media_info = find_key(data, 'xdt_api__v1__media__shortcode__web_info')
                    if media_info and 'items' in media_info:
                        item = media_info['items'][0]
                        if item.get('carousel_media'):
                            for child in item['carousel_media']:
                                m = extract_media_from_node(child)
                                if m: result['media'].append(m)
                        else:
                            m = extract_media_from_node(item)
                            if m: result['media'].append(m)
                        if result['media']:
                            print(f"  -> xdt_api: found {len(result['media'])} media items")
                            return result
            except Exception:
                continue

    # Method 4: Fallback to OG tags (usually low quality thumbnail)
    print("  -> Fallback to OG tags (may be low quality)")
    og_video = soup.find('meta', property='og:video')
    og_image = soup.find('meta', property='og:image')
    
    if og_video:
        result['media'].append({'type': 'video', 'url': og_video['content']})
    elif og_image:
        img_url = og_image.get('content', '')
        # ponytail: scontent-* CDNs serve user photos; static CDNs serve logos/placeholders
        if 'scontent' in img_url or '.fbcdn.net' in img_url:
            result['media'].append({'type': 'image', 'url': img_url})
        else:
            print(f"  -> OG image looks like a placeholder, skipping: {img_url[:80]}")
            result['error'] = 'Could not extract media. This post may require login – provide your Instagram cookies in Advanced Options.'
        
    return result

def parse_facebook(url, cookies=None):
    print(f"Parsing Facebook: {url}")
    # Use desktop user agent for RelayPrefetchedStreamCache
    html = get_html(url, mobile=False, cookies=cookies)
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
                                    img_url = uri_match.group(1).replace('\\/', '/')
                                    # Avoid duplicates
                                    if not any(x['url'] == img_url for x in result['media']):
                                        result['media'].append({'type': 'image', 'url': img_url})
                        except:
                            pass
                        
            except Exception as e:
                print(f"FB Relay error: {e}")

    if result['media']:
        return result

    # 2. Fallback to Mobile Parsing (Old method)
    print("  -> Fallback to Mobile Parsing")
    html_mobile = get_html(url, mobile=True, cookies=cookies)
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

def parse_threads(url, cookies=None):
    print(f"Parsing Threads: {url}")
    html = get_html(url, cookies=cookies)
    if not html: return None
    
    result = {'type': 'threads', 'url': url, 'media': []}
    soup = BeautifulSoup(html, 'lxml')
    
    # Extract Shortcode - support both /post/, /t/, and /share/ formats
    shortcode_match = re.search(r'/(?:post|t|share)/([^/?]+)', url)
    target_shortcode = shortcode_match.group(1) if shortcode_match else None
    
    # ponytail: /share/ links redirect to the real post, extract actual shortcode from canonical URL
    if '/share/' in url:
        canonical = soup.find('link', rel='canonical')
        if canonical:
            canonical_url = canonical.get('href', '')
            # If canonical points to homepage, the share link is invalid
            if canonical_url in ['https://www.threads.com/', 'https://www.threads.com']:
                print(f"  -> Invalid /share/ link (canonical is homepage)")
                return result
            canonical_match = re.search(r'/post/([^/?]+)', canonical_url)
            if canonical_match:
                target_shortcode = canonical_match.group(1)
                print(f"  -> Resolved /share/ to shortcode: {target_shortcode}")
    
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
                # candidates[0] is highest quality
                best_image = candidates[0]
                media_list.append({'type': 'image', 'url': best_image['url'], 'width': best_image.get('width'), 'height': best_image.get('height')})
            return media_list
            
        return media_list

    # 1. Try to find the exact post by shortcode first (most accurate)
    if target_shortcode:
        scripts = soup.find_all('script', type='application/json')
        for script in scripts:
            if not script.string or len(script.string) < 1000:
                continue
            try:
                data = json.loads(script.string)
                
                # Find post node with matching code
                def find_post_by_code(obj, code):
                    if isinstance(obj, dict):
                        if obj.get('code') == code:
                            return obj
                        for v in obj.values():
                            result = find_post_by_code(v, code)
                            if result:
                                return result
                    elif isinstance(obj, list):
                        for item in obj:
                            result = find_post_by_code(item, code)
                            if result:
                                return result
                    return None
                
                post_node = find_post_by_code(data, target_shortcode)
                
                if post_node:
                    # ponytail: prioritize direct media over carousel (avoids picking up recommended content)
                    if post_node.get('video_versions') or post_node.get('image_versions2'):
                        # Single media post (image or video)
                        extracted = extract_threads_media(post_node)
                        if extracted:
                            result['media'].extend(extracted)
                            print(f"  -> Found {len(result['media'])} media items (direct)")
                            return result
                    elif post_node.get('carousel_media'):
                        # Carousel post
                        for item in post_node['carousel_media']:
                            extracted = extract_threads_media(item)
                            result['media'].extend(extracted)
                        if result['media']:
                            print(f"  -> Found {len(result['media'])} media items (carousel)")
                            return result
                            
            except Exception:
                continue
        
        # ponytail: if we have a specific shortcode but couldn't find it, don't fallback to guessing
        # The URL explicitly specified a post that doesn't exist or was deleted
        print(f"  -> Post with shortcode '{target_shortcode}' not found")
        return result
    
    # 2. Fallback: collect all carousels and prioritize video-heavy ones (only when no shortcode specified)
    scripts = soup.find_all('script', type='application/json')
    
    # ponytail: collect all carousels first, prioritize video-heavy ones
    all_carousels = []
    
    for script in scripts:
        if not script.string or len(script.string) < 1000:
            continue
        try:
            data = json.loads(script.string)
            
            # Find ALL carousels in this script
            def find_all_carousels(obj, acc):
                if isinstance(obj, dict):
                    if 'carousel_media' in obj and isinstance(obj['carousel_media'], list):
                        if len(obj['carousel_media']) > 0:
                            acc.append(obj['carousel_media'])
                    for v in obj.values():
                        find_all_carousels(v, acc)
                elif isinstance(obj, list):
                    for item in obj:
                        find_all_carousels(item, acc)
            
            carousels = []
            find_all_carousels(data, carousels)
            all_carousels.extend(carousels)
                        
        except Exception:
            continue
    
    # Process carousels: prioritize ones with videos
    if all_carousels:
        # Score each carousel: videos = 10 points, images = 1 point
        scored_carousels = []
        for carousel in all_carousels:
            score = 0
            video_count = 0
            for item in carousel:
                if item.get('video_versions'):
                    score += 10
                    video_count += 1
                elif item.get('image_versions2'):
                    score += 1
            scored_carousels.append((score, video_count, len(carousel), carousel))
        
        # Sort by score (desc), then video count (desc), then total items (desc)
        scored_carousels.sort(reverse=True)
        
        # Use the highest-scored carousel
        if scored_carousels:
            best_carousel = scored_carousels[0][3]
            for item in best_carousel:
                extracted = extract_threads_media(item)
                result['media'].extend(extracted)
            if result['media']:
                print(f"  -> Found {len(result['media'])} media items")
                return result
    
    # 2. Try single media (no carousel)
    for script in scripts:
        if not script.string or len(script.string) < 1000:
            continue
        try:
            data = json.loads(script.string)
            
            image_versions = find_key(data, 'image_versions2')
            video_versions = find_key(data, 'video_versions')
            
            if image_versions or video_versions:
                def find_media_nodes(obj, acc):
                    if isinstance(obj, dict):
                        if ('image_versions2' in obj or 'video_versions' in obj):
                            if obj.get('image_versions2'):
                                candidates = obj['image_versions2'].get('candidates', [])
                                if candidates and candidates[0].get('width', 0) > 500:
                                    acc.append(obj)
                                    return
                            elif obj.get('video_versions'):
                                acc.append(obj)
                                return
                        for v in obj.values():
                            find_media_nodes(v, acc)
                    elif isinstance(obj, list):
                        for item in obj:
                            find_media_nodes(item, acc)
                
                nodes = []
                find_media_nodes(data, nodes)
                if nodes:
                    extracted = extract_threads_media(nodes[0])
                    result['media'].extend(extracted)
                    if result['media']:
                        print(f"  -> Found {len(result['media'])} media items")
                        return result
                        
        except Exception as e:
            continue

    # 2. Fallback to OG (usually low quality thumbnail)
    if not result['media']:
        print("  -> Fallback to OG tags (may be low quality)")
        og_video = soup.find('meta', property='og:video')
        og_image = soup.find('meta', property='og:image')
        
        if og_video:
            result['media'].append({'type': 'video', 'url': og_video['content']})
        elif og_image:
            # ponytail: OG image is often a placeholder/thumbnail, not original
            result['media'].append({'type': 'image', 'url': og_image['content']})
        
    return result

def parse_xiutaku(url, cookies=None):
    """Parse xiutaku.com photo gallery pages, handling pagination."""
    print(f"Parsing Xiutaku: {url}")
    
    # Normalize URL: remove trailing slash, strip existing page params for base URL
    url = url.rstrip('/')
    base_url = re.sub(r'\?page=\d+', '', url)
    
    result = {'type': 'xiutaku', 'url': url, 'media': []}
    
    # Fetch the first page to determine total pages
    html = get_html(base_url, cookies=cookies)
    if not html:
        return result
    
    soup = BeautifulSoup(html, 'lxml')
    
    # Extract title for metadata
    title_tag = soup.find('title')
    if title_tag:
        result['title'] = title_tag.get_text(strip=True)
    
    # Determine total page count from pagination links
    total_pages = 1
    pagination = soup.find('nav', class_='pagination')
    if pagination:
        page_links = pagination.find_all('a', class_='pagination-link')
        for link in page_links:
            try:
                page_num = int(link.get_text(strip=True))
                if page_num > total_pages:
                    total_pages = page_num
            except (ValueError, TypeError):
                continue
    
    print(f"  -> Found {total_pages} page(s)")
    
    # Extract images from each page
    seen_urls = set()
    
    for page in range(1, total_pages + 1):
        if page == 1:
            page_html = html  # Already fetched
        else:
            page_url = f"{base_url}?page={page}"
            print(f"  -> Fetching page {page}: {page_url}")
            page_html = get_html(page_url, cookies=cookies)
            if not page_html:
                print(f"  -> Failed to fetch page {page}")
                continue
        
        page_soup = BeautifulSoup(page_html, 'lxml')
        
        # Find article content area
        article = page_soup.find('div', class_='article-fulltext')
        if not article:
            # Fallback: search entire page
            article = page_soup
        
        # Extract all img tags with .jpg URLs from i.xiutaku.com
        imgs = article.find_all('img')
        for img in imgs:
            src = img.get('src', '')
            if src and 'i.xiutaku.com' in src and src.endswith('.jpg'):
                if src not in seen_urls:
                    seen_urls.add(src)
                    result['media'].append({
                        'type': 'image',
                        'url': src,
                        'width': img.get('width'),
                        'height': img.get('height')
                    })
        
        # Small delay between pages to be polite
        if page < total_pages:
            time.sleep(0.5)
    
    print(f"  -> Total images found: {len(result['media'])}")
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
