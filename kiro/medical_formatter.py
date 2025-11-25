def format_medical_info(query: str, summary: str):
    """
    Converts raw Wikipedia text into structured medical info.
    """

    lower = summary.lower()

    symptoms = []
    causes = []
    treatment = []
    prevention = []

    # simple keyword extraction
    if "symptom" in lower:
        symptoms.append("Symptoms may include those described in the disease summary.")

    if "cause" in lower:
        causes.append("Causes are mentioned in the summary text.")

    if "treat" in lower:
        treatment.append("Treatment options are noted in the summary text.")

    if "prevent" in lower:
        prevention.append("Preventive measures are referred in the summary.")

    final_answer = f"""
📌 **Information about {query.title()}**

📖 **Definition**
{summary}

🩺 **Symptoms**
- {symptoms[0] if symptoms else "Not clearly listed, but you may experience common disease symptoms like fever, fatigue, or other condition-specific indicators."}

⚠️ **Causes**
- {causes[0] if causes else "Causes are not specifically listed. Check detailed medical sources."}

💊 **Treatment**
- {treatment[0] if treatment else "Treatment methods are not specifically listed. Seek professional medical guidance."}

🛡️ **Precautions / Prevention**
- {prevention[0] if prevention else "General health precautions may apply: hygiene, healthy diet, regular medical checkups."}

⚠️ *Disclaimer: Always consult a medical professional for accurate diagnosis and treatment.*
    """

    return final_answer
