from reportlab.pdfgen import canvas

def create_dummy_pdf(filename):
    c = canvas.Canvas(filename)
    c.drawString(100, 750, "GeminiClaw Company Policy")
    c.drawString(100, 730, "1. Remote Work Guidelines")
    c.drawString(100, 710, "All employees are allowed to work remotely 3 days a week.")
    c.drawString(100, 690, "2. Communication")
    c.drawString(100, 670, "Use Slack for daily communication and Jira for task tracking.")
    c.showPage()
    c.save()

if __name__ == "__main__":
    create_dummy_pdf("dummy_policy.pdf")
    print("Created dummy_policy.pdf")
