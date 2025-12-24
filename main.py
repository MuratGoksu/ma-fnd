# main.py — unified CLI with source selection, detailed logging, and test-friendly run()
import os
import json
import time
import argparse

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from agents import (
    CrawlerAgent,
    TextualAgent,
    ClaimAgent,
    ChallengeAgent,
    JudgeAgent,
    LLMJudgeAgent,
    Logger,
)


def fetch_with_source(source: str, input_val: str | None) -> dict:
    """
    Select the fetching strategy:
      - rss     : agents.RSSCrawlerAgent (feed URL)
      - url     : agents.URLCrawlerAgent (page URL)
      - file    : local JSON with keys {headline, text}
      - twitter : agents.TwitterCrawlerAgent (tweet ID, username, or query)
      - mock    : default CrawlerAgent() (no network)
    """
    s = (source or "mock").lower()
    if s == "rss":
        from agents import RSSCrawlerAgent
        if not input_val:
            raise ValueError("--input (feed URL) is required for --source rss")
        return RSSCrawlerAgent().fetch_news(feed_url=input_val)
    if s == "url":
        from agents import URLCrawlerAgent
        if not input_val:
            raise ValueError("--input (page URL) is required for --source url")
        return URLCrawlerAgent().fetch_news(url=input_val)
    if s == "file":
        if not input_val:
            raise ValueError("--input (path) is required for --source file")
        with open(input_val, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "id": data.get("id", "file-1"),
            "link": data.get("link") or data.get("id", "file-1"),
            "headline": data.get("headline", "Untitled"),
            "text": data.get("text", ""),
        }
    if s == "twitter":
        from agents import TwitterCrawlerAgent
        if not input_val:
            raise ValueError("--input (tweet_id, @username, or query) is required for --source twitter")
        
        crawler = TwitterCrawlerAgent()
        
        # Parse input: can be tweet_id, @username, or query
        input_str = input_val.strip()
        
        if input_str.startswith("@"):
            # Username
            username = input_str[1:]  # Remove @
            return crawler.fetch_news(username=username)
        elif input_str.isdigit() or input_str.startswith("http"):
            # Tweet ID or URL
            if "twitter.com" in input_str or "x.com" in input_str:
                # Extract tweet ID from URL
                tweet_id = input_str.split("/status/")[-1].split("?")[0]
            else:
                tweet_id = input_str
            return crawler.fetch_news(tweet_id=tweet_id)
        else:
            # Search query
            return crawler.fetch_news(query=input_val)
    
    # default mock
    return CrawlerAgent().fetch_news()


def select_judge(judge_choice: str | None, model: str | None):
    judge_type = (judge_choice or os.getenv("JUDGE", "rule")).lower()
    if judge_type in {"llm", "llmjudge", "llm-judge"}:
        try:
            return LLMJudgeAgent(model=model or os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
        except Exception as e:
            print(f"[warn] LLM judge unavailable ({e}), falling back to rule-based JudgeAgent.")
            return JudgeAgent()
    return JudgeAgent()


def run(source: str,
    input_val: str | None = None,
    judge_flag: str | None = None,
        model: str | None = None,
        conf_threshold: float | None = None,
        **kwargs):
    """Test-friendly entry point.

    Accepts both `judge_flag` and `judge_choice` (for backward-compat with tests).
    Returns (verdict_value, record_dict).
    """
    # Back-compat: some tests call run(..., judge_choice="rule")
    judge_choice = kwargs.get("judge_choice", None)
    if judge_choice is not None and not judge_flag:
        judge_flag = judge_choice

    # Crawler by source
    try:
        news = fetch_with_source(source, input_val)
    except Exception as e:
        print(f"[warn] fetch failed ({e}); falling back to mock sample.")
        news = CrawlerAgent().fetch_news()
    print(f"[source] {source} input={input_val or ''}")

    # Pipeline
    textual = TextualAgent()
    claim = ClaimAgent()
    challenge = ChallengeAgent()
    logger = Logger()
    judge = select_judge(judge_flag, model)

    clean_news = textual.clean_text(news)
    pro_arg = claim.generate_argument(clean_news)
    con_arg = challenge.generate_argument(clean_news)

    # Determine if judge is LLM
    is_llm = isinstance(judge, LLMJudgeAgent)

    verdict_value = "UNSURE"
    verdict_details = None

    if is_llm:
        verdict_details = judge.evaluate_detailed(pro_arg, con_arg)
        # Confidence threshold (default from env or arg)
        thr = None
        if conf_threshold is not None:
            thr = float(conf_threshold)
        else:
            try:
                thr = float(os.getenv("CONF_THRESHOLD", "0.70"))
            except Exception:
                thr = 0.70
        conf = verdict_details.get("confidence", 0.5)
        verdict_value = verdict_details.get("verdict", "UNSURE")
        if conf < thr:
            verdict_value = "UNSURE"
        logger.log_result(clean_news, pro_arg, con_arg, verdict_details)
    else:
        # Rule-based judge now also receives the item for domain scoring
        verdict_result = judge.evaluate(pro_arg, con_arg, item=clean_news)
        # evaluate() returns dict when called with item parameter
        if isinstance(verdict_result, dict):
            verdict_value = verdict_result.get("verdict", "UNSURE")
            verdict_details = verdict_result
        else:
            verdict_value = verdict_result
        logger.log_result(clean_news, pro_arg, con_arg, verdict_value)

    assert verdict_value in {"REAL", "FAKE", "UNSURE"}, f"Unexpected verdict: {verdict_value}"

    # JSONL log record for tests/analytics
    os.makedirs("logs", exist_ok=True)
    record = {
        "ts": int(time.time()),
        "source": source,
        "input": input_val,
        "headline": clean_news.get("headline"),
        "text_len": len(clean_news.get("text", "")),
        "pro": pro_arg,
        "con": con_arg,
        "verdict": verdict_value,
    }
    if isinstance(verdict_details, dict):
        record.update({
            "model": verdict_details.get("model"),
            "confidence": verdict_details.get("confidence"),
            "rationale": verdict_details.get("rationale"),
        })
    with open("logs/run.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Test passed: verdict is {verdict_value}")
    return verdict_value, record


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=os.getenv("SOURCE", "mock"), help="mock | rss | url | file | twitter")
    parser.add_argument("--input", default=os.getenv("INPUT", ""), help="feed URL, page URL or file path")
    parser.add_argument("--judge", dest="judge_choice", default=os.getenv("JUDGE", "rule"), help="rule | llm")
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    parser.add_argument("--conf-threshold", dest="conf_threshold", default=os.getenv("CONF_THRESHOLD", "0.70"))
    parser.add_argument("--trust", default=os.getenv("TRUST_SITES_PATH", ""), help="Path to JSON trust list (overrides config/trust_sites.json)")
    args = parser.parse_args()

    verdict, rec = run(
        source=args.source,
        input_val=args.input,
        judge_flag=args.judge_choice,
        model=args.model,
        conf_threshold=float(args.conf_threshold) if args.conf_threshold is not None else None,
    )
