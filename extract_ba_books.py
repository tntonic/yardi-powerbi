#!/usr/bin/env python3
"""
Extract BA- books from the original grep output
"""

# From the original grep output, I can see these BA- books:
ba_books_raw = """
24,BA-6Y-Q3-22-27
25,BA-6Y-Q4.-23-28
28,BA-6Y-Q1.-23-28
29,BA-6Y-Q2-23-28
30,BA-6Y-Q3-23-28
31,BA-6Y-Q4-23-28
34,BA-6Y-Q2.-23-28
37,BA-11Y-Q1-24-34
43,BA-11Y-Q3-24-34
45,BA-11Y-Q1-25-35
"""

print("BA- Forecast Books Identified:")
print("=" * 60)
print("Book ID | Book Name                    | Forecast Period")
print("=" * 60)

ba_books = []
for line in ba_books_raw.strip().split('\n'):
    if line.strip():
        parts = line.split(',')
        book_id = parts[0]
        book_name = parts[1]
        ba_books.append({'book_id': int(book_id), 'book_name': book_name})
        
        # Extract forecast period info
        if "6Y" in book_name:
            period_type = "6-Year"
        elif "11Y" in book_name:
            period_type = "11-Year"
        else:
            period_type = "Unknown"
            
        print(f"{book_id:>7} | {book_name:<28} | {period_type}")

print("\nKey Insights:")
print("- Total BA- books found: 10")
print("- 6-Year forecasts (BA-6Y): 7 books") 
print("- 11-Year forecasts (BA-11Y): 3 books")
print("- Book 1 = Accrual (use for actuals)")
print("- Book 0 = Cash")

print("\nForecasting Periods:")
print("6-Year Books:")
for book in ba_books:
    if "6Y" in book['book_name']:
        print(f"  - Book {book['book_id']}: {book['book_name']}")

print("\n11-Year Books:")
for book in ba_books:
    if "11Y" in book['book_name']:
        print(f"  - Book {book['book_id']}: {book['book_name']}")
        
# Additional key books for reference
print("\nOther Key Books for P&L:")
print("  - Book 1: Accrual (Primary actuals)")  
print("  - Book 46: FPR (Financial Planning & Reporting)")
print("  - Book 6: Budget")
print("  - Book 26: Business Plan Budget-6y")
print("  - Book 36: Business Plan Budget-11y")