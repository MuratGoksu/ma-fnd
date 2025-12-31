"""
Fact-Check Detector
Detects fact-check websites and extracts their ratings
"""
import re
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse
from bs4 import BeautifulSoup


class FactCheckDetector:
    """
    Detects fact-check websites and extracts their verdicts
    """
    
    # Fact-check site patterns
    FACT_CHECK_DOMAINS = {
        "politifact.com": {
            "name": "PolitiFact",
            "rating_patterns": [
                r'class="[^"]*m-meter[^"]*"[^>]*>.*?<span[^>]*>([^<]+)</span>',
                r'"rating":\s*"([^"]+)"',
                r'Truth-O-Meter[^>]*>([^<]+)<',
                r'(True|Mostly True|Half True|Mostly False|False|Pants on Fire)',
            ],
            "false_ratings": ["False", "Pants on Fire", "Mostly False"],
            "true_ratings": ["True", "Mostly True"],
            "unsure_ratings": ["Half True"]
        },
        "snopes.com": {
            "name": "Snopes",
            "rating_patterns": [
                r'rating[^>]*>([^<]+)<',
                r'"rating":\s*"([^"]+)"',
                r'(True|False|Mixture|Unproven|Outdated)',
            ],
            "false_ratings": ["False", "Mixture"],
            "true_ratings": ["True"],
            "unsure_ratings": ["Unproven", "Outdated"]
        },
        "factcheck.org": {
            "name": "FactCheck.org",
            "rating_patterns": [
                r'verdict[^>]*>([^<]+)<',
                r'(True|False|Misleading|Unproven)',
            ],
            "false_ratings": ["False", "Misleading"],
            "true_ratings": ["True"],
            "unsure_ratings": ["Unproven"]
        },
        "fullfact.org": {
            "name": "Full Fact",
            "rating_patterns": [
                r'verdict[^>]*>([^<]+)<',
                r'(True|False|Incorrect|Misleading)',
            ],
            "false_ratings": ["False", "Incorrect", "Misleading"],
            "true_ratings": ["True"],
            "unsure_ratings": []
        },
    }
    
    def __init__(self):
        pass
    
    def is_fact_check_site(self, url: str) -> bool:
        """Check if URL is from a fact-check website"""
        try:
            domain = urlparse(url).netloc.lower()
            for fact_check_domain in self.FACT_CHECK_DOMAINS.keys():
                if fact_check_domain in domain:
                    return True
            return False
        except Exception:
            return False
    
    def extract_fact_check_result(self, url: str, html_content: str) -> Optional[Dict[str, Any]]:
        """
        Extract fact-check rating from HTML content
        
        Returns:
            {
                "is_fact_check": True,
                "site_name": "PolitiFact",
                "rating": "False",
                "verdict": "FAKE",  # or "REAL" or "UNSURE"
                "confidence": 0.95
            }
        """
        if not self.is_fact_check_site(url):
            return None
        
        try:
            domain = urlparse(url).netloc.lower()
            site_config = None
            
            for fact_check_domain, config in self.FACT_CHECK_DOMAINS.items():
                if fact_check_domain in domain:
                    site_config = config
                    break
            
            if not site_config:
                return None
            
            # Try BeautifulSoup parsing first (more reliable)
            rating = None
            try:
                soup = BeautifulSoup(html_content, "html.parser")
                
                # PolitiFact specific: look for meter/rating classes
                if "politifact" in domain:
                    # First, check page text for rating keywords (most reliable)
                    page_text_lower = soup.get_text().lower()
                    
                    # Check in order of specificity
                    rating_keywords = [
                        ("pants on fire", "Pants on Fire"),
                        ("mostly false", "Mostly False"),
                        ("half true", "Half True"),
                        ("mostly true", "Mostly True"),
                        ("false", "False"),
                        ("true", "True")
                    ]
                    
                    # First, check for explicit "false false" pattern (common in PolitiFact HTML)
                    if "false false" in page_text_lower or '"false"' in html_content.lower():
                        # Check if it's in a rating context
                        false_idx = page_text_lower.find("false")
                        if false_idx >= 0:
                            context = page_text_lower[max(0, false_idx-100):min(len(page_text_lower), false_idx+100)]
                            if any(word in context for word in ["rating", "verdict", "meter", "truth", "fact", "check", "politifact", "rated", "class", "span"]):
                                rating = "False"
                    
                    # If not found, try keyword matching
                    if not rating:
                        for keyword, rating_value in rating_keywords:
                            if keyword in page_text_lower:
                                # Verify it's in a relevant context
                                idx = page_text_lower.find(keyword)
                                context = page_text_lower[max(0, idx-50):min(len(page_text_lower), idx+50)]
                                # More lenient - just check if it's not in a random place
                                if any(word in context for word in ["rating", "verdict", "meter", "truth", "fact", "check", "politifact", "rated"]):
                                    rating = rating_value
                                    break
                    
                    # Also check in specific elements (including class names)
                    if not rating:
                        # Check for class="false" or similar patterns
                        false_elements = soup.find_all(class_=re.compile(r"false|rating", re.I))
                        for elem in false_elements:
                            classes = elem.get("class", [])
                            if any("false" in str(c).lower() for c in classes):
                                # Verify it's a rating element
                                parent_text = elem.get_text(strip=True).lower()
                                if any(word in parent_text for word in ["rating", "verdict", "meter", "truth"]):
                                    rating = "False"
                                    break
                        
                        if not rating:
                            meter_divs = soup.find_all(class_=re.compile(r"meter|rating|truth", re.I))
                            for div in meter_divs:
                                text = div.get_text(strip=True).lower()
                                for keyword, rating_value in rating_keywords:
                                    if keyword in text:
                                        rating = rating_value
                                        break
                                if rating:
                                    break
                    
                    # Check h1/h2/h3 tags
                    if not rating:
                        for tag in soup.find_all(["h1", "h2", "h3", "title"]):
                            text = tag.get_text(strip=True).lower()
                            for keyword, rating_value in rating_keywords:
                                if keyword in text:
                                    rating = rating_value
                                    break
                            if rating:
                                break
                
                # Generic: look for rating/verdict elements
                if not rating:
                    rating_elements = soup.find_all(
                        class_=re.compile(r"rating|verdict|meter|truth", re.I)
                    )
                    for elem in rating_elements:
                        text = elem.get_text(strip=True)
                        # Check for known ratings
                        for possible_rating in ["True", "False", "Pants on Fire", "Mostly True", "Mostly False", "Half True", "Mixture", "Unproven"]:
                            if possible_rating.lower() in text.lower():
                                rating = possible_rating
                                break
                        if rating:
                            break
                
                # Fallback: search in all text (more aggressive)
                if not rating:
                    page_text = soup.get_text()
                    # Look for rating in title/headings first
                    for tag in soup.find_all(["title", "h1", "h2"]):
                        tag_text = tag.get_text()
                        for possible_rating in ["Pants on Fire", "Mostly False", "Half True", "Mostly True", "False", "True"]:
                            if possible_rating in tag_text:
                                rating = possible_rating
                                break
                        if rating:
                            break
                    
                    # If still not found, search entire page text
                    if not rating:
                        for possible_rating in ["Pants on Fire", "Mostly False", "Half True", "Mostly True", "False", "True"]:
                            if possible_rating in page_text:
                                # Check context - but be more lenient
                                idx = page_text.find(possible_rating)
                                if idx >= 0:
                                    context = page_text[max(0, idx-100):min(len(page_text), idx+100)]
                                    # More lenient context check
                                    if any(word in context.lower() for word in ["rating", "verdict", "meter", "truth", "rated", "fact", "check", "politifact"]):
                                        rating = possible_rating
                                        break
            except Exception:
                pass
            
            # Fallback to regex patterns if BeautifulSoup didn't work
            if not rating:
                # First, try to find "false" in class attributes or data attributes
                false_class_pattern = r'class=["\'][^"\']*false[^"\']*["\']'
                if re.search(false_class_pattern, html_content, re.IGNORECASE):
                    # Check context around it
                    matches = re.finditer(false_class_pattern, html_content, re.IGNORECASE)
                    for match in matches:
                        context = html_content[max(0, match.start()-100):min(len(html_content), match.end()+100)]
                        if any(word in context.lower() for word in ["rating", "verdict", "meter", "truth", "fact", "check"]):
                            rating = "False"
                            break
                
                # If still not found, try regex patterns
                if not rating:
                    for pattern in site_config["rating_patterns"]:
                        matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)
                        if matches:
                            rating = matches[0].strip()
                            # Clean up rating text
                            for possible_rating in ["True", "Mostly True", "Half True", "Mostly False", "False", "Pants on Fire"]:
                                if possible_rating.lower() in rating.lower():
                                    rating = possible_rating
                                    break
                            break
                
                # Last resort: search for "false" near rating-related keywords
                if not rating:
                    rating_contexts = [
                        r'(?:rating|verdict|meter|truth)[^>]*false',
                        r'false[^>]*(?:rating|verdict|meter|truth)',
                        r'class=["\'][^"\']*false[^"\']*["\']',
                        r'data-rating=["\']false["\']'
                    ]
                    for pattern in rating_contexts:
                        if re.search(pattern, html_content, re.IGNORECASE):
                            rating = "False"
                            break
            
            if not rating:
                return {
                    "is_fact_check": True,
                    "site_name": site_config["name"],
                    "rating": None,
                    "verdict": "UNSURE",
                    "confidence": 0.5
                }
            
            # Determine verdict based on rating
            rating_lower = rating.lower() if rating else ""
            verdict = "UNSURE"
            confidence = 0.5
            
            # CRITICAL: More aggressive matching - prioritize false ratings
            if rating and any(r.lower() in rating_lower for r in site_config["false_ratings"]):
                verdict = "FAKE"
                confidence = 0.92  # Fact-check sites are highly reliable (92% = 85-95% range when scaled)
            elif rating and any(r.lower() in rating_lower for r in site_config["true_ratings"]):
                verdict = "REAL"
                confidence = 0.92
            elif rating and any(r.lower() in rating_lower for r in site_config["unsure_ratings"]):
                verdict = "UNSURE"
                confidence = 0.6
            elif rating:
                # Fallback: if rating contains "false" or "fire", it's fake
                if "false" in rating_lower or "fire" in rating_lower or "pants" in rating_lower:
                    verdict = "FAKE"
                    confidence = 0.90
                elif "true" in rating_lower:
                    verdict = "REAL"
                    confidence = 0.90
            else:
                # If rating is None but we're on a fact-check site, be conservative
                verdict = "UNSURE"
                confidence = 0.5
            
            return {
                "is_fact_check": True,
                "site_name": site_config["name"],
                "rating": rating,
                "verdict": verdict,
                "confidence": confidence,
                "source_url": url
            }
        
        except Exception as e:
            return None
    
    def get_fact_check_verdict(self, url: str, html_content: str) -> Optional[Tuple[str, float]]:
        """
        Quick method to get verdict and confidence
        Returns: (verdict, confidence) or None
        """
        result = self.extract_fact_check_result(url, html_content)
        if result:
            return (result["verdict"], result["confidence"])
        return None

