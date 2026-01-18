"""
Fake News Categorizer
Categorizes fake news into 7 subcategories with scores
"""
from typing import Dict, Any, List
import re


class FakeNewsCategorizer:
    """
    Categorizes fake news into subcategories:
    1. Dezenformasyon (Disinformation)
    2. Mezenformasyon (Misinformation)
    3. Propaganda
    4. Şaka/Gırgır (Satire/Humor)
    5. Hiciv (Parody)
    6. Tıklama yemi (Clickbait)
    7. Çerçöp haber (Junk news)
    """
    
    def __init__(self):
        self.categories = [
            "dezenformasyon",
            "mezenformasyon",
            "propaganda",
            "şaka_gırgır",
            "hiciv",
            "tıklama_yemi",
            "çerçöp_haber"
        ]
    
    def categorize(
        self,
        item: Dict[str, Any],
        analyses: Dict[str, Any],
        verdict: str,
        confidence: float,
        fact_check_result: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Categorize fake news with scores (0-100)
        
        Returns:
            {
                "is_fake": bool,
                "categories": {
                    "dezenformasyon": 0-100,
                    "mezenformasyon": 0-100,
                    ...
                },
                "primary_category": str,
                "overall_score": float
            }
        """
        # IMPORTANT: Check verdict first
        is_fake = (verdict == "FAKE")
        
        if not is_fake:
            return {
                "is_fake": False,
                "categories": {cat: 0 for cat in self.categories},
                "primary_category": None,
                "overall_score": 0.0
            }
        
        # Extract data - preserve original case for better analysis
        headline = item.get("headline", "")
        text = item.get("text", "")
        link = item.get("link", "")
        
        # Convert to lowercase for pattern matching, but keep original for length checks
        headline_lower = headline.lower()
        text_lower = text.lower()
        
        textual_analysis = analyses.get("textual_analysis", {})
        source_analysis = analyses.get("source_analysis", {})
        visual_analysis = analyses.get("visual_analysis", {})
        
        
        # Calculate scores for each category
        scores = {}
        
        # Use lowercase versions for pattern matching
        scores["dezenformasyon"] = self._score_disinformation(
            headline_lower, text_lower, textual_analysis, source_analysis, confidence
        )
        
        scores["mezenformasyon"] = self._score_misinformation(
            headline_lower, text_lower, textual_analysis, source_analysis, confidence
        )
        
        scores["propaganda"] = self._score_propaganda(
            headline_lower, text_lower, textual_analysis, source_analysis
        )
        
        scores["şaka_gırgır"] = self._score_satire(
            headline_lower, text_lower, textual_analysis
        )
        
        scores["hiciv"] = self._score_parody(
            headline_lower, text_lower, textual_analysis
        )
        
        scores["tıklama_yemi"] = self._score_clickbait(
            headline, text, textual_analysis, source_analysis  # Keep original for length checks
        )
        
        scores["çerçöp_haber"] = self._score_junk_news(
            headline, text, source_analysis, textual_analysis  # Keep original for length checks
        )
        
        # Find primary category (highest score)
        primary_category = max(scores.items(), key=lambda x: x[1])[0] if scores else None
        
        # Overall fake score calculation
        # SIMPLE AND CLEAR: Use average of top 3 categories (or all if less than 3)
        # This makes it easy for users to understand: if categories are 25%, 25%, 20%, overall = ~23%
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Filter out zero scores for calculation
        non_zero_scores = [(cat, score) for cat, score in sorted_scores if score > 0]
        
        if len(non_zero_scores) >= 3:
            # Simple average of top 3 categories
            top_3 = non_zero_scores[:3]
            overall_score = sum([score for _, score in top_3]) / 3.0
        elif len(non_zero_scores) >= 2:
            # Average of top 2 categories
            top_2 = non_zero_scores[:2]
            overall_score = sum([score for _, score in top_2]) / 2.0
        elif len(non_zero_scores) >= 1:
            # Single category - use it directly
            overall_score = non_zero_scores[0][1]
        else:
            # No category scores - use default based on verdict
            overall_score = 50.0 if verdict == "FAKE" else 0.0
        
        # If fact-check result exists, use it as a multiplier/adjustment
        # But keep it close to category scores
        if fact_check_result and fact_check_result.get("is_fact_check"):
            fact_check_confidence = confidence
            fact_check_score = fact_check_confidence * 100
            
            # If fact-check is very confident (90%+), boost overall score slightly
            # But never more than 1.3x the category average
            if fact_check_score >= 90:
                # Boost by max 30% if fact-check is very confident
                boost_factor = min(1.3, 1.0 + (fact_check_score - 90) / 100)
                overall_score = min(100, overall_score * boost_factor)
            else:
                # For lower fact-check confidence, use average of category and fact-check
                overall_score = (overall_score * 0.7) + (fact_check_score * 0.3)
        
        # Round to 1 decimal place for clarity
        overall_score = round(overall_score, 1)
        
        return {
            "is_fake": True,  # Always True if we reach here (verdict == "FAKE")
            "categories": scores,
            "primary_category": primary_category,
            "overall_score": round(overall_score, 1)
        }
    
    def _score_disinformation(
        self,
        headline: str,
        text: str,
        textual_analysis: Dict[str, Any],
        source_analysis: Dict[str, Any],
        confidence: float
    ) -> float:
        """Dezenformasyon skoru - kasıtlı yanlış bilgi (içeriğe göre dinamik)"""
        score = 0.0
        
        # Source credibility kontrolü
        source_cred = 0.5
        if source_analysis:
            source_cred = source_analysis.get("source_info", {}).get("credibility_score", 0.5)
        
        # Low source credibility + high confidence in fake = disinformation
        # Ama bu sabit değil, içeriğe göre ayarlanacak
        if source_cred < 0.3 and confidence > 0.7:
            base_score = 30
            # İçerik uzunluğuna göre ayarla
            if len(text) < 200:
                base_score += 10  # Kısa içerik = daha yüksek risk
            score += base_score
        elif source_cred >= 0.7:
            # Güvenilir kaynaklarda bu göstergeler normal olabilir
            # Ama yine de içeriğe göre kontrol et
            pass  # Devam et, ama daha düşük puanlar ver
        
        # Emotional manipulation indicators - textual analysis'ten al
        emotional_words = ["şok", "skandal", "ifşa", "gizli", "yasak", "saklanan", "ifşalandı"]
        emotional_count = sum(1 for word in emotional_words if word in headline or word in text)
        
        if emotional_count > 0:
            # Textual analysis'ten duygusal manipülasyon skorunu kullan
            if textual_analysis:
                analysis_data = textual_analysis.get("analysis", {})
                if isinstance(analysis_data, dict):
                    emotional_manip = analysis_data.get("emotional_manipulation", {})
                    if isinstance(emotional_manip, dict):
                        manip_score = emotional_manip.get("score", 0.0)
                        if manip_score > 0.6:
                            score += int(manip_score * 25) if source_cred < 0.5 else int(manip_score * 10)
                        else:
                            score += 10 if source_cred < 0.5 else 3
            else:
                # Fallback: kelime sayısına göre
                score += (emotional_count * 8) if source_cred < 0.5 else (emotional_count * 2)
        
        # Lack of evidence - içeriğe göre kontrol
        evidence_words = ["kaynak", "referans", "kanıt", "rapor", "çalışma", "araştırma"]
        has_evidence = any(word in text for word in evidence_words)
        
        if not has_evidence and len(text) > 300:  # Uzun metin ama kaynak yok
            score += 20 if source_cred < 0.5 else 8
        elif not has_evidence and len(text) < 200:  # Kısa metin, kaynak beklenmez
            score += 5 if source_cred < 0.5 else 2
        
        # Sensational language - içeriğe göre
        sensational_count = headline.count("!") + (1 if headline.isupper() and len(headline) > 10 else 0)
        if sensational_count > 0:
            score += (sensational_count * 8) if source_cred < 0.5 else (sensational_count * 2)
        
        # Political/divisive content - içeriğe göre
        political_words = ["hükümet", "parti", "iktidar", "muhalefet", "darbe", "siyaset"]
        political_count = sum(1 for word in political_words if word in text)
        
        if political_count >= 3:  # Çok fazla siyasi kelime
            score += 15 if source_cred < 0.4 else 5
        elif political_count >= 1:
            score += 8 if source_cred < 0.4 else 2
        
        # Textual analysis'ten gelen güven skorunu kullan
        if textual_analysis:
            text_confidence = textual_analysis.get("overall_confidence", 0.5)
            # Düşük güven + düşük kaynak güvenilirliği = dezenformasyon
            if text_confidence < 0.4 and source_cred < 0.4:
                score += 15
        
        return min(100, max(0, score))
    
    def _score_misinformation(
        self,
        headline: str,
        text: str,
        textual_analysis: Dict[str, Any],
        source_analysis: Dict[str, Any],
        confidence: float
    ) -> float:
        """Mezenformasyon skoru - yanlış ama kasıtsız bilgi"""
        score = 0.0
        
        # Source credibility kontrolü - içeriğe göre dinamik
        source_cred = 0.5
        if source_analysis:
            source_cred = source_analysis.get("source_info", {}).get("credibility_score", 0.5)
        
        # Medium source credibility but still fake = misinformation
        # Ama bu sabit değil, içeriğe göre değişmeli
        if 0.3 <= source_cred < 0.6 and confidence > 0.6:
            # Base score, ama içeriğe göre ayarlanacak
            base_score = 20
            # İçerik uzunluğuna göre ayarla
            if len(text) < 200:
                base_score += 10  # Kısa içerik = daha yüksek risk
            elif len(text) > 1000:
                base_score -= 5  # Uzun içerik = daha düşük risk
            score += base_score
        
        # Factual errors - textual_analysis'ten al
        if textual_analysis:
            analysis_data = textual_analysis.get("analysis", {})
            if isinstance(analysis_data, dict):
                fact_consistency = analysis_data.get("fact_consistency", {})
                if isinstance(fact_consistency, dict):
                    inconsistencies = fact_consistency.get("inconsistencies", [])
                    if inconsistencies:
                        score += min(30, len(inconsistencies) * 8)  # Max 30 puan
        
        # Outdated information - içeriğe göre kontrol
        outdated_patterns = ["geçen yıl", "önceki", "eski", "geçmişte", "daha önce"]
        outdated_count = sum(1 for pattern in outdated_patterns if pattern in text)
        if outdated_count > 0:
            score += min(20, outdated_count * 5)
        
        # Misleading statistics - içeriğe göre kontrol
        stat_patterns = [
            r'%\s*\d+', r'\d+\s*%', r'\d+\s*oranında', r'\d+\s*katı'
        ]
        stat_count = sum(1 for pattern in stat_patterns if re.search(pattern, text))
        if stat_count > 0:
            score += min(15, stat_count * 5)
        
        # Textual analysis'ten gelen güven skorunu kullan
        if textual_analysis:
            text_confidence = textual_analysis.get("overall_confidence", 0.5)
            # Düşük güven = yüksek misinformation riski
            if text_confidence < 0.4:
                score += 15
            elif text_confidence > 0.7:
                score -= 10  # Yüksek güven = düşük misinformation riski
        
        # Headline-text uyumsuzluğu
        if headline and text:
            headline_words = set(headline.lower().split()[:5])
            text_words = set(text.lower().split()[:30])
            overlap = len(headline_words & text_words) / len(headline_words) if headline_words else 0
            if overlap < 0.2:  # Başlık ve metin çok farklı
                score += 10
        
        return min(100, max(0, score))
    
    def _score_propaganda(
        self,
        headline: str,
        text: str,
        textual_analysis: Dict[str, Any],
        source_analysis: Dict[str, Any]
    ) -> float:
        """Propaganda skoru"""
        score = 0.0
        
        # One-sided narrative
        if text.count("ama") < 2 and text.count("ancak") < 2:
            score += 20
        
        # Repetitive messaging
        words = text.split()
        if len(set(words)) / len(words) < 0.3:  # Low vocabulary diversity
            score += 15
        
        # Emotional appeals
        emotional = ["korku", "tehlike", "düşman", "saldırı", "tehdit"]
        if sum(1 for word in emotional if word in text) >= 2:
            score += 25
        
        # Political alignment
        political = ["destek", "karşı", "yanlış", "doğru", "haklı", "haksız"]
        if sum(1 for word in political if word in text) >= 3:
            score += 20
        
        return min(100, score)
    
    def _score_satire(
        self,
        headline: str,
        text: str,
        textual_analysis: Dict[str, Any]
    ) -> float:
        """Şaka/Gırgır skoru"""
        score = 0.0
        
        # Humor indicators
        humor_words = ["şaka", "gırgır", "komik", "eğlenceli", "mizah", "espri"]
        if any(word in headline or word in text for word in humor_words):
            score += 40
        
        # Exaggeration
        if "çok" in headline or "süper" in headline or "mega" in headline:
            score += 20
        
        # Absurd claims
        absurd = ["uzaylı", "zombi", "büyü", "sihir"]
        if any(word in text for word in absurd):
            score += 30
        
        # Emoji usage (if text contains emojis)
        if "😀" in text or "😂" in text or "🤣" in text:
            score += 10
        
        return min(100, score)
    
    def _score_parody(
        self,
        headline: str,
        text: str,
        textual_analysis: Dict[str, Any]
    ) -> float:
        """Hiciv skoru"""
        score = 0.0
        
        # Parody indicators
        parody_words = ["parodi", "taklit", "alay", "ironi", "hiciv"]
        if any(word in headline or word in text for word in parody_words):
            score += 50
        
        # Known parody sites
        if "onion" in text or "zaytung" in text.lower():
            score += 30
        
        # Exaggerated style
        if headline.count("!") >= 2:
            score += 20
        
        return min(100, score)
    
    def _score_clickbait(
        self,
        headline: str,
        text: str,
        textual_analysis: Dict[str, Any],
        source_analysis: Dict[str, Any] = None
    ) -> float:
        """Tıklama yemi skoru - İçeriğe göre dinamik hesaplama"""
        score = 0.0
        
        # Güvenilir kaynaklar için bonus (clickbait daha az olası)
        source_cred = 0.5
        if source_analysis:
            source_cred = source_analysis.get("source_info", {}).get("credibility_score", 0.5)
        
        # Clickbait pattern'leri - içeriğe göre dinamik
        clickbait_patterns = [
            (r"bu\s+haber\s+şok\s+edecek", 20),
            (r"görmeniz\s+gereken", 15),
            (r"inanamayacaksınız", 20),
            (r"numara\s+\d+", 15),
            (r"mutlaka\s+okuyun", 15),
            (r"kaçırmayın", 10),
            (r"şok\s+edici", 15),
            (r"gizli\s+gerçek", 20)
        ]
        
        # "son dakika" sadece düşük güvenilir kaynaklarda clickbait
        if source_cred < 0.7:
            clickbait_patterns.append((r"son\s+dakika", 10))
        
        # Pattern matching - her pattern için ayrı kontrol
        matched_patterns = 0
        for pattern, penalty in clickbait_patterns:
            if re.search(pattern, headline, re.IGNORECASE):
                # Güvenilir kaynaklarda daha az puan
                adjusted_penalty = int(penalty * 0.6) if source_cred >= 0.7 else penalty
                score += adjusted_penalty
                matched_patterns += 1
        
        # Çok fazla pattern eşleşirse ekstra puan
        if matched_patterns >= 2:
            score += 10
        
        # Question in headline (içeriğe göre)
        question_count = headline.count("?")
        if question_count > 0:
            # Soru işareti sayısına göre
            penalty = 8 + (question_count - 1) * 5
            score += penalty if source_cred < 0.7 else int(penalty * 0.5)
        
        # Headline-text mismatch (içeriğe göre dinamik)
        if headline and text:
            headline_words = set(headline.lower().split()[:5])
            text_words = set(text.lower().split()[:30])  # Daha fazla kelime kontrolü
            overlap = len(headline_words & text_words) / len(headline_words) if headline_words else 0
            
            if overlap < 0.2:  # Çok düşük overlap
                penalty = 25 if source_cred < 0.7 else 15
                score += penalty
            elif overlap < 0.4:  # Orta düşük overlap
                penalty = 15 if source_cred < 0.7 else 8
                score += penalty
        
        # Headline uzunluğu ve metin uzunluğu oranı
        if headline and text:
            headline_len = len(headline)
            text_len = len(text)
            if text_len > 0:
                ratio = headline_len / text_len
                # Başlık çok uzun, metin çok kısa = clickbait
                if ratio > 0.3 and text_len < 300:
                    score += 15 if source_cred < 0.7 else 8
        
        # Ünlem işareti kullanımı
        exclamation_count = headline.count("!")
        if exclamation_count > 0:
            score += min(15, exclamation_count * 5)
        
        # Büyük harf kullanımı (ALL CAPS)
        if headline.isupper() and len(headline) > 10:
            score += 20 if source_cred < 0.7 else 10
        
        # Textual analysis'ten gelen duygusal manipülasyon skorunu kullan
        if textual_analysis:
            analysis_data = textual_analysis.get("analysis", {})
            if isinstance(analysis_data, dict):
                emotional_manip = analysis_data.get("emotional_manipulation", {})
                if isinstance(emotional_manip, dict):
                    manip_score = emotional_manip.get("score", 0.0)
                    # Yüksek duygusal manipülasyon = clickbait
                    if manip_score > 0.6:
                        score += int(manip_score * 20)
        
        return min(100, max(0, score))
    
    def _score_junk_news(
        self,
        headline: str,
        text: str,
        source_analysis: Dict[str, Any],
        textual_analysis: Dict[str, Any]
    ) -> float:
        """Çerçöp haber skoru"""
        score = 0.0
        
        # Low quality indicators
        source_cred = source_analysis.get("source_info", {}).get("credibility_score", 0.5)
        if source_cred < 0.4:
            score += 30
        
        # Very short content
        if len(text) < 100:
            score += 25
        
        # Poor grammar/spelling (simplified check)
        if text.count(" ") < 10:  # Very few words
            score += 20
        
        # No author information
        if "yazar" not in text and "muhabir" not in text:
            score += 15
        
        # Excessive ads/promotional content
        promotional = ["tıkla", "indir", "kazan", "bedava", "ücretsiz"]
        if sum(1 for word in promotional if word in text) >= 2:
            score += 20
        
        return min(100, score)

