from agents import CrawlerAgent, TextualAgent, ClaimAgent, ChallengeAgent, JudgeAgent

def test_deterministic_verdict():
    crawler = CrawlerAgent()
    textual = TextualAgent()
    claim = ClaimAgent()
    challenge = ChallengeAgent()
    judge = JudgeAgent()

    news = crawler.fetch_news()
    clean = textual.clean_text(news)
    pro = claim.generate_argument(clean)
    con = challenge.generate_argument(clean)
    verdict = judge.evaluate(pro, con)

    assert verdict in {"REAL", "FAKE", "UNSURE"}

def test_repeatability_mock_mode():
    crawler = CrawlerAgent()
    textual = TextualAgent()
    claim = ClaimAgent()
    challenge = ChallengeAgent()
    judge = JudgeAgent()

    news = crawler.fetch_news()
    clean = textual.clean_text(news)

    v1 = judge.evaluate(claim.generate_argument(clean), challenge.generate_argument(clean))
    v2 = judge.evaluate(claim.generate_argument(clean), challenge.generate_argument(clean))

    assert v1 == v2
