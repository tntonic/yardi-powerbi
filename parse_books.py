#!/usr/bin/env python3
"""
Parse dim_book.csv to extract all books and identify BA- forecast books
"""

import csv
import pandas as pd

def parse_dim_book():
    """Parse the dim_book.csv file and extract book information"""
    
    # Read the file
    with open('/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/Data/Yardi_Tables/dim_book.csv', 'r') as f:
        content = f.read().strip()
    
    # Remove the BOM and split by commas
    content = content.replace('﻿', '')
    parts = content.split(',')
    
    # Parse the book data 
    # Format: "book id,book,database id" followed by "0,Cash,1,1,Accrual,1,2,Accrual-Cons,1..."
    books = []
    
    # Find where actual data starts (after the header)
    start_idx = 0
    for i, part in enumerate(parts):
        if part.strip() == "database id":
            start_idx = i + 1
            break
    
    # Process data in groups of 3: book_id, book_name, database_id
    i = start_idx
    while i < len(parts) - 2:
        try:
            book_id = parts[i].strip()
            book_name = parts[i + 1].strip()  
            database_id = parts[i + 2].strip()
            
            # Skip empty or malformed entries
            if not book_id or not book_name:
                i += 3
                continue
                
            books.append({
                'book_id': int(book_id) if book_id.isdigit() else book_id,
                'book_name': book_name,
                'database_id': database_id
            })
            i += 3
        except Exception as e:
            print(f"Error at index {i}: {e}, parts around index: {parts[max(0,i-2):i+5]}")
            i += 1
    
    # Create DataFrame
    df = pd.DataFrame(books)
    
    print("All Books in dim_book:")
    print("=" * 50)
    for _, row in df.iterrows():
        print(f"ID: {row['book_id']:>3} | Name: {row['book_name']}")
    
    print("\nBA- Books (Forecast Books):")
    print("=" * 50)
    ba_books = df[df['book_name'].str.contains('BA-', na=False)]
    for _, row in ba_books.iterrows():
        print(f"ID: {row['book_id']:>3} | Name: {row['book_name']}")
    
    print("\nOther Key Books:")
    print("=" * 50)
    key_books = df[df['book_name'].isin(['Accrual', 'Budget', 'Business Plan Budget-6y', 'Business Plan Budget-11y', 'FPR'])]
    for _, row in key_books.iterrows():
        print(f"ID: {row['book_id']:>3} | Name: {row['book_name']}")
    
    return df, ba_books

if __name__ == "__main__":
    df, ba_books = parse_dim_book()
    
    # Export BA- books for reference
    ba_books.to_csv('/Users/michaeltang/Documents/GitHub/BI/Yardi PowerBI/ba_books_analysis.csv', index=False)
    print(f"\nTotal books found: {len(df)}")
    print(f"BA- forecast books found: {len(ba_books)}")