class Logger:
    def log_result(self, news, pro, con, verdict_or_details):
        print("📰 Headline:", news.get("headline"))
        print("📝 Text:", (news.get("text") or "")[:180].strip(), "\n")
        print("✅ PRO:", pro)
        print("❌ CON:", con)
        if isinstance(verdict_or_details, dict):
            print("🧠 VERDICT:", verdict_or_details.get("verdict"))
            if "confidence" in verdict_or_details:
                print("🔎 Confidence:", verdict_or_details.get("confidence"))
        else:
            print("🧠 VERDICT:", verdict_or_details)