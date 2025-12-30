from predict_plagiarism import PlagiarismPredictor

def verify_writing_style():
    # Initialize your industrial-grade predictor
    scanner = PlagiarismPredictor()

    # Define 3 specific test cases based on supervisor's research
    test_cases = [
        {
            "id": "CASE 1: AUTHENTIC (SPOKEN)",
            "text": "ඔහු ගෙදර ගියා. අම්මා කෑම හැදුවා. අපි හැමෝම සතුටින් හිටියා.",
            "description": "Simple/Spoken Sinhala using common verb forms like 'ගියා' and 'හැදුවා'."
        },
        {
            "id": "CASE 2: SUSPICIOUS (LITERARY)",
            "text": "ඔහු නිවස බලා ගියේය. මාතාව විසින් ආහාර පිසින ලදී. අපි සියල්ලෝම ඉමහත් ප්‍රීතියෙන් පසු වූවෙමු.",
            "description": "Formal/Literary Sinhala with strict subject-verb agreement like 'ගියේය'."
        },
        {
            "id": "CASE 3: SUSPICIOUS (ACADEMIC)",
            "text": "ශ්‍රී ලංකාවේ වර්තමාන ආර්ථික අර්බුදය හමුවේ රජය විසින් නව බදු ප්‍රතිසංස්කරණ හඳුන්වා දී ඇත.",
            "description": "High academic density and professional news style."
        }
    ]

    print("\n" + "="*70)
    print("STARTING WRITING STYLE VERIFICATION (IT22330628)")
    print("="*70)

    for case in test_cases:
        print(f"\n{case['id']}")
        print(f"DESCRIPTION : {case['description']}")
        
        # Run the intrinsic scan
        report = scanner.run_intrinsic_scan(case['text'])
        
        print(f"DECISION    : {report['decision']}")
        print(f"RATIONALE   : {report['rationale']}")
        print("-" * 40)

    print("\nVERIFICATION COMPLETE\n")

if __name__ == "__main__":
    verify_writing_style()